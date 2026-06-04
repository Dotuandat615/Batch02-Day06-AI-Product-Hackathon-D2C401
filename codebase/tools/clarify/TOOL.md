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
- **Gỡ rối & Thu hẹp lựa chọn**: Dùng MCQ để hỏi nhanh khi yêu cầu quá chung chung (vd: "đói quá") hoặc mâu thuẫn.
- **Ràng buộc quan trọng**: Dùng MCQ để xác nhận chính xác mức độ ăn chay, dị ứng, tôn giáo.
- **Thiếu vị trí**: Hỏi bổ sung bằng text khi chưa có tọa độ GPS.
- **Xác nhận**: Xác nhận (yes/no) trước khi mở Google Maps.

`response_type`:
- `"choice"` → MCQ với danh sách `options`
- `"text"` → Hỏi tự do
- `"yes_no"` → Xác nhận đồng ý/từ chối
