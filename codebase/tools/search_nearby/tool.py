from __future__ import annotations

from typing import Any


# --- MOCK DATA ---
# TODO (P1): Thay bằng Google Places Nearby Search API thật
# Xem TEAM_TASKS.md > Người 1 để biết chi tiết implementation
MOCK_PLACES = [
    {
        "place_id": "mock_place_001",
        "name": "Bún cá Nha Trang Bà Bảy",
        "vicinity": "12 Bến Chợ, Nha Trang",
        "rating": 4.6,
        "user_ratings_total": 342,
        "price_level": 1,
        "opening_hours": {"open_now": True},
        "geometry": {"location": {"lat": 12.2450, "lng": 109.1950}},
        "types": ["restaurant", "food"],
    },
    {
        "place_id": "mock_place_002",
        "name": "Bánh căn Mỹ Hòa",
        "vicinity": "Đường Trần Phú, Nha Trang",
        "rating": 4.4,
        "user_ratings_total": 215,
        "price_level": 1,
        "opening_hours": {"open_now": True},
        "geometry": {"location": {"lat": 12.2480, "lng": 109.1935}},
        "types": ["restaurant", "food"],
    },
    {
        "place_id": "mock_place_003",
        "name": "Nem nướng Ninh Hòa Hai Bà",
        "vicinity": "Lô 6 Chợ Đầm, Nha Trang",
        "rating": 4.7,
        "user_ratings_total": 528,
        "price_level": 2,
        "opening_hours": {"open_now": True},
        "geometry": {"location": {"lat": 12.2410, "lng": 109.1880}},
        "types": ["restaurant", "food"],
    },
    {
        "place_id": "mock_place_004",
        "name": "Phở Hồng",
        "vicinity": "45 Lê Thánh Tôn, Nha Trang",
        "rating": 4.2,
        "user_ratings_total": 87,
        "price_level": 1,
        "opening_hours": {"open_now": False},
        "geometry": {"location": {"lat": 12.2500, "lng": 109.1960}},
        "types": ["restaurant", "food"],
    },
    {
        "place_id": "mock_place_005",
        "name": "Quán Chay An Nhiên",
        "vicinity": "23 Nguyễn Thiện Thuật, Nha Trang",
        "rating": 4.3,
        "user_ratings_total": 64,
        "price_level": 1,
        "opening_hours": {"open_now": True},
        "geometry": {"location": {"lat": 12.2460, "lng": 109.1940}},
        "types": ["restaurant", "food", "vegetarian"],
    },
]


def search_nearby_places(
    lat: float = 0.0,
    lng: float = 0.0,
    radius: int = 500,
    keyword: str = "restaurant",
    meal_time: str = "",
) -> dict[str, Any]:
    """Tìm quán ăn gần vị trí.

    Args:
        lat: Vĩ độ GPS của người dùng.
        lng: Kinh độ GPS của người dùng.
        radius: Bán kính tìm kiếm (mét), mặc định 500m.
        keyword: Từ khóa tìm kiếm bổ sung (ví dụ: "chay", "hải sản").
        meal_time: Bữa ăn (sáng/trưa/tối/khuya) — dùng để lọc quán mở giờ đó.

    Returns:
        dict với key "places" chứa danh sách quán.
    """
    # TODO (P1): Gọi Google Places API thật
    # 1. Gọi Nearby Search: https://maps.googleapis.com/maps/api/place/nearbysearch/json
    # 2. Nếu kết quả < 3: mở rộng radius (500 → 1000 → 2000 → 5000)
    # 3. Lọc theo opening_hours nếu meal_time = "khuya"

    # --- STUB: trả mock data ---
    places = MOCK_PLACES
    if keyword and keyword != "restaurant":
        keyword_lower = keyword.lower()
        places = [p for p in places if keyword_lower in str(p.get("types", [])).lower()
                  or keyword_lower in p.get("name", "").lower()]

    return {
        "tool": "search_nearby",
        "lat": lat,
        "lng": lng,
        "radius": radius,
        "keyword": keyword,
        "places": places,
        "is_mock": True,  # Xóa khi implement API thật
    }
