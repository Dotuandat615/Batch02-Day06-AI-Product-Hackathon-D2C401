"""
location/service.py

Cách dùng nhanh:
    from modules.location import LocationService

    svc = LocationService(google_api_key="...", anthropic_api_key="...")

    # 1. Lấy vị trí người dùng (qua IP nếu không có lat/lng)
    loc = svc.get_location()                        # tự detect qua IP
    loc = svc.get_location(lat=12.2451, lng=109.19) # hoặc truyền thẳng

    # 2. Lấy danh sách quán xung quanh
    restaurants = svc.get_nearby_restaurants(loc)

    # 3. Lấy chi tiết 1 quán (reviews, giờ, số điện thoại, menu AI)
    detail = svc.get_restaurant_detail(restaurants[0].place_id, loc)
"""

import os
import json
import httpx
import anthropic
from dataclasses import dataclass, field
from typing import Optional

from .geo_utils import haversine_m, fmt_distance, maps_url

# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class Location:
    lat: float
    lng: float
    city: str                   # "Nha Trang"
    province: str               # "Khánh Hòa"
    display_name: str           # "Nha Trang, Khánh Hòa"
    source: str                 # "ip" | "gps" | "manual"


@dataclass
class Review:
    author: str
    rating: int                 # 1–5
    text: str
    time_description: str       # "1 tháng trước"
    timestamp: int              # Unix epoch


@dataclass
class MenuItem:
    dish: str
    description: str
    estimated_price: str        # "35.000–55.000đ"


@dataclass
class Restaurant:
    place_id: str
    name: str
    address: str
    lat: float
    lng: float
    distance_m: float           # khoảng cách tính bằng mét
    distance_text: str          # "350m" | "1.2km"
    maps_url: str               # Google Maps deep link
    rating: Optional[float]
    review_count: Optional[int]
    price_level: Optional[int]  # 1 = $, 2 = $$, 3 = $$$, 4 = $$$$
    is_open_now: Optional[bool]
    types: list[str]            # ["restaurant", "food", ...]
    photo_url: Optional[str]    # URL ảnh đại diện (cần API key để hiển thị)


@dataclass
class RestaurantDetail(Restaurant):
    phone: Optional[str] = None
    website: Optional[str] = None
    opening_hours: list[str] = field(default_factory=list)  # ["Thứ 2: 7:00–22:00", ...]
    reviews: list[Review] = field(default_factory=list)
    menu_items: list[MenuItem] = field(default_factory=list)  # do AI suy luận


# ── Service ───────────────────────────────────────────────────────────────────

class LocationService:
    PLACES_BASE = "https://maps.googleapis.com/maps/api/place"
    PHOTO_BASE  = "https://maps.googleapis.com/maps/api/place/photo"
    DEFAULT_RADIUS_KM = 1.5     # bán kính mặc định: 1.5km (phù hợp đi bộ)
    MAX_RESULTS = 20            # lấy tối đa 20 quán trước khi lọc

    def __init__(self, google_api_key: str = None, anthropic_api_key: str = None):
        self._gkey  = google_api_key  or os.getenv("GOOGLE_MAPS_API_KEY", "")
        self._akey  = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY", "")
        if not self._gkey:
            raise ValueError("Cần GOOGLE_MAPS_API_KEY — đặt trong .env hoặc truyền vào constructor.")

    # ── 1. Lấy vị trí ─────────────────────────────────────────────────────────

    def get_location(self, lat: float = None, lng: float = None) -> Location:
        """
        Trả về Location.
        - Nếu có lat/lng: dùng trực tiếp, reverse-geocode để lấy tên thành phố.
        - Nếu không: tự detect qua địa chỉ IP (dùng ip-api.com, miễn phí).
        """
        if lat is not None and lng is not None:
            return self._reverse_geocode(lat, lng, source="gps")
        return self._ip_geolocation()

    def _ip_geolocation(self) -> Location:
        """ip-api.com — miễn phí, không cần key, giới hạn 45 req/phút."""
        resp = httpx.get("http://ip-api.com/json/?lang=vi&fields=lat,lon,city,regionName,status,message",
                         timeout=6.0)
        data = resp.json()
        if data.get("status") != "success":
            raise RuntimeError(f"ip-api.com lỗi: {data.get('message', 'unknown')}")
        city = data.get("city", "")
        province = data.get("regionName", "")
        return Location(
            lat=data["lat"], lng=data["lon"],
            city=city, province=province,
            display_name=f"{city}, {province}" if city != province else city,
            source="ip",
        )

    def _reverse_geocode(self, lat: float, lng: float, source: str) -> Location:
        """Google Geocoding API: tọa độ → tên thành phố."""
        resp = httpx.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"latlng": f"{lat},{lng}", "language": "vi",
                    "result_type": "locality|administrative_area_level_1",
                    "key": self._gkey},
            timeout=8.0,
        )
        data = resp.json()
        if data.get("status") != "OK":
            raise RuntimeError(f"Google Geocoding lỗi: {data.get('status')}")
        city = province = ""
        for comp in data["results"][0].get("address_components", []):
            t = comp.get("types", [])
            if "locality" in t:
                city = comp["long_name"]
            if "administrative_area_level_1" in t:
                province = comp["long_name"]
        city = city or province or "Không xác định"
        return Location(
            lat=lat, lng=lng,
            city=city, province=province,
            display_name=f"{city}, {province}" if city != province and province else city,
            source=source,
        )

    # ── 2. Danh sách quán xung quanh ──────────────────────────────────────────

    def get_nearby_restaurants(
        self,
        location: Location,
        radius_km: float = DEFAULT_RADIUS_KM,
        keyword: str = "",
    ) -> list[Restaurant]:
        """
        Trả về danh sách quán ăn gần location, sắp xếp theo khoảng cách.

        Params:
            location   : Location object (từ get_location())
            radius_km  : bán kính tìm kiếm (mặc định 1.5km)
            keyword    : từ khoá lọc thêm, ví dụ "chay", "đặc sản", "bún bò"

        Trả về list[Restaurant] — tất cả trường có trong Google Places API.
        """
        params = {
            "location": f"{location.lat},{location.lng}",
            "radius": int(radius_km * 1000),
            "type": "restaurant",
            "language": "vi",
            "key": self._gkey,
        }
        if keyword:
            params["keyword"] = keyword

        results = self._paginate_nearby(params)
        restaurants = [self._parse_restaurant(p, location) for p in results]
        restaurants.sort(key=lambda r: r.distance_m)
        return restaurants

    def _paginate_nearby(self, params: dict) -> list:
        """Gọi Nearby Search, lấy tối đa MAX_RESULTS quán (có thể qua nhiều trang)."""
        all_results = []
        url = f"{self.PLACES_BASE}/nearbysearch/json"

        while True:
            resp = httpx.get(url, params=params, timeout=10.0)
            data = resp.json()
            status = data.get("status")
            if status == "ZERO_RESULTS":
                break
            if status not in ("OK", "ZERO_RESULTS"):
                raise RuntimeError(f"Google Places Nearby Search lỗi: {status} — {data.get('error_message', '')}")
            all_results.extend(data.get("results", []))
            if len(all_results) >= self.MAX_RESULTS or "next_page_token" not in data:
                break
            # Google yêu cầu delay ~2s trước khi dùng next_page_token
            import time; time.sleep(2)
            params = {"pagetoken": data["next_page_token"], "key": self._gkey}

        return all_results[:self.MAX_RESULTS]

    def _parse_restaurant(self, p: dict, location: Location) -> Restaurant:
        loc = p.get("geometry", {}).get("location", {})
        r_lat, r_lng = loc.get("lat", 0.0), loc.get("lng", 0.0)
        dist = haversine_m(location.lat, location.lng, r_lat, r_lng)

        photos = p.get("photos", [])
        photo_url = None
        if photos:
            ref = photos[0].get("photo_reference", "")
            photo_url = (
                f"{self.PHOTO_BASE}?maxwidth=400&photo_reference={ref}&key={self._gkey}"
            )

        return Restaurant(
            place_id=p["place_id"],
            name=p.get("name", ""),
            address=p.get("vicinity", ""),
            lat=r_lat,
            lng=r_lng,
            distance_m=dist,
            distance_text=fmt_distance(dist),
            maps_url=maps_url(r_lat, r_lng, p.get("name", ""), location.lat, location.lng),
            rating=p.get("rating"),
            review_count=p.get("user_ratings_total"),
            price_level=p.get("price_level"),
            is_open_now=p.get("opening_hours", {}).get("open_now"),
            types=p.get("types", []),
            photo_url=photo_url,
        )

    # ── 3. Chi tiết quán: reviews, giờ, SĐT, menu AI ─────────────────────────

    def get_restaurant_detail(
        self,
        place_id: str,
        location: Location = None,
        include_ai_menu: bool = True,
    ) -> RestaurantDetail:
        """
        Lấy toàn bộ thông tin chi tiết của một quán.

        Params:
            place_id        : Google Place ID (lấy từ Restaurant.place_id)
            location        : dùng để tính khoảng cách và tạo Maps URL chỉ đường
            include_ai_menu : True = dùng Claude để suy luận menu từ tên quán + reviews

        Trả về RestaurantDetail với tất cả trường từ Places API + menu AI.
        """
        fields = ",".join([
            "place_id", "name", "formatted_address",
            "formatted_phone_number", "website",
            "opening_hours", "rating", "user_ratings_total",
            "price_level", "reviews", "geometry",
            "types", "photos", "business_status",
            "editorial_summary",
        ])
        resp = httpx.get(
            f"{self.PLACES_BASE}/details/json",
            params={"place_id": place_id, "fields": fields, "language": "vi", "key": self._gkey},
            timeout=10.0,
        )
        data = resp.json()
        if data.get("status") != "OK":
            raise RuntimeError(f"Google Place Details lỗi: {data.get('status')}")

        r = data["result"]
        loc = r.get("geometry", {}).get("location", {})
        r_lat, r_lng = loc.get("lat", 0.0), loc.get("lng", 0.0)

        # Khoảng cách và Maps URL
        if location and location.lat:
            dist = haversine_m(location.lat, location.lng, r_lat, r_lng)
            dist_text = fmt_distance(dist)
            murl = maps_url(r_lat, r_lng, r.get("name", ""), location.lat, location.lng)
        else:
            dist, dist_text = 0.0, ""
            murl = maps_url(r_lat, r_lng, r.get("name", ""))

        # Ảnh đại diện
        photos = r.get("photos", [])
        photo_url = None
        if photos:
            ref = photos[0].get("photo_reference", "")
            photo_url = f"{self.PHOTO_BASE}?maxwidth=800&photo_reference={ref}&key={self._gkey}"

        # Reviews
        reviews = [
            Review(
                author=rv.get("author_name", "Ẩn danh"),
                rating=rv.get("rating", 0),
                text=rv.get("text", ""),
                time_description=rv.get("relative_time_description", ""),
                timestamp=rv.get("time", 0),
            )
            for rv in r.get("reviews", [])
        ]

        # Giờ mở cửa
        opening_hours = r.get("opening_hours", {}).get("weekday_text", [])

        detail = RestaurantDetail(
            place_id=place_id,
            name=r.get("name", ""),
            address=r.get("formatted_address", ""),
            lat=r_lat,
            lng=r_lng,
            distance_m=dist,
            distance_text=dist_text,
            maps_url=murl,
            rating=r.get("rating"),
            review_count=r.get("user_ratings_total"),
            price_level=r.get("price_level"),
            is_open_now=r.get("opening_hours", {}).get("open_now"),
            types=r.get("types", []),
            photo_url=photo_url,
            phone=r.get("formatted_phone_number"),
            website=r.get("website"),
            opening_hours=opening_hours,
            reviews=reviews,
        )

        if include_ai_menu and self._akey:
            detail.menu_items = self._infer_menu(detail)

        return detail

    # ── 4. AI menu inference ──────────────────────────────────────────────────

    def _infer_menu(self, detail: RestaurantDetail) -> list[MenuItem]:
        """
        Dùng Claude để suy luận danh sách món tiêu biểu dựa trên
        tên quán, địa chỉ, loại hình, và nội dung review thực tế.
        Trả về list[MenuItem], [] nếu Claude không trả về JSON hợp lệ.
        """
        review_text = "\n".join(
            f'- {rv.author} ({rv.rating}⭐): {rv.text[:300]}'
            for rv in detail.reviews[:5]
        ) or "Chưa có review."

        prompt = f"""Dưới đây là thông tin về một quán ăn tại Việt Nam:
Tên: {detail.name}
Địa chỉ: {detail.address}
Loại hình: {', '.join(detail.types)}
Review thực tế:
{review_text}

Dựa vào tên quán, địa chỉ và nội dung review, suy luận 4–6 món tiêu biểu quán này có thể phục vụ.
Chỉ trả về JSON hợp lệ, không thêm bất kỳ text nào khác:
[
  {{
    "dish": "Tên món",
    "description": "Mô tả ngắn 1 câu",
    "estimated_price": "35.000–55.000đ"
  }}
]"""

        client = anthropic.Anthropic(api_key=self._akey)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",  # dùng Haiku vì task đơn giản, nhanh và rẻ hơn
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        # Bỏ markdown code fence nếu có
        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()
        try:
            items = json.loads(raw)
            return [MenuItem(**item) for item in items]
        except (json.JSONDecodeError, TypeError):
            return []
