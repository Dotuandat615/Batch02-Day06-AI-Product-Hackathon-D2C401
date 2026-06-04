from __future__ import annotations

import math
from typing import Any

from pydantic import BaseModel, Field, model_validator


class RecommendationItem(BaseModel):
    """Một quán gợi ý từ LLM.

    Chấp nhận cả hai dạng toạ độ:
    - flat: {"lat": 10.7, "lng": 106.6, ...}
    - nested: {"geometry": {"location": {"lat": 10.7, "lng": 106.6}}, ...}
    model_validator sẽ resolve về lat/lng flat sau khi parse.
    """
    place_id: str = ""
    name: str = "Không rõ"
    vicinity: str = ""
    rating: float | None = None
    reason: str = ""
    confidence: str = "high"
    geometry: dict[str, Any] = Field(default_factory=dict)
    warning: str | None = None
    thumbnail: str | None = None
    lat: float = 0.0
    lng: float = 0.0

    @model_validator(mode="after")
    def resolve_coordinates(self) -> "RecommendationItem":
        """Nếu lat/lng = 0, thử lấy từ geometry.location."""
        if self.lat == 0.0 and self.lng == 0.0:
            loc = self.geometry.get("location", {})
            self.lat = float(loc.get("lat", 0.0))
            self.lng = float(loc.get("lng", 0.0))
        return self


class FormatInput(BaseModel):
    recommendations: list[RecommendationItem] = Field(default_factory=list)
    user_lat: float = 0.0
    user_lng: float = 0.0


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _maps_link(lat: float, lng: float) -> str:
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"


def _distance_text(meters: float) -> str:
    if meters < 1000:
        return f"{int(meters)}m"
    return f"{meters / 1000:.1f}km"


def _walk_time(meters: float) -> str:
    minutes = int(meters / 80)
    if minutes < 1:
        return "dưới 1 phút"
    return f"~{minutes} phút"


def format_recs(**kwargs) -> dict[str, Any]:
    """Format danh sách quán gợi ý thành output cho user.

    Kwargs (validated by FormatInput):
        recommendations: list quán gợi ý (tối đa 3), mỗi item có thể dùng
                         flat lat/lng hoặc nested geometry.location.lat/lng
        user_lat: vĩ độ người dùng
        user_lng: kinh độ người dùng

    Returns:
        dict với "formatted_text" và "cards" cho UI render.
    """
    inp = FormatInput(**kwargs)

    if not inp.recommendations:
        return {
            "tool": "format_recommendations",
            "formatted_text": "Không có quán nào để hiển thị.",
            "cards": [],
        }

    cards: list[dict[str, Any]] = []
    lines: list[str] = []

    for rank, rec in enumerate(inp.recommendations[:3], 1):
        dist = (
            _haversine_m(inp.user_lat, inp.user_lng, rec.lat, rec.lng)
            if (inp.user_lat and inp.user_lng)
            else 0
        )

        card = {
            "rank": rank,
            "name": rec.name,
            "address": rec.vicinity,
            "rating": rec.rating,
            "distance": _distance_text(dist),
            "walk_time": _walk_time(dist),
            "reason": rec.reason,
            "confidence": rec.confidence,
            "maps_link": _maps_link(rec.lat, rec.lng),
            "warning": rec.warning,
            "thumbnail": rec.thumbnail,
        }
        cards.append(card)

        emoji_rank = ["①", "②", "③"][rank - 1]
        confidence_badge = ""
        if rec.confidence == "low":
            confidence_badge = " ⚠️ Review cũ/ít"
        elif rec.confidence == "medium":
            confidence_badge = " ℹ️ Cần xác nhận"

        line = (
            f"{emoji_rank} **{card['name']}**{confidence_badge}\n"
            f"📍 {card['address']}, cách bạn {card['distance']} — đi bộ {card['walk_time']}\n"
            f"⭐ {card['rating'] or '?'}\n"
            f"💡 *{card['reason']}*"
        )
        if card["warning"]:
            line += f"\n⚠️ *{card['warning']}*"
        lines.append(line)

    formatted = "\n\n".join(lines)
    formatted += "\n\n> ⚠️ *Giờ mở cửa có thể thay đổi. Nhấn tên quán để kiểm tra trên Google Maps trước khi xuất phát.*"

    return {
        "tool": "format_recommendations",
        "formatted_text": formatted,
        "cards": cards,
    }
