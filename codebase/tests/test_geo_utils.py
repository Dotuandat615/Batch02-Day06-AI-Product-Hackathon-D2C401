"""
test_geo_utils.py — Unit tests cho geo_utils.py (không cần API key, chạy được ngay).

Đầu vào / đầu ra mong đợi được ghi rõ trong từng test.
Chạy: python -m pytest tests/test_geo_utils.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

from modules.location.geo_utils import haversine_m, fmt_distance, maps_url


# ─── haversine_m ─────────────────────────────────────────────────────────────

class TestHaversineM:

    def test_same_point_is_zero(self):
        """
        Đầu vào : cùng tọa độ (12.2451, 109.1943) — (12.2451, 109.1943)
        Mong đợi: 0.0 mét
        """
        result = haversine_m(12.2451, 109.1943, 12.2451, 109.1943)
        assert result == 0.0

    def test_nha_trang_hotel_to_ben_cho(self):
        """
        Đầu vào : Khách sạn gần biển Nha Trang (12.2451, 109.1943)
                  → Bến Chợ Nha Trang     (12.2482, 109.1943)
        Mong đợi: ~345m (chênh lệch ~0.0031 độ vĩ ≈ 345m)
        Sai số cho phép: ±30m
        """
        result = haversine_m(12.2451, 109.1943, 12.2482, 109.1943)
        assert 315 < result < 375, f"Kết quả: {result:.1f}m"

    def test_nha_trang_to_da_lat(self):
        """
        Đầu vào : Nha Trang (12.2451, 109.1943) → Đà Lạt (11.9465, 108.4419)
        Mong đợi: ~88km đường chim bay (không phải đường bộ ~140km)
        Sai số cho phép: ±5km
        """
        result = haversine_m(12.2451, 109.1943, 11.9465, 108.4419)
        assert 83_000 < result < 93_000, f"Kết quả: {result/1000:.1f}km"

    def test_ha_noi_to_hcm(self):
        """
        Đầu vào : Hà Nội (21.0285, 105.8542) → TP. HCM (10.8231, 106.6297)
        Mong đợi: ~1138km đường chim bay (không phải đường bộ ~1750km)
        Sai số cho phép: ±20km
        """
        result = haversine_m(21.0285, 105.8542, 10.8231, 106.6297)
        assert 1_118_000 < result < 1_158_000, f"Kết quả: {result/1000:.1f}km"

    def test_symmetry(self):
        """
        Đầu vào : A→B và B→A
        Mong đợi: khoảng cách bằng nhau (tính chất đối xứng)
        """
        ab = haversine_m(12.2451, 109.1943, 10.8231, 106.6297)
        ba = haversine_m(10.8231, 106.6297, 12.2451, 109.1943)
        assert abs(ab - ba) < 0.001


# ─── fmt_distance ─────────────────────────────────────────────────────────────

class TestFmtDistance:

    def test_zero(self):
        """Đầu vào: 0m → Mong đợi: '0m'"""
        assert fmt_distance(0) == "0m"

    def test_small_metres(self):
        """Đầu vào: 50m → Mong đợi: '50m'"""
        assert fmt_distance(50) == "50m"

    def test_350_metres(self):
        """Đầu vào: 350.4m → Mong đợi: '350m' (làm tròn)"""
        assert fmt_distance(350.4) == "350m"

    def test_just_under_1km(self):
        """Đầu vào: 999m → Mong đợi: '999m' (chưa đủ 1km)"""
        assert fmt_distance(999) == "999m"

    def test_exactly_1km(self):
        """Đầu vào: 1000m → Mong đợi: '1.0km'"""
        assert fmt_distance(1000) == "1.0km"

    def test_1_point_2_km(self):
        """Đầu vào: 1200m → Mong đợi: '1.2km'"""
        assert fmt_distance(1200) == "1.2km"

    def test_5_point_5_km(self):
        """Đầu vào: 5500m → Mong đợi: '5.5km'"""
        assert fmt_distance(5500) == "5.5km"


# ─── maps_url ─────────────────────────────────────────────────────────────────

class TestMapsUrl:

    def test_with_origin_uses_dir(self):
        """
        Đầu vào : dest=(12.2482, 109.1943), origin=(12.2451, 109.1943)
        Mong đợi: URL dạng google.com/maps/dir/origin/dest
                  → mở Google Maps chỉ đường từ user đến quán
        """
        url = maps_url(12.2482, 109.1943, "Bún cá Bà Bảy", 12.2451, 109.1943)
        assert "google.com/maps/dir/" in url
        assert "12.2482" in url
        assert "12.2451" in url

    def test_without_origin_uses_search(self):
        """
        Đầu vào : dest=(12.2482, 109.1943), không có origin
        Mong đợi: URL dạng google.com/maps/search/?api=1&query=...
                  → mở Google Maps hiển thị vị trí quán
        """
        url = maps_url(12.2482, 109.1943, "Bánh căn Mỹ Hòa")
        assert "google.com/maps/search/" in url
        assert "12.2482" in url

    def test_is_valid_url_string(self):
        """Mong đợi: kết quả luôn là string bắt đầu bằng https://"""
        url = maps_url(10.0, 106.0, "Test Restaurant")
        assert isinstance(url, str)
        assert url.startswith("https://")
