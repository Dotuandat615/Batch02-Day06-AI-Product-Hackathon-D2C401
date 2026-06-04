"""
Location module — public API.
Other modules import from here, not from submodules directly.
"""

from .geocoding import reverse_geocode, GeoAddress
from .places import get_nearby_restaurants, get_restaurant_detail, get_ai_menu, Restaurant, RestaurantDetail
from .geo_utils import haversine_distance, format_distance, estimate_walk_time, maps_directions_url
from .ui import render_location_step, render_maps_button

__all__ = [
    # Geocoding
    "reverse_geocode",
    "GeoAddress",
    # Places
    "get_nearby_restaurants",
    "get_restaurant_detail",
    "get_ai_menu",
    "Restaurant",
    "RestaurantDetail",
    # Geo math
    "haversine_distance",
    "format_distance",
    "estimate_walk_time",
    "maps_directions_url",
    # Streamlit UI
    "render_location_step",
    "render_maps_button",
]
