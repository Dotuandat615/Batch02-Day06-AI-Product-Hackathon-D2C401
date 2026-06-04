"""
ui.py — Streamlit UI components for the location module.
Handles GPS detection step and renders the location banner.
Other modules import render_location_step() to embed it in their flow.
"""

import asyncio
import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from .geocoding import reverse_geocode
from .geo_utils import maps_directions_url, maps_search_url


def render_location_step() -> dict | None:
    """
    Render the location detection UI.
    Returns a location dict when confirmed, None while still detecting.

    Returned dict shape:
    {
      "lat": float | None,
      "lng": float | None,
      "city": str,
      "province": str,
      "display_name": str,   # e.g. "Nha Trang, Khánh Hòa"
    }
    """
    st.subheader("📍 Bạn đang ở đâu?")

    # Session state keys
    if "location" not in st.session_state:
        st.session_state.location = None
    if "location_mode" not in st.session_state:
        st.session_state.location_mode = "idle"  # idle | gps | manual

    loc = st.session_state.location
    if loc:
        _render_confirmed_banner(loc)
        return loc

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📍 Xác định vị trí tự động", use_container_width=True):
            st.session_state.location_mode = "gps"
    with col2:
        if st.button("⌨️ Nhập tên thành phố", use_container_width=True):
            st.session_state.location_mode = "manual"

    if st.session_state.location_mode == "gps":
        _handle_gps_detection()

    elif st.session_state.location_mode == "manual":
        _handle_manual_input()

    return None


def _handle_gps_detection():
    """Request browser GPS via streamlit-js-eval, then reverse geocode."""
    coords = streamlit_js_eval(
        js_expressions="""new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
                p => resolve({lat: p.coords.latitude, lng: p.coords.longitude}),
                e => resolve({error: e.message}),
                {enableHighAccuracy: true, timeout: 10000}
            );
        })""",
        key="gps_coords",
    )

    if coords is None:
        st.info("⏳ Đang chờ GPS...")
        return

    if isinstance(coords, dict) and "error" in coords:
        st.error(f"⚠️ {coords['error']} — Hãy thử nhập tay.")
        st.session_state.location_mode = "manual"
        return

    if isinstance(coords, dict) and "lat" in coords:
        with st.spinner("Đang xác định tên thành phố..."):
            try:
                geo = asyncio.run(reverse_geocode(coords["lat"], coords["lng"]))
                loc = {
                    "lat": geo.lat,
                    "lng": geo.lng,
                    "city": geo.city,
                    "province": geo.province,
                    "display_name": geo.display_name,
                }
                st.session_state.location = loc
                st.session_state.location_mode = "idle"
                st.rerun()
            except Exception as e:
                st.error(f"Không thể xác định thành phố: {e}")
                st.session_state.location_mode = "manual"


def _handle_manual_input():
    with st.form("manual_city_form"):
        city = st.text_input("Nhập tên thành phố / tỉnh", placeholder="Ví dụ: Nha Trang, Đà Lạt, Hội An")
        submitted = st.form_submit_button("Xác nhận")
        if submitted and city.strip():
            loc = {
                "lat": None, "lng": None,
                "city": city.strip(),
                "province": city.strip(),
                "display_name": city.strip(),
            }
            st.session_state.location = loc
            st.session_state.location_mode = "idle"
            st.rerun()


def _render_confirmed_banner(loc: dict):
    st.success(f"📍 Bạn đang ở **{loc['display_name']}**")
    if st.button("Đổi vị trí", key="change_location"):
        st.session_state.location = None
        st.session_state.location_mode = "idle"
        st.rerun()


# ─── Reusable Maps link renderer ──────────────────────────────────────────────

def render_maps_button(restaurant_name: str, dest_lat: float, dest_lng: float,
                       user_lat: float = None, user_lng: float = None, city: str = ""):
    """
    Render a styled Google Maps button for a restaurant.
    Called by the recommendation module after it displays each restaurant card.
    """
    if dest_lat and dest_lng:
        url = maps_directions_url(dest_lat, dest_lng, restaurant_name, user_lat, user_lng)
    else:
        url = maps_search_url(restaurant_name, city)

    st.markdown(
        f'<a href="{url}" target="_blank">'
        f'<button style="background:#4285F4;color:white;border:none;padding:8px 16px;'
        f'border-radius:8px;cursor:pointer;font-size:14px;">🗺️ Xem trên Google Maps</button>'
        f"</a>",
        unsafe_allow_html=True,
    )
