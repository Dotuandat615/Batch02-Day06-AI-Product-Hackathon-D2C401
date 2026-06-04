"""
places.py — Google Places API integration.
Provides:
  - get_nearby_restaurants(): Nearby Search filtered by MCQ profile
  - get_restaurant_detail():  Place Details + reviews
  - get_ai_menu():            Claude-generated menu for a restaurant
"""

import os
import json
import httpx
import anthropic
from dataclasses import dataclass, field
from typing import Optional
from .geo_utils import haversine_distance, format_distance, estimate_walk_time, maps_directions_url, maps_search_url

PLACES_BASE = "https://maps.googleapis.com/maps/api/place"


@dataclass
class Restaurant:
    place_id: str
    name: str
    address: str
    lat: float
    lng: float
    rating: Optional[float]
    review_count: Optional[int]
    price_level: Optional[int]      # 1–4 ($→$$$$)
    is_open_now: Optional[bool]
    photo_reference: Optional[str]
    types: list[str] = field(default_factory=list)
    # Enriched after distance calculation:
    distance_metres: Optional[float] = None
    distance_text: str = ""
    walk_time: str = ""
    maps_url: str = ""
    # AI-assessed confidence:
    confidence: str = "high"        # "high" | "medium" | "low"
    warning: Optional[str] = None


@dataclass
class RestaurantDetail:
    place_id: str
    name: str
    address: str
    phone: Optional[str]
    website: Optional[str]
    opening_hours: list[str]        # ["Thứ 2: 7:00–22:00", ...]
    reviews: list[dict]             # [{ author, rating, text, time }]
    maps_url: str
    ai_menu: list[dict] = field(default_factory=list)   # [{ dish, description, estimated_price }]


# ─── Nearby Search ────────────────────────────────────────────────────────────

async def get_nearby_restaurants(
    lat: float,
    lng: float,
    mcq: dict,
    radius_metres: int = 1500,
) -> dict:
    """
    Search for restaurants near (lat, lng) matching the user's MCQ profile.

    mcq keys: meal_time, group_size, style, dietary

    Returns:
    {
      "status": "success" | "low_confidence" | "failure",
      "restaurants": [Restaurant, ...],   # top 3 after ranking
      "correction_options": [...],        # only when status == "failure"
    }
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_MAPS_API_KEY không được đặt trong .env")

    keyword = _mcq_to_keyword(mcq)
    raw = await _places_nearby_search(lat, lng, radius_metres, keyword, api_key)

    if not raw:
        return {
            "status": "failure",
            "restaurants": [],
            "correction_options": [
                f"Mở rộng bán kính lên {radius_metres * 2 // 1000}km",
                "Bỏ bộ lọc phong cách, tìm quán ăn bất kỳ gần nhất",
                "Tìm cửa hàng tiện lợi có đồ ăn sẵn",
            ],
        }

    restaurants = [_parse_place(p, lat, lng) for p in raw]
    restaurants = _apply_dietary_filter(restaurants, mcq.get("dietary", ""))
    restaurants = _rank_and_trim(restaurants, mcq)

    if not restaurants:
        return {
            "status": "failure",
            "restaurants": [],
            "correction_options": [
                "Mở rộng bán kính tìm kiếm",
                "Bỏ yêu cầu đặc biệt để xem thêm lựa chọn",
            ],
        }

    status = "success"
    if any(r.confidence in ("medium", "low") for r in restaurants):
        status = "low_confidence"

    return {"status": status, "restaurants": restaurants, "correction_options": []}


async def _places_nearby_search(lat, lng, radius, keyword, api_key) -> list:
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "type": "restaurant",
        "language": "vi",
        "key": api_key,
    }
    if keyword:
        params["keyword"] = keyword

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{PLACES_BASE}/nearbysearch/json", params=params)
        resp.raise_for_status()
        data = resp.json()

    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        raise RuntimeError(f"Google Places Nearby Search error: {data.get('status')} — {data.get('error_message', '')}")

    return data.get("results", [])


def _parse_place(p: dict, user_lat: float, user_lng: float) -> Restaurant:
    loc = p.get("geometry", {}).get("location", {})
    r_lat, r_lng = loc.get("lat", 0), loc.get("lng", 0)
    metres = haversine_distance(user_lat, user_lng, r_lat, r_lng)
    rating = p.get("rating")
    review_count = p.get("user_ratings_total", 0)

    # Confidence heuristic
    if rating and rating >= 4.0 and review_count >= 50:
        confidence = "high"
    elif rating and rating >= 3.5 and review_count >= 10:
        confidence = "medium"
    else:
        confidence = "low"

    warning = None
    if review_count and review_count < 10:
        warning = "Quán này có ít review — nên kiểm tra trên Google Maps trước khi đến."
    if not p.get("opening_hours", {}).get("open_now", True):
        warning = "Quán hiện có thể đã đóng cửa. Kiểm tra giờ mở cửa trước khi đi."

    photos = p.get("photos", [])
    photo_ref = photos[0].get("photo_reference") if photos else None

    return Restaurant(
        place_id=p["place_id"],
        name=p.get("name", ""),
        address=p.get("vicinity", ""),
        lat=r_lat,
        lng=r_lng,
        rating=rating,
        review_count=review_count,
        price_level=p.get("price_level"),
        is_open_now=p.get("opening_hours", {}).get("open_now"),
        photo_reference=photo_ref,
        types=p.get("types", []),
        distance_metres=metres,
        distance_text=format_distance(metres),
        walk_time=estimate_walk_time(metres),
        maps_url=maps_directions_url(r_lat, r_lng, p.get("name", ""), user_lat, user_lng),
        confidence=confidence,
        warning=warning,
    )


def _mcq_to_keyword(mcq: dict) -> str:
    """Map MCQ style answer to a Google Places keyword for better results."""
    style_map = {
        "Đặc sản địa phương": "đặc sản",
        "Nhanh - gọn": "ăn nhanh",
        "Thoải mái - ngồi lâu": "nhà hàng",
        "Bình dân - no bụng": "cơm bình dân",
    }
    dietary_map = {
        "Chay": "chay",
        "Không hải sản": "",
        "Không cay": "",
        "Không có yêu cầu gì": "",
    }
    parts = []
    style_kw = style_map.get(mcq.get("style", ""), "")
    dietary_kw = dietary_map.get(mcq.get("dietary", ""), "")
    if style_kw:
        parts.append(style_kw)
    if dietary_kw:
        parts.append(dietary_kw)
    return " ".join(parts)


def _apply_dietary_filter(restaurants: list, dietary: str) -> list:
    """Flag low-confidence restaurants when dietary restriction is critical."""
    if dietary in ("Chay", "Không hải sản"):
        for r in restaurants:
            if r.confidence == "high":
                r.confidence = "medium"
                r.warning = (
                    r.warning or ""
                ) + f" Yêu cầu '{dietary}' chưa được xác nhận — hỏi lại quán trước khi đến."
    return restaurants


def _rank_and_trim(restaurants: list, mcq: dict) -> list:
    """Sort by (confidence_score, rating, distance) and return top 3."""
    conf_score = {"high": 2, "medium": 1, "low": 0}
    is_open = mcq.get("meal_time", "") in ("Sáng", "Trưa", "Tối")

    def score(r):
        open_bonus = 1 if (is_open and r.is_open_now) else 0
        return (conf_score.get(r.confidence, 0), open_bonus, r.rating or 0, -(r.distance_metres or 99999))

    return sorted(restaurants, key=score, reverse=True)[:3]


# ─── Place Details ─────────────────────────────────────────────────────────────

async def get_restaurant_detail(place_id: str, user_lat: float = None, user_lng: float = None) -> RestaurantDetail:
    """
    Fetch full detail for a restaurant: hours, phone, reviews, then call AI for menu.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_MAPS_API_KEY không được đặt trong .env")

    fields = "name,formatted_address,formatted_phone_number,website,opening_hours,reviews,geometry,types"
    params = {"place_id": place_id, "fields": fields, "language": "vi", "key": api_key}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{PLACES_BASE}/details/json", params=params)
        resp.raise_for_status()
        data = resp.json()

    if data.get("status") != "OK":
        raise RuntimeError(f"Google Place Details error: {data.get('status')}")

    result = data["result"]
    loc = result.get("geometry", {}).get("location", {})
    r_lat, r_lng = loc.get("lat"), loc.get("lng")

    # Build Maps URL
    if r_lat and r_lng and user_lat and user_lng:
        url = maps_directions_url(r_lat, r_lng, result.get("name", ""), user_lat, user_lng)
    else:
        url = maps_search_url(result.get("name", ""), result.get("formatted_address", ""))

    # Parse opening hours
    hours_raw = result.get("opening_hours", {}).get("weekday_text", [])

    # Parse reviews
    reviews = [
        {
            "author": r.get("author_name", "Ẩn danh"),
            "rating": r.get("rating"),
            "text": r.get("text", ""),
            "time": r.get("relative_time_description", ""),
        }
        for r in result.get("reviews", [])[:5]
    ]

    # AI-generated menu
    ai_menu = await get_ai_menu(
        name=result.get("name", ""),
        address=result.get("formatted_address", ""),
        types=result.get("types", []),
        reviews=reviews,
    )

    return RestaurantDetail(
        place_id=place_id,
        name=result.get("name", ""),
        address=result.get("formatted_address", ""),
        phone=result.get("formatted_phone_number"),
        website=result.get("website"),
        opening_hours=hours_raw,
        reviews=reviews,
        maps_url=url,
        ai_menu=ai_menu,
    )


# ─── AI Menu Generation ───────────────────────────────────────────────────────

async def get_ai_menu(name: str, address: str, types: list, reviews: list) -> list[dict]:
    """
    Use Claude to infer likely menu items from the restaurant's name, location, and reviews.
    Returns [{ dish, description, estimated_price }, ...]
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    review_snippets = "\n".join(
        f'- {r["author"]} ({r["rating"]}⭐): {r["text"][:200]}'
        for r in reviews[:3]
    ) or "Chưa có review."

    prompt = f"""Dưới đây là thông tin về một quán ăn tại Việt Nam:
Tên: {name}
Địa chỉ: {address}
Loại hình: {', '.join(types)}
Review thực tế:
{review_snippets}

Dựa vào tên quán, địa chỉ và review, hãy suy luận ra 4–6 món ăn tiêu biểu mà quán này có thể phục vụ.
Trả về JSON hợp lệ theo đúng format sau, không thêm gì ngoài JSON:
[
  {{
    "dish": "Tên món",
    "description": "Mô tả ngắn 1 câu",
    "estimated_price": "Ví dụ: 35.000–55.000đ"
  }}
]"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        text = message.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except (json.JSONDecodeError, IndexError):
        return []
