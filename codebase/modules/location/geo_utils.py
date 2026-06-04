"""
geo_utils.py — Pure math helpers. No external dependencies, fully testable.
"""

import math


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Straight-line distance in metres between two GPS points."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def format_distance(metres: float) -> str:
    """'350m' or '1.2km'."""
    if metres < 1000:
        return f"{round(metres)}m"
    return f"{metres / 1000:.1f}km"


def estimate_walk_time(metres: float) -> str:
    """Rough walking estimate at 5 km/h."""
    minutes = round(metres / 83)
    return "~1 phút đi bộ" if minutes < 2 else f"~{minutes} phút đi bộ"


def maps_directions_url(dest_lat: float, dest_lng: float, dest_name: str,
                        origin_lat: float = None, origin_lng: float = None) -> str:
    """Google Maps directions deep link. No API key required."""
    import urllib.parse
    dest = f"{dest_lat},{dest_lng}"
    if origin_lat is not None and origin_lng is not None:
        return f"https://www.google.com/maps/dir/{origin_lat},{origin_lng}/{dest}"
    label = urllib.parse.quote(dest_name)
    return f"https://www.google.com/maps/search/?api=1&query={dest}&query_place_id={label}"


def maps_search_url(name: str, city: str) -> str:
    import urllib.parse
    return f"https://www.google.com/maps/search/{urllib.parse.quote(name + ' ' + city)}"
