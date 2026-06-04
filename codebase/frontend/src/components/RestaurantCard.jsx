/**
 * RestaurantCard
 * Displays one restaurant recommendation from AI.
 * Handles the "open Google Maps" action — the ONLY action user takes after AI suggests.
 *
 * Props:
 *   restaurant: {
 *     rank: number,
 *     name: string,
 *     address: string,
 *     rating: string,       // e.g. "4.6"
 *     reviewSnippet: string,
 *     reason: string,       // AI's match reason
 *     distanceText: string, // "350m"
 *     walkTime: string,     // "~5 phút đi bộ"
 *     mapsUrl: string,
 *     confidence: "high" | "medium" | "low",
 *     warning: string | null,
 *   }
 *   onSelect(restaurant) — called when user taps the card
 */
export default function RestaurantCard({ restaurant, onSelect }) {
  const {
    rank,
    name,
    address,
    rating,
    reviewSnippet,
    reason,
    distanceText,
    walkTime,
    mapsUrl,
    confidence,
    warning,
  } = restaurant;

  const rankEmojis = ["①", "②", "③"];
  const confidenceBadge = {
    high: null,
    medium: { label: "Độ tin cậy trung bình", className: "badge-medium" },
    low: { label: "Dữ liệu hạn chế", className: "badge-low" },
  }[confidence];

  function handleOpenMaps(e) {
    e.stopPropagation();
    window.open(mapsUrl, "_blank", "noopener,noreferrer");
  }

  return (
    <div
      className={`restaurant-card confidence-${confidence}`}
      onClick={() => onSelect(restaurant)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onSelect(restaurant)}
    >
      <div className="card-header">
        <span className="rank-badge">{rankEmojis[rank - 1] || rank}</span>
        <div className="card-title-block">
          <h3 className="restaurant-name">{name}</h3>
          {confidenceBadge && (
            <span className={`confidence-badge ${confidenceBadge.className}`}>
              {confidenceBadge.label}
            </span>
          )}
        </div>
      </div>

      <div className="card-body">
        <p className="restaurant-address">
          📍 {address}
          {distanceText && (
            <span className="distance">
              {" "}— cách bạn {distanceText}
              {walkTime && `, ${walkTime}`}
            </span>
          )}
        </p>

        {rating && (
          <p className="restaurant-rating">
            ⭐ {rating}
            {reviewSnippet && (
              <span className="review-snippet"> · "{reviewSnippet}"</span>
            )}
          </p>
        )}

        <p className="restaurant-reason">
          💡 <em>{reason}</em>
        </p>

        {warning && (
          <p className="restaurant-warning">
            ⚠️ {warning}
          </p>
        )}
      </div>

      <div className="card-footer">
        <button
          className="btn-maps"
          onClick={handleOpenMaps}
          aria-label={`Mở Google Maps chỉ đường đến ${name}`}
        >
          🗺️ Xem trên Google Maps
        </button>
      </div>
    </div>
  );
}
