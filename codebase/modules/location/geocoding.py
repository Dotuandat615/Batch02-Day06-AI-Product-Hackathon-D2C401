"""
geocoding.py — Reverse geocoding: (lat, lng) → city/province name.
Uses Google Geocoding API. Falls back to Nominatim (OSM) if no Google key.
"""

import os
import httpx
from dataclasses import dataclass


@dataclass
class GeoAddress:
    city: str
    province: str
    display_name: str       # e.g. "Nha Trang, Khánh Hòa"
    country_code: str       # "VN"
    lat: float
    lng: float


async def reverse_geocode(lat: float, lng: float) -> GeoAddress:
    """
    Convert GPS coordinates to a GeoAddress.
    Tries Google Geocoding API first (best quality for Vietnam).
    Falls back to Nominatim (OSM) if GOOGLE_MAPS_API_KEY is not set.
    """
    google_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if google_key:
        return await _google_reverse_geocode(lat, lng, google_key)
    return await _nominatim_reverse_geocode(lat, lng)


async def _google_reverse_geocode(lat: float, lng: float, api_key: str) -> GeoAddress:
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "latlng": f"{lat},{lng}",
        "language": "vi",
        "result_type": "locality|administrative_area_level_1",
        "key": api_key,
    }
    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    if data.get("status") != "OK" or not data.get("results"):
        raise ValueError(f"Google Geocoding API error: {data.get('status')}")

    # Parse address components from the first result
    city = province = ""
    for component in data["results"][0].get("address_components", []):
        types = component.get("types", [])
        if "locality" in types or "sublocality" in types:
            city = component["long_name"]
        if "administrative_area_level_1" in types:
            province = component["long_name"]

    city = city or province or "Không xác định"
    display_name = f"{city}, {province}" if city != province and province else city

    return GeoAddress(
        city=city,
        province=province,
        display_name=display_name,
        country_code="VN",
        lat=lat,
        lng=lng,
    )


async def _nominatim_reverse_geocode(lat: float, lng: float) -> GeoAddress:
    """Free fallback: Nominatim (OpenStreetMap). No API key, max 1 req/sec."""
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {"lat": lat, "lon": lng, "format": "json", "accept-language": "vi"}
    headers = {"User-Agent": "AI-Local-Guide-Hackathon/1.0"}

    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    addr = data.get("address", {})
    city = (
        addr.get("city") or addr.get("town") or addr.get("village")
        or addr.get("county") or addr.get("state_district")
        or addr.get("state") or "Không xác định"
    )
    province = addr.get("state") or addr.get("province") or city
    display_name = f"{city}, {province}" if city != province and province else city

    return GeoAddress(
        city=city,
        province=province,
        display_name=display_name,
        country_code=(addr.get("country_code") or "vn").upper(),
        lat=lat,
        lng=lng,
    )
