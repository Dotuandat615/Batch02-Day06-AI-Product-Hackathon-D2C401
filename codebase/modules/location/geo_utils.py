"""Pure math helpers — no external dependencies."""

import math
import urllib.parse


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Straight-line distance in metres between two GPS points."""
    R = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def fmt_distance(metres: float) -> str:
    """350 → '350m', 1200 → '1.2km'"""
    if metres < 1000:
        return f"{round(metres)}m"
    return f"{metres / 1000:.1f}km"


def maps_url(dest_lat: float, dest_lng: float, dest_name: str,
             origin_lat: float = None, origin_lng: float = None) -> str:
    """Google Maps deep link — no API key needed."""
    dest = f"{dest_lat},{dest_lng}"
    if origin_lat is not None and origin_lng is not None:
        return f"https://www.google.com/maps/dir/{origin_lat},{origin_lng}/{dest}"
    q = urllib.parse.quote(dest_name)
    return f"https://www.google.com/maps/search/?api=1&query={dest}&query_place_id={q}"
