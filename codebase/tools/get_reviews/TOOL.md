---
name: get_reviews
track: core
kind: live_api
provider: Google Places API
requires_env: [GOOGLE_PLACES_API_KEY]
inputs: [place_id, max_reviews]
outputs: [reviews, summary]
side_effect: false
---
# get_reviews

Lấy review và chi tiết của một quán ăn cụ thể.

- Gọi Google Places Details API
- Trả về: reviews (text + rating + thời gian), tóm tắt điểm mạnh/yếu
- Dùng để AI đánh giá confidence và sinh lý do gợi ý

**Stub hiện tại:** Trả mock reviews. Team P1 (Places API) sẽ implement API thật.
