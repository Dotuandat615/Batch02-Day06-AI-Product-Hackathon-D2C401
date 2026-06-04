"""
gps.py — Lấy GPS thật từ browser qua Streamlit.

Dùng streamlit-js-eval để chạy navigator.geolocation trong browser,
trả về lat/lng thật của thiết bị người dùng.

Cách dùng trong app Streamlit:
    from modules.location.gps import get_gps_from_browser

    coords = get_gps_from_browser()   # None nếu chưa có kết quả
    if coords:
        print(coords["lat"], coords["lng"], coords["accuracy"])
"""

from typing import Optional


def get_gps_from_browser() -> Optional[dict]:
    """
    Gọi browser GPS qua JavaScript, trả về dict hoặc None.

    Trả về:
        {"lat": float, "lng": float, "accuracy": float}  — khi có vị trí
        {"error": str}                                    — khi bị từ chối / lỗi
        None                                              — đang chờ (chưa có kết quả)

    Chỉ dùng được trong Streamlit app (cần browser context).
    Không dùng được trong script Python thuần.
    """
    try:
        from streamlit_js_eval import streamlit_js_eval
    except ImportError:
        raise ImportError(
            "Cần cài streamlit-js-eval: pip install streamlit-js-eval"
        )

    result = streamlit_js_eval(
        js_expressions="""
            new Promise((resolve) => {
                if (!navigator.geolocation) {
                    resolve({ error: "Trình duyệt không hỗ trợ GPS" });
                    return;
                }
                navigator.geolocation.getCurrentPosition(
                    (pos) => resolve({
                        lat:      pos.coords.latitude,
                        lng:      pos.coords.longitude,
                        accuracy: pos.coords.accuracy
                    }),
                    (err) => {
                        const msg = {
                            1: "Người dùng từ chối quyền truy cập vị trí",
                            2: "Không thể xác định vị trí (kiểm tra GPS)",
                            3: "Hết thời gian chờ GPS",
                        };
                        resolve({ error: msg[err.code] || err.message });
                    },
                    { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
                );
            })
        """,
        key="browser_gps",
    )
    return result  # None = đang chờ, dict = có kết quả


def render_location_picker(on_location_ready) -> None:
    """
    Streamlit UI component để người dùng chọn cách cung cấp vị trí.

    Luồng:
      1. Bấm "Dùng GPS" → browser hỏi quyền → lấy lat/lng thật
      2. Hoặc nhập tay tên thành phố (fallback khi không có GPS)

    Khi có vị trí, gọi on_location_ready({"lat": ..., "lng": ..., "city": ...})
    """
    import streamlit as st

    if "gps_mode" not in st.session_state:
        st.session_state.gps_mode = "idle"
    if "confirmed_location" not in st.session_state:
        st.session_state.confirmed_location = None

    # Đã có vị trí — hiển thị banner
    if st.session_state.confirmed_location:
        loc = st.session_state.confirmed_location
        label = loc.get("city") or f"{loc['lat']:.4f}, {loc['lng']:.4f}"
        st.success(f"📍 {label}")
        if st.button("Đổi vị trí", key="change_loc"):
            st.session_state.confirmed_location = None
            st.session_state.gps_mode = "idle"
            st.rerun()
        on_location_ready(loc)
        return

    # Chọn phương thức
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📍 Dùng GPS của thiết bị", use_container_width=True):
            st.session_state.gps_mode = "gps"
            st.rerun()
    with col2:
        if st.button("⌨️ Nhập tên thành phố", use_container_width=True):
            st.session_state.gps_mode = "manual"
            st.rerun()

    # Lấy GPS từ browser
    if st.session_state.gps_mode == "gps":
        st.info("⏳ Đang chờ trình duyệt lấy vị trí GPS…")
        result = get_gps_from_browser()

        if result is None:
            return  # Streamlit tự rerun khi có kết quả

        if "error" in result:
            st.error(f"⚠️ {result['error']}")
            st.session_state.gps_mode = "idle"
            return

        # Có lat/lng thật
        loc = {
            "lat":      result["lat"],
            "lng":      result["lng"],
            "accuracy": result.get("accuracy"),
            "city":     None,   # module location sẽ reverse-geocode
            "source":   "gps",
        }
        st.session_state.confirmed_location = loc
        st.rerun()

    # Nhập tay
    elif st.session_state.gps_mode == "manual":
        with st.form("manual_city"):
            city = st.text_input("Tên thành phố / tỉnh",
                                 placeholder="Nha Trang, Đà Lạt, Hội An…")
            if st.form_submit_button("Xác nhận") and city.strip():
                loc = {"lat": None, "lng": None,
                       "city": city.strip(), "source": "manual"}
                st.session_state.confirmed_location = loc
                st.rerun()
        if st.button("← Quay lại", key="back"):
            st.session_state.gps_mode = "idle"
            st.rerun()
