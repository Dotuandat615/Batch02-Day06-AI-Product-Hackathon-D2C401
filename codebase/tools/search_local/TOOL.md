# Tool: search_nearby_restaurants

Tìm quán ăn / cafe / nhà hàng gần vị trí người dùng.  
Gọi đến `modules/location` — dữ liệu thật từ **SerpAPI google_maps**.

---

## Đầu vào (Input)

| Tham số | Kiểu | Bắt buộc | Mặc định | Mô tả |
|---------|------|----------|----------|-------|
| `query` | string | ✅ | — | Từ khoá tìm kiếm. Ví dụ: `"quán ăn"`, `"quán cafe"`, `"bún bò"`, `"chay"` |
| `lat` | number | — | auto (IP) | Vĩ độ người dùng |
| `lng` | number | — | auto (IP) | Kinh độ người dùng |
| `radius_km` | number | — | `1.5` | Bán kính tìm (km). Dùng `3.0–5.0` nếu không tìm thấy |
| `max_results` | integer | — | `5` | Số quán tối đa trả về (tối đa 20) |

> Nếu không có `lat`/`lng`, tool tự phát hiện vị trí qua IP.

---

## Đầu ra (Output)

JSON string với schema:

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
      "operating_hours": { "thứ hai": "06:00–14:00", "...": "..." },
      "highlights": ["Bún cá ngon", "Giá bình dân"],
      "offerings": ["Bún cá", "Chả cá"],
      "atmosphere": ["Bình dân", "Đông khách"],
      "popular_for": ["Bữa sáng", "Bữa trưa"],
      "amenities": ["Nhà vệ sinh"],
      "service_options": ["Ăn tại chỗ", "Đồ ăn mang đi"],
      "payments": ["Chỉ nhận tiền mặt"],
      "parking": ["Bãi đỗ xe miễn phí"],
      "phone": "+84 258 3123 456",
      "website": null,
      "user_review": "\"Nước dùng đậm vị cá tươi, đúng kiểu Nha Trang.\"",
      "maps_url": "https://www.google.com/maps/dir/12.2451,109.1943/12.2482,109.1943",
      "thumbnail": "https://lh3.googleusercontent.com/...",
      "place_id": "ChIJ...",
      "data_id": "0x3135..."
    }
  ],
  "error": null
}
```

Khi lỗi: `restaurants = []`, `error = "mô tả lỗi"`.

---

## Tích hợp vào agent loop

```python
import anthropic
from tools.search_local.tool import TOOL_DEFINITION, execute

client = anthropic.Anthropic()

# Bước 1 — Gửi message và khai báo tool
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=[TOOL_DEFINITION],
    messages=[
        {"role": "user", "content": "Tìm quán bún bò gần tôi, tôi đang ở Nha Trang"}
    ],
)

# Bước 2 — Xử lý khi Claude quyết định gọi tool
while response.stop_reason == "tool_use":
    tool_results = []
    for block in response.content:
        if block.type == "tool_use" and block.name == "search_nearby_restaurants":
            result = execute(block.input)          # gọi tool thật
            tool_results.append({
                "type":        "tool_result",
                "tool_use_id": block.id,
                "content":     result,
            })

    # Bước 3 — Trả kết quả tool về cho Claude
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=[TOOL_DEFINITION],
        messages=[
            {"role": "user",      "content": "Tìm quán bún bò gần tôi, tôi đang ở Nha Trang"},
            {"role": "assistant", "content": response.content},
            {"role": "user",      "content": tool_results},
        ],
    )

# Bước 4 — In câu trả lời cuối
print(response.content[0].text)
```

---

## Yêu cầu môi trường

```
MAP_API           = <serpapi_key>         # bắt buộc
MAP_ENDPOINT      = https://serpapi.com/search
ANTHROPIC_API_KEY = <key>                 # chỉ cần nếu gọi get_ai_menu
```

---

## Ghi chú

- `data_id` trong mỗi quán dùng để gọi `svc.get_reviews(restaurant)` nếu cần review đầy đủ.
- `radius_km` mặc định 1.5km — phù hợp đi bộ. Khi Failure Path (không tìm được), agent nên thử lại với `radius_km=3.0` hoặc `5.0`.
- Tool không tự gọi reviews hay AI menu để giữ latency thấp. Agent chủ động gọi thêm khi cần.
