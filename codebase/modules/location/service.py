"""
location/service.py  —  SerpAPI google_maps + ip-api.com

Cách dùng:
    from modules.location import LocationService

    svc = LocationService()
    loc     = svc.get_location()                            # auto-detect qua IP
    loc     = svc.get_location(lat=21.0285, lng=105.8542)  # hoặc GPS

    results = svc.get_nearby_restaurants(loc, radius_km=1.5, query="quán ăn")
    reviews = svc.get_reviews(results[0])
    menu    = svc.get_ai_menu(results[0])

.env cần:
    MAP_API           = <serpapi_key>
    MAP_ENDPOINT      = https://serpapi.com/search
    ANTHROPIC_API_KEY = <key>   (chỉ cần cho get_ai_menu)
"""

import os, json
import httpx
from dataclasses import dataclass, field
from typing import Optional

from .geo_utils import haversine_m, fmt_distance, maps_url

_ZOOM = [(0.5, 16), (1.0, 15), (1.5, 14), (3.0, 13), (6.0, 12), (12.0, 11)]

def _to_zoom(km: float) -> int:
    for threshold, z in _ZOOM:
        if km <= threshold:
            return z
    return 11


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class Location:
    lat: float
    lng: float
    city: str
    province: str
    display_name: str   # "Nha Trang, Khánh Hòa"
    source: str         # "ip" | "gps"


@dataclass
class Review:
    author: str
    rating: Optional[int]
    text: str
    date: str           # "2 tuần trước"


@dataclass
class MenuItem:
    dish: str
    description: str
    estimated_price: str


@dataclass
class Restaurant:
    # ── Định danh ──────────────────────────────────────────────────────────────
    position: int
    place_id: str               # ChIJ... (Google Maps Place ID)
    data_id: str                # 0x... (dùng để lấy reviews qua google_maps_reviews)
    data_cid: str
    reviews_link: str           # SerpAPI link lấy reviews
    place_id_search: str        # SerpAPI link chi tiết quán
    provider_id: str

    # ── Thông tin cơ bản ───────────────────────────────────────────────────────
    title: str
    address: str
    lat: float
    lng: float
    phone: Optional[str]
    website: Optional[str]

    # ── Loại hình ──────────────────────────────────────────────────────────────
    type: str                   # loại hình chính, vd "Nhà hàng"
    types: list[str]            # tất cả loại hình
    type_id: str
    type_ids: list[str]

    # ── Đánh giá ───────────────────────────────────────────────────────────────
    rating: Optional[float]
    review_count: Optional[int]
    user_review: Optional[str]  # 1 snippet review nổi bật

    # ── Giá ────────────────────────────────────────────────────────────────────
    price: Optional[str]        # "1-100.000 ₫"
    price_level: Optional[int]  # 1–4

    # ── Giờ hoạt động ──────────────────────────────────────────────────────────
    open_state: Optional[str]           # "Đang mở cửa · Đóng cửa vào 23:00"
    operating_hours: dict               # {"thứ hai": "08:00–22:00", ...}

    # ── Tiện ích & không gian (từ extensions) ──────────────────────────────────
    highlights: list[str]               # ["Cà phê ngon", "Wi-Fi miễn phí"]
    service_options_list: list[str]     # ["Ăn tại chỗ", "Giao hàng", ...]
    offerings: list[str]                # ["Cà phê", "Rượu"]
    atmosphere: list[str]               # ["Ấm cúng", "Yên tĩnh"]
    popular_for: list[str]
    amenities: list[str]
    payments: list[str]
    children: list[str]
    parking: list[str]
    service_options_dict: dict          # {"Ăn_tại_chỗ": True, ...}

    # ── Ảnh ────────────────────────────────────────────────────────────────────
    thumbnail: Optional[str]            # ảnh thumbnail từ SerpAPI
    serpapi_thumbnail: Optional[str]

    # ── Khoảng cách & chỉ đường (tính thêm) ────────────────────────────────────
    distance_m: float
    distance_text: str
    maps_url: str

    # ── Điền sau khi gọi get_reviews() / get_ai_menu() ─────────────────────────
    reviews: list[Review]    = field(default_factory=list)
    menu_items: list[MenuItem] = field(default_factory=list)


# ── Service ───────────────────────────────────────────────────────────────────

class LocationService:
    DEFAULT_RADIUS_KM = 1.5
    MAX_RESULTS = 20

    def __init__(self, map_api_key: str = None, map_endpoint: str = None,
                 anthropic_api_key: str = None):
        self._key      = map_api_key      or os.getenv("MAP_API", "")
        self._endpoint = (map_endpoint    or os.getenv("MAP_ENDPOINT",
                          "https://serpapi.com/search")).split("?")[0]
        self._akey     = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY", "")

        if not self._key:
            raise ValueError("Cần MAP_API — đặt trong .env hoặc truyền vào constructor.")

    # ── 1. Vị trí ─────────────────────────────────────────────────────────────

    def get_location(self, lat: float = None, lng: float = None) -> Location:
        """
        Trả về Location với lat/lng và tên thành phố.

        - Có lat/lng (GPS thật từ browser/app):
            → Reverse geocode qua Nominatim để lấy tên thành phố chính xác.
        - Không có lat/lng:
            → Tự detect qua IP (ip-api.com). Nhanh nhưng sai ~1–50km.
        """
        if lat is not None and lng is not None:
            return self._reverse_geocode(lat, lng)
        return self._detect_by_ip()

    # Tiền tố hành chính VN cần bỏ để lấy đúng tên thành phố / tỉnh
    _VN_PREFIXES = [
        "Phường ", "Xã ", "Thị trấn ", "Thị xã ",
        "Thành phố ", "Quận ", "Huyện ", "Tỉnh ",
    ]

    def _strip_vn_prefix(self, s: str) -> str:
        for prefix in self._VN_PREFIXES:
            if s.startswith(prefix):
                return s[len(prefix):]
        return s

    def _reverse_geocode(self, lat: float, lng: float) -> Location:
        """
        Chuyển GPS coordinates → tên thành phố bằng Nominatim (OSM).
        Miễn phí, không cần API key. Giới hạn 1 req/giây.
        """
        resp = httpx.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lng, "format": "json",
                    "accept-language": "vi"},
            headers={"User-Agent": "AI-Local-Guide-Hackathon/1.0"},
            timeout=8.0,
        )
        resp.raise_for_status()
        addr = resp.json().get("address", {})

        raw_city = (addr.get("city") or addr.get("town") or addr.get("village")
                    or addr.get("county") or addr.get("state_district")
                    or addr.get("state") or "Không xác định")
        raw_province = addr.get("state") or addr.get("province") or raw_city

        city     = self._strip_vn_prefix(raw_city)
        province = self._strip_vn_prefix(raw_province)
        display  = f"{city}, {province}" if city != province and province else city

        return Location(lat=lat, lng=lng, city=city, province=province,
                        display_name=display, source="gps")

    def _detect_by_ip(self) -> Location:
        """Phát hiện vị trí từ IP public — nhanh nhưng chỉ chính xác ở cấp thành phố."""
        resp = httpx.get(
            "http://ip-api.com/json/",
            params={"lang": "vi", "fields": "status,message,lat,lon,city,regionName"},
            timeout=6.0,
        )
        data = resp.json()
        if data.get("status") != "success":
            raise RuntimeError(f"ip-api.com: {data.get('message')}")
        city, province = data.get("city", ""), data.get("regionName", "")
        display = f"{city}, {province}" if city != province and province else city
        return Location(lat=data["lat"], lng=data["lon"], city=city,
                        province=province, display_name=display, source="ip")

    # ── 2. Danh sách quán xung quanh ──────────────────────────────────────────

    def get_nearby_restaurants(
        self,
        location: Location,
        radius_km: float = DEFAULT_RADIUS_KM,
        query: str = "quán ăn",
    ) -> list[Restaurant]:
        """
        Tìm quán xung quanh location trong radius_km.
        Trả về list[Restaurant] sắp xếp gần → xa.
        Tất cả trường mà google_maps API trả về đều được giữ nguyên.
        """
        resp = httpx.get(
            self._endpoint,
            params={
                "engine":  "google_maps",
                "q":       query,
                "ll":      f"@{location.lat},{location.lng},{_to_zoom(radius_km)}z",
                "type":    "search",
                "hl":      "vi",
                "api_key": self._key,
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        raw = resp.json().get("local_results", [])
        results = [self._parse(r, location) for r in raw[:self.MAX_RESULTS]]
        results.sort(key=lambda r: r.distance_m)
        return results

    def _parse(self, r: dict, loc: Location) -> Restaurant:
        coords = r.get("gps_coordinates", {})
        r_lat  = coords.get("latitude",  0.0)
        r_lng  = coords.get("longitude", 0.0)
        dist   = haversine_m(loc.lat, loc.lng, r_lat, r_lng)

        # Trích xuất extensions (list of single-key dicts)
        ext = {}
        for d in r.get("extensions", []):
            ext.update(d)

        return Restaurant(
            # Định danh
            position         = r.get("position", 0),
            place_id         = r.get("place_id", ""),
            data_id          = r.get("data_id", ""),
            data_cid         = r.get("data_cid", ""),
            reviews_link     = r.get("reviews_link", ""),
            place_id_search  = r.get("place_id_search", ""),
            provider_id      = r.get("provider_id", ""),
            # Cơ bản
            title            = r.get("title", ""),
            address          = r.get("address", ""),
            lat              = r_lat,
            lng              = r_lng,
            phone            = r.get("phone"),
            website          = r.get("website"),
            # Loại hình
            type             = r.get("type", ""),
            types            = r.get("types", []),
            type_id          = r.get("type_id", ""),
            type_ids         = r.get("type_ids", []),
            # Đánh giá
            rating           = r.get("rating"),
            review_count     = r.get("reviews"),
            user_review      = r.get("user_review"),
            # Giá
            price            = r.get("price"),
            price_level      = r.get("extracted_price"),
            # Giờ
            open_state       = r.get("open_state"),
            operating_hours  = r.get("operating_hours", {}),
            # Extensions
            highlights           = ext.get("highlights", []),
            service_options_list = ext.get("service_options", []),
            offerings            = ext.get("offerings", []),
            atmosphere           = ext.get("atmosphere", []),
            popular_for          = ext.get("popular_for", []),
            amenities            = ext.get("amenities", []),
            payments             = ext.get("payments", []),
            children             = ext.get("children", []),
            parking              = ext.get("parking", []),
            service_options_dict = r.get("service_options", {}),
            # Ảnh
            thumbnail            = r.get("thumbnail"),
            serpapi_thumbnail    = r.get("serpapi_thumbnail"),
            # Tính thêm
            distance_m           = dist,
            distance_text        = fmt_distance(dist),
            maps_url             = maps_url(r_lat, r_lng, r.get("title", ""),
                                            loc.lat, loc.lng),
        )

    # ── 3. Reviews ────────────────────────────────────────────────────────────

    def get_reviews(self, restaurant: Restaurant, max_reviews: int = 10) -> list[Review]:
        """
        Lấy reviews thật từ google_maps_reviews engine.
        Cần restaurant.data_id (có trong kết quả get_nearby_restaurants).
        Trả về list[Review], gán vào restaurant.reviews nếu muốn lưu lại.
        """
        if not restaurant.data_id:
            return []
        resp = httpx.get(
            self._endpoint,
            params={
                "engine":  "google_maps_reviews",
                "data_id": restaurant.data_id,
                "hl":      "vi",
                "api_key": self._key,
            },
            timeout=15.0,
        )
        if not resp.is_success:
            return []
        reviews = [
            Review(
                author = rv.get("user", {}).get("name", "Ẩn danh"),
                rating = rv.get("rating"),
                text   = rv.get("snippet", ""),
                date   = rv.get("date", ""),
            )
            for rv in resp.json().get("reviews", [])[:max_reviews]
        ]
        restaurant.reviews = reviews
        return reviews

    # ── 4. AI menu ────────────────────────────────────────────────────────────

    def get_ai_menu(self, restaurant: Restaurant) -> list[MenuItem]:
        """
        Dùng Claude Haiku suy luận 4–6 món tiêu biểu.
        Dùng tên quán + type + offerings + user_review làm context.
        Gán vào restaurant.menu_items nếu muốn lưu lại.
        Trả về [] nếu chưa có ANTHROPIC_API_KEY hoặc parse thất bại.
        """
        if not self._akey:
            return []
        try:
            import anthropic
        except ImportError:
            return []

        prompt = f"""Thông tin về một cơ sở ăn uống tại Việt Nam:
Tên: {restaurant.title}
Loại hình: {restaurant.type}
Địa chỉ: {restaurant.address}
Đồ uống/món có: {', '.join(restaurant.offerings) or 'Không rõ'}
Review nổi bật: {restaurant.user_review or 'Không có'}

Suy luận 4–6 món tiêu biểu. Chỉ trả về JSON, không thêm text nào khác:
[{{"dish":"Tên món","description":"Mô tả 1 câu","estimated_price":"XX.000–YY.000đ"}}]"""

        client = anthropic.Anthropic(api_key=self._akey)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()
        try:
            items = [MenuItem(**i) for i in json.loads(raw)]
            restaurant.menu_items = items
            return items
        except (json.JSONDecodeError, TypeError, KeyError):
            return []
