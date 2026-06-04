from __future__ import annotations

import math
from typing import Any


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Khoảng cách giữa 2 tọa độ (mét), công thức Haversine."""
    R = 6_371_000  # bán kính Trái Đất (m)
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
    minutes = int(meters / 80)  # ~80m/phút đi bộ
    if minutes < 1:
        return "dưới 1 phút"
    return f"~{minutes} phút"


def format_recs(
    recommendations: list[dict[str, Any]] | None = None,
    user_lat: float = 0.0,
    user_lng: float = 0.0,
) -> dict[str, Any]:
    """Format danh sách quán gợi ý thành output cho user.

    Args:
        recommendations: Danh sách quán (từ AI engine), mỗi item có:
            name, place_id, rating, vicinity, reason, confidence,
            geometry.location.lat/lng
        user_lat: Vĩ độ người dùng.
        user_lng: Kinh độ người dùng.

    Returns:
        dict với "formatted_text" và "cards" cho UI render.
    """
    if not recommendations:
        return {
            "tool": "format_recommendations",
            "formatted_text": "Không có quán nào để hiển thị.",
            "cards": [],
        }

    cards: list[dict[str, Any]] = []
    lines: list[str] = []

    for rank, rec in enumerate(recommendations[:3], 1):
        loc = rec.get("geometry", {}).get("location", {})
        lat = loc.get("lat", 0)
        lng = loc.get("lng", 0)
        dist = _haversine_m(user_lat, user_lng, lat, lng) if (user_lat and user_lng) else 0

        card = {
            "rank": rank,
            "name": rec.get("name", "Không rõ"),
            "address": rec.get("vicinity", ""),
            "rating": rec.get("rating"),
            "distance": _distance_text(dist),
            "walk_time": _walk_time(dist),
            "reason": rec.get("reason", ""),
            "confidence": rec.get("confidence", "high"),
            "maps_link": _maps_link(lat, lng),
            "warning": rec.get("warning"),
            "thumbnail": rec.get("thumbnail"),
        }
        cards.append(card)

        # Text format
        emoji_rank = ["①", "②", "③"][rank - 1]
        confidence_badge = ""
        if card["confidence"] == "low":
            confidence_badge = " ⚠️ Review cũ/ít"
        elif card["confidence"] == "medium":
            confidence_badge = " ℹ️ Cần xác nhận"

        line = (
            f"{emoji_rank} **{card['name']}**{confidence_badge}\n"
            f"📍 {card['address']}, cách bạn {card['distance']} — đi bộ {card['walk_time']}\n"
            f"🗺️ Google Maps: {card['maps_link']}\n"
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
