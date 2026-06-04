/**
 * locationService.test.js
 * Unit tests for pure functions (no network, no browser APIs).
 * Run with: node locationService.test.js
 */

import {
  haversineDistance,
  formatDistance,
  estimateWalkTime,
  buildGoogleMapsDirectionsUrl,
  buildGoogleMapsSearchUrl,
  enrichRestaurantsWithLocation,
} from "./locationService.js";

let passed = 0;
let failed = 0;

function assert(label, condition) {
  if (condition) {
    console.log(`  ✅ ${label}`);
    passed++;
  } else {
    console.error(`  ❌ ${label}`);
    failed++;
  }
}

function assertApprox(label, actual, expected, tolerance = 0.01) {
  const ok = Math.abs(actual - expected) <= tolerance * expected;
  assert(`${label} (got ${actual.toFixed(1)}, expected ~${expected})`, ok);
}

console.log("\n--- haversineDistance ---");
// Hanoi HN → HCMC: ~1730km
const hanoiHCMC = haversineDistance(21.0285, 105.8542, 10.8231, 106.6297);
assertApprox("Hanoi→HCMC ~1730km", hanoiHCMC / 1000, 1730, 0.05);

// Same point → 0
assert("Same point = 0m", haversineDistance(10, 106, 10, 106) === 0);

// ~350m test (Nha Trang area)
const short = haversineDistance(12.2451, 109.1943, 12.2482, 109.1943);
assertApprox("~350m segment", short, 345, 0.1);

console.log("\n--- formatDistance ---");
assert("0m", formatDistance(0) === "0m");
assert("350m", formatDistance(350) === "350m");
assert("999m", formatDistance(999) === "999m");
assert("1.0km", formatDistance(1000) === "1.0km");
assert("1.1km", formatDistance(1100) === "1.1km");
assert("5.5km", formatDistance(5500) === "5.5km");

console.log("\n--- estimateWalkTime ---");
assert("<2min → ~1 phút", estimateWalkTime(50) === "~1 phút đi bộ");
assert("350m → ~4 phút", estimateWalkTime(350) === "~4 phút đi bộ");
assert("600m → ~7 phút", estimateWalkTime(600) === "~7 phút đi bộ");

console.log("\n--- buildGoogleMapsDirectionsUrl ---");
const urlWithOrigin = buildGoogleMapsDirectionsUrl(12.25, 109.20, "Bún cá Bà Bảy", 12.24, 109.19);
assert("With origin contains /dir/", urlWithOrigin.includes("/maps/dir/"));
assert("With origin contains dest coords", urlWithOrigin.includes("12.25,109.2"));

const urlNoOrigin = buildGoogleMapsDirectionsUrl(12.25, 109.20, "Bún cá Bà Bảy");
assert("No origin uses /maps/search/", urlNoOrigin.includes("/maps/search/"));

console.log("\n--- buildGoogleMapsSearchUrl ---");
const searchUrl = buildGoogleMapsSearchUrl("Bánh căn Mỹ Hòa", "Nha Trang");
assert("Search URL is string", typeof searchUrl === "string");
assert("Contains maps domain", searchUrl.includes("google.com/maps"));

console.log("\n--- enrichRestaurantsWithLocation ---");
const userLoc = { lat: 12.2451, lng: 109.1943, city: "Nha Trang", displayName: "Nha Trang, Khánh Hòa" };
const restaurants = [
  { name: "Bún cá Bà Bảy", lat: 12.2482, lng: 109.1943 },
  { name: "Bánh căn Mỹ Hòa", lat: null, lng: null },
];

const enriched = enrichRestaurantsWithLocation(restaurants, userLoc);

assert("Enriched count matches", enriched.length === 2);
assert("First has distanceText", typeof enriched[0].distanceText === "string");
assert("First has mapsUrl with /dir/", enriched[0].mapsUrl.includes("/dir/"));
assert("Second (no coords) fallback search URL", enriched[1].mapsUrl.includes("/maps/search/"));
assert("Second distanceMetres is null", enriched[1].distanceMetres === null);

console.log(`\n=== Results: ${passed} passed, ${failed} failed ===\n`);
if (failed > 0) process.exit(1);
