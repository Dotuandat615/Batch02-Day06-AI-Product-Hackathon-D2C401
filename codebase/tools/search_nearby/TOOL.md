---
name: search_nearby
track: core
kind: live_api
provider: Google Places API
requires_env: [GOOGLE_PLACES_API_KEY]
inputs: [lat, lng, radius, keyword, meal_time]
outputs: [places]
side_effect: false
---
# search_nearby

Tìm quán ăn gần vị trí người dùng dựa trên tọa độ GPS.

- Gọi Google Places Nearby Search API
- Trả về danh sách quán với: name, place_id, rating, vicinity, opening_hours, distance
- Hỗ trợ mở rộng bán kính tự động nếu kết quả < 3

**Stub hiện tại:** Trả mock data 5 quán ở Nha Trang. Team P1 (Places API) sẽ implement API thật.
