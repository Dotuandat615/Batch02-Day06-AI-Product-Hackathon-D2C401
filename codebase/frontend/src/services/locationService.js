/**
 * locationService.js
 * Handles: GPS acquisition, reverse geocoding (Nominatim OSM), distance calculation, Google Maps links.
 * No API keys required — uses free public APIs and browser APIs only.
 */

const NOMINATIM_BASE = "https://nominatim.openstreetmap.org";

/**
 * Step 1: Get user's GPS coordinates via Browser Geolocation API.
 * Returns { lat, lng } or throws with a user-friendly message.
 */
export async function getUserLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Trình duyệt không hỗ trợ định vị GPS. Vui lòng nhập tên thành phố thủ công."));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy: position.coords.accuracy, // metres
        });
      },
      (error) => {
        const messages = {
          1: "Bạn đã từ chối quyền truy cập vị trí. Vui lòng cho phép trong cài đặt trình duyệt.",
          2: "Không thể xác định vị trí. Hãy kiểm tra kết nối mạng hoặc GPS.",
          3: "Hết thời gian chờ xác định vị trí. Thử lại sau.",
        };
        reject(new Error(messages[error.code] || "Lỗi không xác định khi lấy vị trí."));
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000, // cache 1 minute
      }
    );
  });
}

/**
 * Step 2: Reverse geocode lat/lng → human-readable location string.
 * Uses Nominatim (OpenStreetMap) — free, no API key.
 * Returns { city, district, province, displayName, countryCode }
 *
 * Nominatim usage policy: 1 req/sec, User-Agent required.
 */
export async function reverseGeocode(lat, lng) {
  const url = `${NOMINATIM_BASE}/reverse?lat=${lat}&lon=${lng}&format=json&accept-language=vi`;

  const response = await fetch(url, {
    headers: {
      "User-Agent": "AI-Local-Guide-Hackathon/1.0 (phanhieupkkq@gmail.com)",
    },
  });

  if (!response.ok) {
    throw new Error("Không thể xác định tên thành phố. Kiểm tra kết nối mạng.");
  }

  const data = await response.json();
  const addr = data.address || {};

  // Nominatim Vietnamese address fields vary by region.
  // Priority order for "city" concept in Vietnam:
  const city =
    addr.city ||
    addr.town ||
    addr.village ||
    addr.county ||
    addr.state_district ||
    addr.state ||
    "Không xác định";

  const province = addr.state || addr.province || city;

  // Build short display like "Nha Trang, Khánh Hòa"
  const displayName =
    city !== province && province ? `${city}, ${province}` : city;

  return {
    city,
    province,
    displayName,
    countryCode: addr.country_code?.toUpperCase() || "VN",
    rawAddress: data.display_name,
  };
}

/**
 * Convenience: get location + reverse geocode in one call.
 * Returns { lat, lng, accuracy, city, province, displayName }
 */
export async function getLocationWithName() {
  const coords = await getUserLocation();
  const geo = await reverseGeocode(coords.lat, coords.lng);
  return { ...coords, ...geo };
}

/**
 * Step 3a: Calculate straight-line distance between two lat/lng points.
 * Uses Haversine formula. Returns distance in metres.
 */
export function haversineDistance(lat1, lng1, lat2, lng2) {
  const R = 6371000; // Earth radius in metres
  const toRad = (deg) => (deg * Math.PI) / 180;

  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;

  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/**
 * Human-readable distance string, e.g. "350m" or "1.2km".
 */
export function formatDistance(metres) {
  if (metres < 1000) return `${Math.round(metres)}m`;
  return `${(metres / 1000).toFixed(1)}km`;
}

/**
 * Rough walking time estimate (avg 5km/h = 83m/min).
 * Returns string like "~5 phút đi bộ".
 */
export function estimateWalkTime(metres) {
  const minutes = Math.round(metres / 83);
  if (minutes < 2) return "~1 phút đi bộ";
  return `~${minutes} phút đi bộ`;
}

/**
 * Step 3b: Build a Google Maps directions deep link.
 * Opens the native Maps app on mobile, Maps in browser on desktop.
 * No API key required.
 *
 * @param {number} destLat - Restaurant latitude
 * @param {number} destLng - Restaurant longitude
 * @param {string} destName - Restaurant name (for the pin label)
 * @param {number|null} originLat - User latitude (null = Maps uses current location)
 * @param {number|null} originLng - User longitude
 */
export function buildGoogleMapsDirectionsUrl(
  destLat,
  destLng,
  destName,
  originLat = null,
  originLng = null
) {
  const dest = `${destLat},${destLng}`;
  const label = encodeURIComponent(destName);

  if (originLat !== null && originLng !== null) {
    const origin = `${originLat},${originLng}`;
    return `https://www.google.com/maps/dir/${origin}/${dest}`;
  }

  // Without origin — Maps will ask user for their location
  return `https://www.google.com/maps/search/?api=1&query=${dest}&query_place_id=${label}`;
}

/**
 * Build a Google Maps search link by restaurant name + city (fallback when no lat/lng).
 */
export function buildGoogleMapsSearchUrl(restaurantName, city) {
  const query = encodeURIComponent(`${restaurantName} ${city}`);
  return `https://www.google.com/maps/search/${query}`;
}

/**
 * Attach distance + walk time + maps URL to each restaurant object.
 * Expects restaurant to have { lat, lng, name } fields.
 * userLocation: { lat, lng, displayName }
 */
export function enrichRestaurantsWithLocation(restaurants, userLocation) {
  return restaurants.map((r) => {
    if (r.lat && r.lng) {
      const metres = haversineDistance(
        userLocation.lat,
        userLocation.lng,
        r.lat,
        r.lng
      );
      return {
        ...r,
        distanceMetres: metres,
        distanceText: formatDistance(metres),
        walkTime: estimateWalkTime(metres),
        mapsUrl: buildGoogleMapsDirectionsUrl(
          r.lat,
          r.lng,
          r.name,
          userLocation.lat,
          userLocation.lng
        ),
      };
    }

    // No coordinates — fallback to name search
    return {
      ...r,
      distanceMetres: null,
      distanceText: "Không rõ",
      walkTime: null,
      mapsUrl: buildGoogleMapsSearchUrl(r.name, userLocation.city),
    };
  });
}
