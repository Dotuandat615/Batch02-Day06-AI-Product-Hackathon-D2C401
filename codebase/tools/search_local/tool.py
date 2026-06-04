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

from modules.location import LocationService, Restaurant

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

def execute(tool_input: dict) -> str:
    """
    Chạy tool khi agent gọi.

    Params:
        tool_input : dict theo input_schema ở trên
                     {"query": "quán ăn", "lat": 12.2451, "lng": 109.1943, ...}

    Trả về:
        JSON string — agent đọc trực tiếp.
        Schema:
        {
          "location": {"display_name": "...", "lat": ..., "lng": ...},
          "query": "...",
          "radius_km": 1.5,
          "total_found": 5,
          "restaurants": [
            {
              "rank": 1,
              "name": "...",
              "address": "...",
              "distance": "350m",
              "rating": 4.6,
              "review_count": 234,
              "type": "Nhà hàng",
              "price": "1-100.000 ₫",
              "open_state": "Đang mở cửa · Đóng cửa vào 22:00",
              "operating_hours": {"thứ hai": "08:00–22:00", ...},
              "highlights": ["Cà phê ngon", "Wi-Fi"],
              "offerings": ["Cà phê", "Bánh"],
              "atmosphere": ["Yên tĩnh"],
              "popular_for": ["Phù hợp để làm việc"],
              "amenities": ["Nhà vệ sinh", "Wi-Fi miễn phí"],
              "service_options": ["Ăn tại chỗ", "Mang về"],
              "parking": ["Bãi đỗ xe miễn phí"],
              "payments": ["Thẻ tín dụng"],
              "phone": "+84 ...",
              "website": "https://...",
              "user_review": "\"Quán ngon, giá hợp lý\"",
              "maps_url": "https://www.google.com/maps/dir/...",
              "thumbnail": "https://..."
            },
            ...
          ],
          "error": null
        }
    """
    query      = tool_input.get("query", "quán ăn")
    lat        = tool_input.get("lat")
    lng        = tool_input.get("lng")
    radius_km  = float(tool_input.get("radius_km", 1.5))
    max_results = min(int(tool_input.get("max_results", 5)), 20)

    try:
        svc = LocationService()
        loc = svc.get_location(lat=lat, lng=lng)
        restaurants = svc.get_nearby_restaurants(loc, radius_km=radius_km, query=query)

        return json.dumps({
            "location": {
                "display_name": loc.display_name,
                "city":         loc.city,
                "province":     loc.province,
                "lat":          loc.lat,
                "lng":          loc.lng,
                "source":       loc.source,
            },
            "query":       query,
            "radius_km":   radius_km,
            "total_found": len(restaurants),
            "restaurants": [_format(r, rank) for rank, r in enumerate(restaurants[:max_results], 1)],
            "error":       None,
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "location":    None,
            "query":       query,
            "radius_km":   radius_km,
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
