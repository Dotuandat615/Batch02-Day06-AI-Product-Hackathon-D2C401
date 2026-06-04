---
name: format_recommendations
track: core
kind: local_formatter
requires_env: []
inputs: [recommendations, user_location]
outputs: [formatted_text]
side_effect: false
---
# format_recommendations

Format danh sách 3 quán gợi ý thành output đẹp cho người dùng.

- Nhận danh sách recommendations từ AI engine
- Tính khoảng cách từ vị trí user đến quán
- Tạo Google Maps deep link cho mỗi quán
- Format thành text có emoji, lý do, cảnh báo nếu cần

**Dùng bởi:** P2 (Prompt Engineering) để format output cuối cùng.
