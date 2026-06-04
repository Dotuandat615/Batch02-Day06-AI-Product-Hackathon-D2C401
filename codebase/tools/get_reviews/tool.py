from __future__ import annotations

from typing import Any


# --- MOCK DATA ---
# TODO (P1): Thay bằng Google Places Details API thật
MOCK_REVIEWS: dict[str, list[dict[str, Any]]] = {
    "mock_place_001": [
        {"author": "Lan P.", "rating": 5, "text": "Nước dùng đậm vị cá tươi, đúng kiểu Nha Trang, giá 45k/tô.", "time": "2 tuần trước"},
        {"author": "Minh T.", "rating": 4, "text": "Quán đông nhưng phục vụ nhanh, bún tươi ngon.", "time": "1 tháng trước"},
        {"author": "Hoa N.", "rating": 5, "text": "Phải thử khi đến Nha Trang, rẻ mà ngon.", "time": "3 tuần trước"},
    ],
    "mock_place_002": [
        {"author": "Thảo L.", "rating": 4, "text": "Bánh giòn, trứng chín đều, ăn kèm mắm nêm rất ngon.", "time": "1 tuần trước"},
        {"author": "Đức V.", "rating": 5, "text": "Đặc sản Nha Trang phải thử, giá bình dân.", "time": "2 tháng trước"},
    ],
    "mock_place_003": [
        {"author": "An K.", "rating": 5, "text": "Nem cuốn bánh tráng tại chỗ, tươi ngon, không cần đặt trước.", "time": "1 tuần trước"},
        {"author": "Bình H.", "rating": 5, "text": "Món Khánh Hòa chính hiệu, review rất ổn định.", "time": "3 tuần trước"},
        {"author": "Chi M.", "rating": 4, "text": "Hơi xa trung tâm nhưng đáng đi.", "time": "1 tháng trước"},
    ],
    "mock_place_004": [
        {"author": "Duy P.", "rating": 3, "text": "Phở bình thường, không có gì đặc biệt.", "time": "8 tháng trước"},
    ],
    "mock_place_005": [
        {"author": "Mai A.", "rating": 4, "text": "Quán chay sạch sẽ, nhiều món lựa chọn.", "time": "2 tuần trước"},
        {"author": "Tú B.", "rating": 5, "text": "Thích hợp cho người ăn chay, giá hợp lý.", "time": "1 tháng trước"},
    ],
}


def get_place_reviews(
    place_id: str = "",
    max_reviews: int = 5,
) -> dict[str, Any]:
    """Lấy review của một quán ăn.

    Args:
        place_id: ID của quán (từ kết quả search_nearby).
        max_reviews: Số review tối đa cần lấy.

    Returns:
        dict với key "reviews" chứa danh sách review.
    """
    # TODO (P1): Gọi Google Places Details API thật
    # fields=reviews,name,rating,opening_hours,formatted_address

    reviews = MOCK_REVIEWS.get(place_id, [])[:max_reviews]

    return {
        "tool": "get_reviews",
        "place_id": place_id,
        "reviews": reviews,
        "review_count": len(reviews),
        "is_mock": True,
    }
