"""
test_service_integration.py  —  Tests cho LocationService (SerpAPI google_local).

Mock tests   : chạy ngay, không cần key.
Integration  : SKIP nếu MAP_API chưa có trong .env.

Chạy: python -m pytest tests/test_service_integration.py -v -s
"""

import sys, os, pytest
from unittest.mock import MagicMock, patch
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

MAP_KEY   = os.getenv("MAP_API", "")
HAS_KEY   = bool(MAP_KEY) and MAP_KEY != "your_serpapi_key_here"

from modules.location import LocationService, Location, Restaurant, MenuItem


# ── Helpers ───────────────────────────────────────────────────────────────────

NHA_TRANG = Location(lat=12.2451, lng=109.1943, city="Nha Trang",
                     province="Khánh Hòa", display_name="Nha Trang, Khánh Hòa", source="gps")

def _svc():
    return LocationService(map_api_key="FAKE_KEY")


# ── Mock data — đúng với google_local response thật ──────────────────────────

MOCK_RESPONSE = {
    "local_results": [
        {
            "position": 1,
            "place_id": "4201058877741143770",
            "place_id_search": "https://serpapi.com/search.json?engine=google_local&ludocid=4201058877741143770",
            "provider_id": "/g/12vrd7h2s",
            "title": "Bún cá Nha Trang Bà Bảy",
            "type": "Nhà hàng",
            "address": "12 Bến Chợ, Nha Trang, Khánh Hòa",
            "gps_coordinates": {"latitude": 12.2482, "longitude": 109.1943},
            "rating": 4.6,
            "reviews": 234,
            "reviews_original": "(234)",
            "description": '"Nước dùng đậm vị cá tươi, đúng kiểu Nha Trang."',
            "thumbnail": "https://serpapi.com/images/mock_ba_bay_small.jpeg",
            "thumbnail_large": "https://lh3.googleusercontent.com/mock_ba_bay_large",
        },
        {
            "position": 2,
            "place_id": "5162517836559873849",
            "place_id_search": "https://serpapi.com/search.json?engine=google_local&ludocid=5162517836559873849",
            "provider_id": "/g/11qxxy0b71",
            "title": "Bánh căn Mỹ Hòa",
            "type": "Quán ăn vặt",
            "address": "Đường Trần Phú, Nha Trang",
            "gps_coordinates": {"latitude": 12.2471, "longitude": 109.1952},
            "rating": 4.4,
            "reviews": 98,
            "reviews_original": "(98)",
            "description": '"Bánh giòn, trứng chín đều, ăn kèm mắm nêm rất ngon."',
            "thumbnail": "https://serpapi.com/images/mock_my_hoa_small.jpeg",
            "thumbnail_large": "https://lh3.googleusercontent.com/mock_my_hoa_large",
        },
        {
            "position": 3,
            "place_id": "9999000111222333444",
            "place_id_search": "https://serpapi.com/search.json?engine=google_local&ludocid=9999000111222333444",
            "provider_id": "/g/11sd_mock",
            "title": "Nem nướng Ninh Hòa Hai Bà",
            "type": "Nhà hàng",
            "address": "Lô 6 Chợ Đầm, Nha Trang",
            "gps_coordinates": {"latitude": 12.2404, "longitude": 109.1921},
            "rating": 4.7,
            "reviews": 512,
            "reviews_original": "(512)",
            "description": '"Nem cuốn bánh tráng tại chỗ, tươi ngon."',
            "thumbnail": "https://serpapi.com/images/mock_nem_small.jpeg",
            "thumbnail_large": "https://lh3.googleusercontent.com/mock_nem_large",
        },
    ]
}


# ── Mock tests ────────────────────────────────────────────────────────────────

class TestMock:

    def _call(self, response=MOCK_RESPONSE):
        mock_resp = MagicMock()
        mock_resp.is_success = True
        mock_resp.json.return_value = response
        with patch("httpx.get", return_value=mock_resp):
            return _svc().get_nearby_restaurants(NHA_TRANG)

    def test_count(self):
        """
        Đầu vào : 3 quán trong mock response
        Mong đợi: 3 Restaurant
        """
        results = self._call()
        print(f"\n  → {len(results)} quán")
        assert len(results) == 3

    def test_sorted_by_distance(self):
        """
        Đầu vào : 3 quán ở tọa độ khác nhau
        Mong đợi: sắp xếp gần → xa
        Kết quả thực tế:
          Bánh căn Mỹ Hòa  ~243m  (gần nhất)
          Bún cá Bà Bảy    ~345m
          Nem nướng        ~575m  (xa nhất)
        """
        results = self._call()
        distances = [r.distance_m for r in results]
        print(f"\n  distances: {[f'{d:.0f}m ({r.title})' for r, d in zip(results, distances)]}")
        assert distances == sorted(distances)

    def test_all_api_fields_present(self):
        """
        Đầu vào : Mock Bún cá Bà Bảy
        Mong đợi (tất cả trường từ API đều có mặt và đúng giá trị):
            position             = 1
            place_id             = "4201058877741143770"
            provider_id          = "/g/12vrd7h2s"
            title                = "Bún cá Nha Trang Bà Bảy"
            type                 = "Nhà hàng"
            address              = "12 Bến Chợ, Nha Trang, Khánh Hòa"
            rating               = 4.6
            review_count         = 234
            review_count_original= "(234)"
            description          chứa "cá tươi"
            thumbnail            bắt đầu "https://"
            thumbnail_large      bắt đầu "https://"
            place_id_search      chứa "ludocid"
        Và các trường tính thêm:
            distance_text        = "345m"
            maps_url             bắt đầu "https://www.google.com/maps/dir/"
        """
        results = self._call()
        r = next(x for x in results if "Bà Bảy" in x.title)

        print(f"\n  [All fields: {r.title}]")
        print(f"    position              = {r.position}")
        print(f"    place_id              = {r.place_id}")
        print(f"    provider_id           = {r.provider_id}")
        print(f"    type                  = {r.type}")
        print(f"    address               = {r.address}")
        print(f"    rating                = {r.rating}")
        print(f"    review_count          = {r.review_count}")
        print(f"    review_count_original = {r.review_count_original}")
        print(f"    description           = {r.description}")
        print(f"    thumbnail             = {r.thumbnail}")
        print(f"    thumbnail_large       = {r.thumbnail_large}")
        print(f"    distance_text         = {r.distance_text}")
        print(f"    maps_url              = {r.maps_url[:55]}...")

        assert r.position              == 1
        assert r.place_id              == "4201058877741143770"
        assert r.provider_id           == "/g/12vrd7h2s"
        assert r.title                 == "Bún cá Nha Trang Bà Bảy"
        assert r.type                  == "Nhà hàng"
        assert r.address               == "12 Bến Chợ, Nha Trang, Khánh Hòa"
        assert r.rating                == 4.6
        assert r.review_count          == 234
        assert r.review_count_original == "(234)"
        assert "cá tươi" in (r.description or "")
        assert (r.thumbnail or "").startswith("https://")
        assert (r.thumbnail_large or "").startswith("https://")
        assert "ludocid" in r.place_id_search
        assert r.distance_text         == "345m"
        assert r.maps_url.startswith("https://www.google.com/maps/dir/")

    def test_empty_response(self):
        """
        Đầu vào : local_results rỗng
        Mong đợi: list rỗng, không crash
        """
        results = self._call({"local_results": []})
        print(f"\n  [empty] → {results}")
        assert results == []

    def test_missing_optional_fields(self):
        """
        Đầu vào : quán không có rating, description, thumbnail
        Mong đợi: không crash, các trường đó là None
        """
        minimal = {"local_results": [{
            "position": 1,
            "place_id": "123", "place_id_search": "", "provider_id": "",
            "title": "Quán Test", "type": "Nhà hàng", "address": "Test",
            "gps_coordinates": {"latitude": 12.2451, "longitude": 109.1943},
        }]}
        results = self._call(minimal)
        r = results[0]
        print(f"\n  [minimal] rating={r.rating} desc={r.description} thumb={r.thumbnail}")
        assert r.rating       is None
        assert r.description  is None
        assert r.thumbnail    is None
        assert r.distance_m   == 0.0   # cùng vị trí với user


# ── Integration tests (cần MAP_API thật) ────────────────────────────────────

@pytest.mark.skipif(not HAS_KEY, reason="Cần MAP_API thật trong .env")
class TestIntegration:

    def setup_method(self):
        self.svc = LocationService()

    def test_ip_detect(self):
        """
        Đầu vào : không truyền gì
        Mong đợi: Location với lat/lng hợp lệ, source='ip'
        """
        loc = self.svc.get_location()
        print(f"\n  [IP] → {loc.display_name} ({loc.lat:.4f}, {loc.lng:.4f})")
        assert -90 <= loc.lat <= 90
        assert -180 <= loc.lng <= 180
        assert loc.source == "ip"

    def test_nearby_nha_trang(self):
        """
        Đầu vào : Nha Trang (12.2451, 109.1943), 1.5km, "quán ăn"
        Mong đợi:
            - Có ít nhất 1 kết quả
            - Sắp xếp gần → xa
            - Mỗi quán có title, address, gps_coordinates, rating
        """
        loc     = self.svc.get_location(lat=12.2451, lng=109.1943)
        results = self.svc.get_nearby_restaurants(loc, radius_km=1.5, query="quán ăn")
        print(f"\n  [Nha Trang 1.5km] → {len(results)} quán")
        for r in results[:5]:
            print(f"    [{r.position}] {r.title} | {r.distance_text} | ⭐{r.rating} | {r.type}")
        assert len(results) > 0
        assert [r.distance_m for r in results] == sorted(r.distance_m for r in results)
        r0 = results[0]
        assert r0.title   != ""
        assert r0.address != ""
        assert r0.lat     != 0.0
        assert r0.maps_url.startswith("https://")

    def test_nearby_ha_noi_cafe(self):
        """
        Đầu vào : Hà Nội (21.0285, 105.8542), 1.5km, "quán cafe"
        Mong đợi: list (có thể rỗng), không crash, các trường đúng kiểu
        """
        loc     = self.svc.get_location(lat=21.0285, lng=105.8542)
        results = self.svc.get_nearby_restaurants(loc, radius_km=1.5, query="quán cafe")
        print(f"\n  [HN cafe] → {len(results)} quán")
        for r in results[:3]:
            print(f"    {r.title} | {r.distance_text} | {r.type} | ⭐{r.rating}")
            print(f"      desc: {r.description}")
        assert isinstance(results, list)
        for r in results:
            assert isinstance(r.title,    str)
            assert isinstance(r.distance_m, float)
            assert isinstance(r.maps_url, str)
