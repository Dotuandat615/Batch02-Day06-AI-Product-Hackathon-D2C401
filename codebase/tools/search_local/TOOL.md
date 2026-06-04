---
name: search_local
kind: live_api
provider: SerpAPI (google_maps engine)
requires_env: [MAP_API, MAP_ENDPOINT]
inputs: [query, lat, lng, radius_km, max_results]
outputs: [location, restaurants, error]
side_effect: false
---

# search_local

Tìm quán ăn / cafe / nhà hàng gần vị trí người dùng qua SerpAPI google_maps.  
Nếu không có `lat`/`lng`, tự phát hiện vị trí qua IP.

## Inputs

| Tham số | Kiểu | Bắt buộc | Mặc định | Mô tả |
|---------|------|----------|----------|-------|
| `query` | string | ✅ | — | Từ khoá. Ví dụ: `"quán ăn"`, `"quán cafe"`, `"bún bò"`, `"chay"` |
| `lat` | number | — | auto (IP) | Vĩ độ người dùng |
| `lng` | number | — | auto (IP) | Kinh độ người dùng |
| `radius_km` | number | — | `1.5` | Bán kính tìm (km). Dùng `3.0–5.0` khi không tìm thấy kết quả |
| `max_results` | integer | — | `5` | Số quán trả về, tối đa 20 |

## Outputs

```json
{
  "location": {
    "display_name": "Nha Trang, Khánh Hòa",
    "city": "Nha Trang",
    "province": "Khánh Hòa",
    "lat": 12.2451,
    "lng": 109.1943,
    "source": "gps"
  },
  "query": "quán ăn",
  "radius_km": 1.5,
  "total_found": 20,
  "restaurants": [
    {
      "rank": 1,
      "name": "Bún cá Nha Trang Bà Bảy",
      "address": "12 Bến Chợ, Nha Trang, Khánh Hòa",
      "distance": "345m",
      "distance_m": 345,
      "lat": 12.2482,
      "lng": 109.1943,
      "rating": 4.6,
      "review_count": 234,
      "type": "Nhà hàng",
      "types": ["Nhà hàng"],
      "price": "1-100.000 ₫",
      "price_level": 1,
      "open_state": "Đang mở cửa · Đóng cửa vào 14:00",
      "operating_hours": { "thứ hai": "06:00–14:00" },
      "highlights": ["Bún cá ngon", "Giá bình dân"],
      "offerings": ["Bún cá", "Chả cá"],
      "atmosphere": ["Bình dân"],
      "popular_for": ["Bữa trưa"],
      "amenities": ["Nhà vệ sinh"],
      "service_options": ["Ăn tại chỗ", "Đồ ăn mang đi"],
      "payments": ["Chỉ nhận tiền mặt"],
      "parking": ["Bãi đỗ xe miễn phí"],
      "phone": "+84 258 3123 456",
      "website": null,
      "user_review": "\"Nước dùng đậm vị cá tươi.\"",
      "maps_url": "https://www.google.com/maps/dir/...",
      "thumbnail": "https://lh3.googleusercontent.com/...",
      "place_id": "ChIJ...",
      "data_id": "0x3135..."
    }
  ],
  "error": null
}
```

Khi lỗi: `restaurants = []`, `error = "mô tả lỗi"`.

## Notes

- `data_id` dùng để gọi `svc.get_reviews(restaurant)` nếu cần review đầy đủ.
- Khi Failure Path, agent thử lại với `radius_km=3.0` hoặc `5.0`.
- Tool không tự gọi reviews hay AI menu để giữ latency thấp.
