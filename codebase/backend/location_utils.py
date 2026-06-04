"""
location_utils.py
Backend helpers for location: reverse geocoding via Nominatim, distance, Maps URLs.
Mirrors the logic in frontend/src/services/locationService.js for server-side use.
"""

import math
import urllib.parse
import httpx
from typing import Optional

NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
USER_AGENT = "AI-Local-Guide-Hackathon/1.0 (phanhieupkkq@gmail.com)"


async def reverse_geocode(lat: float, lng: float) -> dict:
    """
    Reverse geocode lat/lng → city/province using Nominatim (free, no API key).
    Returns dict: { city, province, display_name, country_code, raw_address }
    Nominatim policy: max 1 req/sec.
    """
    url = f"{NOMINATIM_BASE}/reverse"
    params = {"lat": lat, "lon": lng, "format": "json", "accept-language": "vi"}

    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.get(url, params=params, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        data = resp.json()

    addr = data.get("address", {})

    city = (
        addr.get("city")
        or addr.get("town")
        or addr.get("village")
        or addr.get("county")
        or addr.get("state_district")
        or addr.get("state")
        or "Không xác định"
    )
    province = addr.get("state") or addr.get("province") or city
    display_name = f"{city}, {province}" if city != province and province else city

    return {
        "city": city,
        "province": province,
        "display_name": display_name,
        "country_code": (addr.get("country_code") or "vn").upper(),
        "raw_address": data.get("display_name", ""),
    }


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Straight-line distance in metres between two GPS points (Haversine)."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def format_distance(metres: float) -> str:
    if metres < 1000:
        return f"{round(metres)}m"
    return f"{metres / 1000:.1f}km"


def estimate_walk_time(metres: float) -> str:
    minutes = round(metres / 83)  # 5km/h avg
    return "~1 phút đi bộ" if minutes < 2 else f"~{minutes} phút đi bộ"


def build_maps_directions_url(
    dest_lat: float,
    dest_lng: float,
    dest_name: str,
    origin_lat: Optional[float] = None,
    origin_lng: Optional[float] = None,
) -> str:
    """Google Maps directions deep link. No API key needed."""
    dest = f"{dest_lat},{dest_lng}"
    if origin_lat is not None and origin_lng is not None:
        origin = f"{origin_lat},{origin_lng}"
        return f"https://www.google.com/maps/dir/{origin}/{dest}"
    label = urllib.parse.quote(dest_name)
    return f"https://www.google.com/maps/search/?api=1&query={dest}&query_place_id={label}"


def build_maps_search_url(restaurant_name: str, city: str) -> str:
    query = urllib.parse.quote(f"{restaurant_name} {city}")
    return f"https://www.google.com/maps/search/{query}"


def enrich_restaurant(
    restaurant: dict,
    user_lat: Optional[float],
    user_lng: Optional[float],
    city: str,
) -> dict:
    """Add distance, walk time, and Maps URL to a restaurant dict."""
    r_lat = restaurant.get("lat")
    r_lng = restaurant.get("lng")

    if r_lat and r_lng and user_lat and user_lng:
        metres = haversine_distance(user_lat, user_lng, r_lat, r_lng)
        maps_url = build_maps_directions_url(r_lat, r_lng, restaurant["name"], user_lat, user_lng)
        return {
            **restaurant,
            "distance_metres": round(metres),
            "distance_text": format_distance(metres),
            "walk_time": estimate_walk_time(metres),
            "maps_url": maps_url,
        }

    return {
        **restaurant,
        "distance_metres": None,
        "distance_text": "Không rõ",
        "walk_time": None,
        "maps_url": build_maps_search_url(restaurant["name"], city),
    }
