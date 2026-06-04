import { useState } from "react";
import { getLocationWithName } from "../services/locationService.js";

/**
 * LocationDetector
 * Renders the "Bạn đang ở..." banner.
 * States: idle → loading → success | error | manual
 *
 * Props:
 *   onLocationReady(locationObj) — called when location is confirmed
 */
export default function LocationDetector({ onLocationReady }) {
  const [status, setStatus] = useState("idle"); // idle | loading | success | error | manual
  const [location, setLocation] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [manualCity, setManualCity] = useState("");

  async function handleDetect() {
    setStatus("loading");
    setErrorMsg("");
    try {
      const loc = await getLocationWithName();
      setLocation(loc);
      setStatus("success");
      onLocationReady(loc);
    } catch (err) {
      setErrorMsg(err.message);
      setStatus("error");
    }
  }

  function handleManualSubmit(e) {
    e.preventDefault();
    const trimmed = manualCity.trim();
    if (!trimmed) return;
    const loc = {
      lat: null,
      lng: null,
      city: trimmed,
      province: trimmed,
      displayName: trimmed,
    };
    setLocation(loc);
    setStatus("success");
    onLocationReady(loc);
  }

  return (
    <div className="location-detector">
      {status === "idle" && (
        <div className="location-prompt">
          <p className="location-subtitle">Để gợi ý quán ăn gần bạn nhất</p>
          <button className="btn-primary btn-location" onClick={handleDetect}>
            📍 Xác định vị trí tự động
          </button>
          <button
            className="btn-ghost"
            onClick={() => setStatus("manual")}
          >
            Nhập tên thành phố thủ công
          </button>
        </div>
      )}

      {status === "loading" && (
        <div className="location-loading">
          <div className="spinner" />
          <p>Đang xác định vị trí…</p>
        </div>
      )}

      {status === "success" && location && (
        <div className="location-success">
          <span className="location-pin">📍</span>
          <div>
            <p className="location-label">Bạn đang ở</p>
            <p className="location-name">{location.displayName}</p>
          </div>
          <button
            className="btn-ghost btn-small"
            onClick={() => {
              setStatus("idle");
              setLocation(null);
            }}
          >
            Đổi
          </button>
        </div>
      )}

      {status === "error" && (
        <div className="location-error">
          <p className="error-msg">⚠️ {errorMsg}</p>
          <button className="btn-primary btn-small" onClick={handleDetect}>
            Thử lại
          </button>
          <button
            className="btn-ghost btn-small"
            onClick={() => setStatus("manual")}
          >
            Nhập tay
          </button>
        </div>
      )}

      {status === "manual" && (
        <form className="location-manual" onSubmit={handleManualSubmit}>
          <input
            type="text"
            className="input-city"
            placeholder="Ví dụ: Nha Trang, Đà Lạt, Hội An…"
            value={manualCity}
            onChange={(e) => setManualCity(e.target.value)}
            autoFocus
          />
          <button className="btn-primary btn-small" type="submit">
            Xác nhận
          </button>
          <button
            className="btn-ghost btn-small"
            type="button"
            onClick={() => setStatus("idle")}
          >
            Huỷ
          </button>
        </form>
      )}
    </div>
  );
}
