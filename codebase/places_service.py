import httpx
import os

PLACES_API_KEY = os.getenv("PLACES_API_KEY", "YOUR_API_KEY")
NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

async def search_nearby(lat: float, lng: float, radius: int = 500, keyword: str = "restaurant"):
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "keyword": keyword,
        "key": PLACES_API_KEY,
        "language": "vi",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(NEARBY_URL, params=params)
    results = resp.json().get("results", [])
    return results

async def get_place_details(place_id: str) -> dict:
    params = {
        "place_id": place_id,
        "fields": "name,rating,opening_hours,formatted_address,user_ratings_total,photos",
        "key": PLACES_API_KEY,
        "language": "vi",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(DETAILS_URL, params=params)
    return resp.json().get("result", {})

def expand_radius_if_needed(results: list, current_radius: int) -> int:
    """Trả về bán kính mới nếu kết quả < 3"""
    if len(results) < 3 and current_radius < 5000:
        return min(current_radius * 2, 5000)
    return current_radius

def build_maps_link(lat: float, lng: float) -> str:
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"
