---
name: clarify
track: core
kind: control
requires_env: []
inputs: [question, response_type, options]
outputs: [question, response_type, options, awaiting_user]
side_effect: false
---
# clarify

Hỏi người dùng để thu thập thông tin hoặc xác nhận hành động.

Dùng trong các trường hợp:
- **MCQ flow**: Hỏi 4 câu MCQ (bữa ăn, đi cùng ai, phong cách, yêu cầu đặc biệt)
- **Thiếu thông tin**: Hỏi bổ sung khi thiếu vị trí GPS, chưa rõ nhu cầu
- **Xác nhận**: Xác nhận trước khi mở đường đi Google Maps

`response_type`:
- `"choice"` → MCQ với danh sách `options`
- `"text"` → Hỏi tự do
- `"yes_no"` → Xác nhận đồng ý/từ chối
