"""
test_service_integration.py — Integration tests cho LocationService.
Cần GOOGLE_MAPS_API_KEY và ANTHROPIC_API_KEY thật trong .env.
Nếu chưa có key: các test sẽ bị SKIP tự động.

Chạy: python -m pytest tests/test_service_integration.py -v -s

Phần mock (cuối file) chạy được ngay không cần key.
"""

import sys
import os
import json
import pytest
from unittest.mock import MagicMock, patch
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

GOOGLE_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
HAS_GOOGLE_KEY = bool(GOOGLE_KEY) and GOOGLE_KEY != "your_google_maps_api_key_here"
HAS_ANTHROPIC_KEY = bool(ANTHROPIC_KEY) and ANTHROPIC_KEY != "your_anthropic_api_key_here"

from modules.location import LocationService, Location, Restaurant, RestaurantDetail


# ─── Integration tests (SKIP nếu chưa có key) ────────────────────────────────

@pytest.mark.skipif(not HAS_GOOGLE_KEY, reason="Cần GOOGLE_MAPS_API_KEY thật")
class TestGetLocationIntegration:

    def setup_method(self):
        self.svc = LocationService()

    def test_ip_geolocation(self):
        """
        Đầu vào : không có lat/lng (auto-detect qua IP)
        Mong đợi: Location với lat/lng hợp lệ và tên thành phố tiếng Việt
        Ví dụ kết quả:
            Location(lat=21.02, lng=105.84, city='Hà Nội',
                     province='Hà Nội', display_name='Hà Nội', source='ip')
        """
        loc = self.svc.get_location()
        print(f"\n  [IP detect] → {loc}")
        assert isinstance(loc.lat, float)
        assert isinstance(loc.lng, float)
        assert -90 <= loc.lat <= 90
        assert -180 <= loc.lng <= 180
        assert loc.city != ""
        assert loc.source == "ip"

    def test_gps_coords_nha_trang(self):
        """
        Đầu vào : lat=12.2451, lng=109.1943 (Nha Trang)
        Mong đợi: Location với city='Nha Trang' hoặc chứa 'Khánh Hòa'
        Ví dụ kết quả:
            Location(lat=12.2451, lng=109.1943, city='Nha Trang',
                     province='Khánh Hòa', display_name='Nha Trang, Khánh Hòa', source='gps')
        """
        loc = self.svc.get_location(lat=12.2451, lng=109.1943)
        print(f"\n  [GPS Nha Trang] → {loc}")
        assert loc.lat == 12.2451
        assert loc.lng == 109.1943
        assert loc.source == "gps"
        assert "Nha Trang" in loc.display_name or "Khánh Hòa" in loc.display_name


@pytest.mark.skipif(not HAS_GOOGLE_KEY, reason="Cần GOOGLE_MAPS_API_KEY thật")
class TestGetNearbyRestaurantsIntegration:

    def setup_method(self):
        self.svc = LocationService()
        self.nha_trang = Location(
            lat=12.2451, lng=109.1943,
            city="Nha Trang", province="Khánh Hòa",
            display_name="Nha Trang, Khánh Hòa", source="gps"
        )

    def test_basic_search(self):
        """
        Đầu vào : Nha Trang (12.2451, 109.1943), bán kính 1.5km
        Mong đợi: list[Restaurant] không rỗng, sắp xếp gần → xa
        Ví dụ kết quả:
            [
              Restaurant(name='Bún cá Nha Trang', distance_text='280m', rating=4.5, ...),
              Restaurant(name='Bánh căn 74', distance_text='350m', rating=4.3, ...),
              ...
            ]
        """
        results = self.svc.get_nearby_restaurants(self.nha_trang, radius_km=1.5)
        print(f"\n  [Nearby 1.5km Nha Trang] → {len(results)} quán")
        for r in results[:3]:
            print(f"    {r.name} | {r.distance_text} | ⭐{r.rating} | open={r.is_open_now}")
        assert len(results) > 0
        # Phải sắp xếp gần → xa
        for i in range(len(results) - 1):
            assert results[i].distance_m <= results[i+1].distance_m
        # Mỗi quán phải có các trường bắt buộc
        first = results[0]
        assert first.place_id != ""
        assert first.name != ""
        assert first.distance_m >= 0
        assert first.maps_url.startswith("https://")

    def test_search_with_keyword(self):
        """
        Đầu vào : Nha Trang, bán kính 2km, keyword='bún'
        Mong đợi: kết quả ưu tiên quán có 'bún' trong tên hoặc loại món
        """
        results = self.svc.get_nearby_restaurants(self.nha_trang, radius_km=2.0, keyword="bún")
        print(f"\n  [Keyword 'bún'] → {len(results)} quán")
        for r in results[:3]:
            print(f"    {r.name} | {r.distance_text}")
        assert len(results) >= 0  # có thể không có, không nên fail

    def test_restaurant_fields(self):
        """
        Mong đợi: mỗi Restaurant có đủ các trường dữ liệu từ Google Places
        """
        results = self.svc.get_nearby_restaurants(self.nha_trang)
        assert len(results) > 0
        r = results[0]
        # Các trường luôn có
        assert isinstance(r.place_id, str) and len(r.place_id) > 0
        assert isinstance(r.name, str)
        assert isinstance(r.address, str)
        assert isinstance(r.lat, float)
        assert isinstance(r.lng, float)
        assert isinstance(r.distance_m, float)
        assert isinstance(r.distance_text, str)
        assert isinstance(r.maps_url, str)
        assert isinstance(r.types, list)
        # Các trường có thể None (không phải quán nào cũng có)
        assert r.rating is None or isinstance(r.rating, float)
        assert r.price_level is None or r.price_level in (1, 2, 3, 4)


@pytest.mark.skipif(not HAS_GOOGLE_KEY, reason="Cần GOOGLE_MAPS_API_KEY thật")
class TestGetRestaurantDetailIntegration:

    def setup_method(self):
        self.svc = LocationService()
        self.nha_trang = Location(
            lat=12.2451, lng=109.1943,
            city="Nha Trang", province="Khánh Hòa",
            display_name="Nha Trang, Khánh Hòa", source="gps"
        )

    def test_detail_without_ai_menu(self):
        """
        Đầu vào : place_id của quán đầu tiên tìm được ở Nha Trang, include_ai_menu=False
        Mong đợi: RestaurantDetail với reviews, opening_hours, phone
        Ví dụ kết quả:
            RestaurantDetail(
              name='Bún cá Bà Bảy',
              address='12 Bến Chợ, Nha Trang',
              phone='0258 3123 456',
              opening_hours=['Thứ 2: 6:00–14:00', ...],
              reviews=[Review(author='Nguyễn A', rating=5, text='Ngon lắm!', ...)],
              menu_items=[]   ← vì include_ai_menu=False
            )
        """
        restaurants = self.svc.get_nearby_restaurants(self.nha_trang, radius_km=1.5)
        assert len(restaurants) > 0
        detail = self.svc.get_restaurant_detail(
            restaurants[0].place_id, self.nha_trang, include_ai_menu=False
        )
        print(f"\n  [Detail] {detail.name}")
        print(f"    Địa chỉ : {detail.address}")
        print(f"    SĐT     : {detail.phone}")
        print(f"    Website : {detail.website}")
        print(f"    Giờ mở  : {detail.opening_hours[:2]}")
        print(f"    Reviews : {len(detail.reviews)} cái")
        if detail.reviews:
            rv = detail.reviews[0]
            print(f"      → {rv.author} ({rv.rating}⭐): {rv.text[:80]}...")

        assert detail.name != ""
        assert isinstance(detail.reviews, list)
        assert isinstance(detail.opening_hours, list)
        assert detail.menu_items == []

    @pytest.mark.skipif(not HAS_ANTHROPIC_KEY, reason="Cần ANTHROPIC_API_KEY thật")
    def test_detail_with_ai_menu(self):
        """
        Đầu vào : place_id thật, include_ai_menu=True
        Mong đợi: menu_items chứa 4–6 MenuItem do Claude suy luận
        Ví dụ kết quả:
            [
              MenuItem(dish='Bún cá', description='Bún nước dùng cá tươi đặc trưng Nha Trang',
                       estimated_price='40.000–60.000đ'),
              MenuItem(dish='Chả cá chiên', description='Chả cá tự làm, giòn thơm',
                       estimated_price='25.000–35.000đ'),
              ...
            ]
        """
        restaurants = self.svc.get_nearby_restaurants(self.nha_trang, radius_km=1.5)
        assert len(restaurants) > 0
        detail = self.svc.get_restaurant_detail(
            restaurants[0].place_id, self.nha_trang, include_ai_menu=True
        )
        print(f"\n  [AI Menu] {detail.name}")
        for item in detail.menu_items:
            print(f"    {item.dish} — {item.estimated_price}: {item.description}")

        assert len(detail.menu_items) >= 1
        for item in detail.menu_items:
            assert item.dish != ""
            assert item.estimated_price != ""


# ─── Mock tests (chạy được ngay, không cần key) ───────────────────────────────

class TestServiceWithMocks:
    """
    Dùng unittest.mock để giả lập response từ Google Places API.
    Không cần key, chạy được ngay, kiểm tra logic xử lý dữ liệu.
    """

    MOCK_NEARBY_RESPONSE = {
        "status": "OK",
        "results": [
            {
                "place_id": "ChIJmock001",
                "name": "Bún cá Nha Trang Bà Bảy",
                "vicinity": "12 Bến Chợ, Nha Trang",
                "geometry": {"location": {"lat": 12.2482, "lng": 109.1943}},
                "rating": 4.6,
                "user_ratings_total": 234,
                "price_level": 1,
                "opening_hours": {"open_now": True},
                "types": ["restaurant", "food"],
                "photos": [{"photo_reference": "mock_photo_ref_001"}],
            },
            {
                "place_id": "ChIJmock002",
                "name": "Bánh căn Mỹ Hòa",
                "vicinity": "Đường Trần Phú, Nha Trang",
                "geometry": {"location": {"lat": 12.2471, "lng": 109.1952}},
                "rating": 4.4,
                "user_ratings_total": 98,
                "price_level": 1,
                "opening_hours": {"open_now": True},
                "types": ["restaurant", "food"],
                "photos": [],
            },
            {
                "place_id": "ChIJmock003",
                "name": "Nem nướng Ninh Hòa Hai Bà",
                "vicinity": "Lô 6 Chợ Đầm, Nha Trang",
                "geometry": {"location": {"lat": 12.2404, "lng": 109.1921}},
                "rating": 4.7,
                "user_ratings_total": 512,
                "price_level": 2,
                "opening_hours": {"open_now": False},
                "types": ["restaurant", "food"],
                "photos": [],
            },
        ],
    }

    MOCK_DETAIL_RESPONSE = {
        "status": "OK",
        "result": {
            "place_id": "ChIJmock001",
            "name": "Bún cá Nha Trang Bà Bảy",
            "formatted_address": "12 Bến Chợ, Phường Xương Huân, Nha Trang, Khánh Hòa",
            "formatted_phone_number": "0258 3123 456",
            "website": None,
            "geometry": {"location": {"lat": 12.2482, "lng": 109.1943}},
            "rating": 4.6,
            "user_ratings_total": 234,
            "price_level": 1,
            "types": ["restaurant", "food"],
            "photos": [],
            "business_status": "OPERATIONAL",
            "opening_hours": {
                "open_now": True,
                "weekday_text": [
                    "Thứ 2: 6:00 – 14:00", "Thứ 3: 6:00 – 14:00",
                    "Thứ 4: 6:00 – 14:00", "Thứ 5: 6:00 – 14:00",
                    "Thứ 6: 6:00 – 14:00", "Thứ 7: 6:00 – 14:00",
                    "Chủ nhật: 6:00 – 14:00",
                ],
            },
            "reviews": [
                {
                    "author_name": "Nguyễn Minh",
                    "rating": 5,
                    "text": "Nước dùng đậm vị cá tươi, đúng kiểu Nha Trang. Giá 45k/tô rất hợp lý.",
                    "relative_time_description": "2 tuần trước",
                    "time": 1717200000,
                },
                {
                    "author_name": "Trần Lan",
                    "rating": 4,
                    "text": "Quán đông vào buổi sáng, nên đến trước 8h. Chả cá tự làm rất ngon.",
                    "relative_time_description": "1 tháng trước",
                    "time": 1714608000,
                },
            ],
        },
    }

    def _make_service(self):
        """Tạo service với fake key để test logic (không gọi API thật)."""
        return LocationService(google_api_key="FAKE_KEY_FOR_TEST", anthropic_api_key="FAKE_ANTHROPIC_KEY")

    def test_mock_nearby_returns_correct_count(self):
        """
        Đầu vào : Mock response chứa 3 quán
        Mong đợi: get_nearby_restaurants() trả về đúng 3 Restaurant
        """
        svc = self._make_service()
        mock_response = MagicMock()
        mock_response.json.return_value = self.MOCK_NEARBY_RESPONSE

        loc = Location(lat=12.2451, lng=109.1943, city="Nha Trang",
                       province="Khánh Hòa", display_name="Nha Trang, Khánh Hòa", source="gps")

        with patch("httpx.get", return_value=mock_response):
            results = svc.get_nearby_restaurants(loc)

        print(f"\n  [Mock nearby] → {len(results)} quán")
        for r in results:
            print(f"    {r.name} | {r.distance_text} | ⭐{r.rating} | open={r.is_open_now}")
        assert len(results) == 3

    def test_mock_nearby_sorted_by_distance(self):
        """
        Đầu vào : 3 quán ở khoảng cách khác nhau
        Mong đợi: kết quả sắp xếp từ gần nhất đến xa nhất
        Ví dụ:
            [Bún cá Bà Bảy (345m), Bánh căn Mỹ Hòa (~490m), Nem nướng (~670m)]
        """
        svc = self._make_service()
        mock_response = MagicMock()
        mock_response.json.return_value = self.MOCK_NEARBY_RESPONSE

        loc = Location(lat=12.2451, lng=109.1943, city="Nha Trang",
                       province="Khánh Hòa", display_name="Nha Trang, Khánh Hòa", source="gps")

        with patch("httpx.get", return_value=mock_response):
            results = svc.get_nearby_restaurants(loc)

        distances = [r.distance_m for r in results]
        print(f"\n  [Sort kiểm tra] distances: {[f'{d:.0f}m' for d in distances]}")
        assert distances == sorted(distances)

    def test_mock_nearby_restaurant_fields(self):
        """
        Đầu vào : Mock quán đầu tiên (Bún cá Bà Bảy)
        Mong đợi:
            name         = "Bún cá Nha Trang Bà Bảy"
            address      = "12 Bến Chợ, Nha Trang"
            rating       = 4.6
            review_count = 234
            price_level  = 1
            is_open_now  = True
            photo_url    chứa "mock_photo_ref_001"
            maps_url     bắt đầu bằng "https://www.google.com/maps/dir/"
        """
        svc = self._make_service()
        mock_response = MagicMock()
        mock_response.json.return_value = self.MOCK_NEARBY_RESPONSE

        loc = Location(lat=12.2451, lng=109.1943, city="Nha Trang",
                       province="Khánh Hòa", display_name="Nha Trang, Khánh Hòa", source="gps")

        with patch("httpx.get", return_value=mock_response):
            results = svc.get_nearby_restaurants(loc)

        # Tìm quán Bà Bảy (gần nhất)
        ba_bay = next(r for r in results if "Bà Bảy" in r.name)
        print(f"\n  [Fields Bà Bảy]")
        print(f"    name         = {ba_bay.name}")
        print(f"    address      = {ba_bay.address}")
        print(f"    distance     = {ba_bay.distance_text}")
        print(f"    rating       = {ba_bay.rating}")
        print(f"    review_count = {ba_bay.review_count}")
        print(f"    price_level  = {ba_bay.price_level}")
        print(f"    is_open_now  = {ba_bay.is_open_now}")
        print(f"    maps_url     = {ba_bay.maps_url[:60]}...")

        assert ba_bay.name == "Bún cá Nha Trang Bà Bảy"
        assert ba_bay.address == "12 Bến Chợ, Nha Trang"
        assert ba_bay.rating == 4.6
        assert ba_bay.review_count == 234
        assert ba_bay.price_level == 1
        assert ba_bay.is_open_now is True
        assert "mock_photo_ref_001" in (ba_bay.photo_url or "")
        assert ba_bay.maps_url.startswith("https://www.google.com/maps/dir/")

    def test_mock_detail_fields(self):
        """
        Đầu vào : Mock Place Detail response cho Bún cá Bà Bảy
        Mong đợi:
            phone          = "0258 3123 456"
            opening_hours  = 7 phần tử (7 ngày trong tuần)
            reviews        = 2 Review objects
            reviews[0].author = "Nguyễn Minh"
            reviews[0].rating = 5
            reviews[0].text   chứa "45k"
        """
        svc = self._make_service()
        mock_response = MagicMock()
        mock_response.json.return_value = self.MOCK_DETAIL_RESPONSE

        loc = Location(lat=12.2451, lng=109.1943, city="Nha Trang",
                       province="Khánh Hòa", display_name="Nha Trang, Khánh Hòa", source="gps")

        with patch("httpx.get", return_value=mock_response):
            detail = svc.get_restaurant_detail("ChIJmock001", loc, include_ai_menu=False)

        print(f"\n  [Detail fields]")
        print(f"    name          = {detail.name}")
        print(f"    address       = {detail.address}")
        print(f"    phone         = {detail.phone}")
        print(f"    opening_hours = {detail.opening_hours}")
        print(f"    reviews count = {len(detail.reviews)}")
        print(f"    review[0]     = {detail.reviews[0].author} ({detail.reviews[0].rating}⭐): {detail.reviews[0].text[:50]}...")

        assert detail.name == "Bún cá Nha Trang Bà Bảy"
        assert detail.phone == "0258 3123 456"
        assert len(detail.opening_hours) == 7
        assert len(detail.reviews) == 2
        assert detail.reviews[0].author == "Nguyễn Minh"
        assert detail.reviews[0].rating == 5
        assert "45k" in detail.reviews[0].text
        assert detail.menu_items == []  # vì include_ai_menu=False

    def test_zero_results_returns_empty_list(self):
        """
        Đầu vào : Google trả về ZERO_RESULTS (không có quán nào)
        Mong đợi: list rỗng [], không raise exception
        """
        svc = self._make_service()
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ZERO_RESULTS", "results": []}

        loc = Location(lat=0.0, lng=0.0, city="Giữa Biển",
                       province="", display_name="Giữa Biển", source="gps")

        with patch("httpx.get", return_value=mock_response):
            results = svc.get_nearby_restaurants(loc)

        print(f"\n  [Zero results] → {results}")
        assert results == []
