"""
tools/search_local/tool.py

Tool tìm quán ăn gần vị trí người dùng, thiết kế để tích hợp vào AI agent.

Hai thành phần:
  TOOL_DEFINITION  — schema theo chuẩn Claude API tool_use (dùng khi khai báo tool cho LLM)
  execute(input)   — hàm chạy thực sự khi agent gọi tool này

Cách dùng trong agent loop:
    from tools.search_local.tool import TOOL_DEFINITION, execute

    # 1. Khai báo tool cho Claude
    response = client.messages.create(
        model="claude-sonnet-4-6",
        tools=[TOOL_DEFINITION],
        messages=[...]
    )

    # 2. Khi Claude trả về tool_use block:
    for block in response.content:
        if block.type == "tool_use" and block.name == TOOL_DEFINITION["name"]:
            result = execute(block.input)
            # trả result về cho Claude qua tool_result message
"""

import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pydantic import BaseModel, Field
from modules.location import LocationService, Restaurant


class SearchInput(BaseModel):
    query: str = "quán ăn"
    lat: float | None = None
    lng: float | None = None
    radius_km: float = 1.5
    max_results: int = Field(default=5, ge=1, le=20)

# ── Tool schema (Claude API format) ───────────────────────────────────────────

TOOL_DEFINITION = {
    "name": "search_nearby_restaurants",
    "description": (
        "Tìm danh sách quán ăn / cafe / nhà hàng gần vị trí người dùng. "
        "Trả về tên quán, địa chỉ, khoảng cách, rating, giờ mở cửa, giá, "
        "tiện ích, số điện thoại, link Google Maps và review nổi bật. "
        "Dùng khi người dùng hỏi 'quán ăn gần đây', 'tìm cafe', "
        "'đặc sản vùng này', hoặc bất kỳ yêu cầu tìm nơi ăn uống theo vị trí."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Từ khoá tìm kiếm. Ví dụ: 'quán ăn', 'quán cafe', "
                    "'bún bò', 'đặc sản', 'chay', 'hải sản'. "
                    "Nên dùng tiếng Việt để kết quả chính xác hơn."
                ),
            },
            "lat": {
                "type": "number",
                "description": "Vĩ độ (latitude) của người dùng. Bỏ qua để tự detect qua IP.",
            },
            "lng": {
                "type": "number",
                "description": "Kinh độ (longitude) của người dùng. Bỏ qua để tự detect qua IP.",
            },
            "radius_km": {
                "type": "number",
                "description": (
                    "Bán kính tìm kiếm tính bằng km. "
                    "Mặc định 1.5km (phù hợp đi bộ). "
                    "Dùng 3.0–5.0 khi không tìm thấy kết quả phù hợp."
                ),
                "default": 1.5,
            },
            "max_results": {
                "type": "integer",
                "description": "Số quán tối đa trả về. Mặc định 5, tối đa 20.",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}

# ── Execute ───────────────────────────────────────────────────────────────────

def execute(**kwargs) -> str:
    """
    Chạy tool khi agent gọi.

    Params (keyword args, validated by SearchInput):
        query      : từ khoá tìm kiếm
        lat        : vĩ độ người dùng (None → auto-detect qua IP)
        lng        : kinh độ người dùng (None → auto-detect qua IP)
        radius_km  : bán kính km (default 1.5)
        max_results: số quán tối đa (default 5, max 20)

    Trả về:
        JSON string — agent đọc trực tiếp.
    """
    inp = SearchInput(**kwargs)

    try:
        svc = LocationService()
        loc = svc.get_location(lat=inp.lat, lng=inp.lng)
        restaurants = svc.get_nearby_restaurants(loc, radius_km=inp.radius_km, query=inp.query)

        return json.dumps({
            "location": {
                "display_name": loc.display_name,
                "city":         loc.city,
                "province":     loc.province,
                "lat":          loc.lat,
                "lng":          loc.lng,
                "source":       loc.source,
            },
            "query":       inp.query,
            "radius_km":   inp.radius_km,
            "total_found": len(restaurants),
            "restaurants": [_format(r, rank) for rank, r in enumerate(restaurants[:inp.max_results], 1)],
            "error":       None,
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "location":    None,
            "query":       inp.query,
            "radius_km":   inp.radius_km,
            "total_found": 0,
            "restaurants": [],
            "error":       str(e),
        }, ensure_ascii=False)


def _format(r: Restaurant, rank: int) -> dict:
    """Chuyển Restaurant dataclass → dict gọn cho agent đọc."""
    return {
        "rank":            rank,
        "name":            r.title,
        "address":         r.address,
        "distance":        r.distance_text,
        "distance_m":      round(r.distance_m),
        "lat":             r.lat,
        "lng":             r.lng,
        "rating":          r.rating,
        "review_count":    r.review_count,
        "type":            r.type,
        "types":           r.types,
        "price":           r.price,
        "price_level":     r.price_level,
        "open_state":      r.open_state,
        "operating_hours": r.operating_hours,
        "highlights":      r.highlights,
        "offerings":       r.offerings,
        "atmosphere":      r.atmosphere,
        "popular_for":     r.popular_for,
        "amenities":       r.amenities,
        "service_options": r.service_options_list,
        "payments":        r.payments,
        "parking":         r.parking,
        "phone":           r.phone,
        "website":         r.website,
        "user_review":     r.user_review,
        "maps_url":        r.maps_url,
        "thumbnail":       r.thumbnail,
        "place_id":        r.place_id,
        "data_id":         r.data_id,
    }
