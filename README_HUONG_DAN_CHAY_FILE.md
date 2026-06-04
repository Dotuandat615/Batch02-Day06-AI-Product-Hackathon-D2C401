# Day06-C401-Nhom C1-1 — AI Local Guide

## 1. Thông tin nhóm

**Track:** Food & Local Delivery  
**Tên sản phẩm:** AI Local Guide — Gợi ý quán ăn theo vị trí  
**Bối cảnh demo:** Người dùng đang ở Hà Nội / khu vực trường, muốn tìm quán ăn phù hợp nhanh mà không cần tự gõ nhiều từ khóa trên Google Maps.

### Thành viên nhóm

| STT | Mã học viên   | Họ và tên          | Vai trò chính |
|---|---------------|--------------------|---|
| 1 | `2A202600732` | `Phan Văn Hiếu`    | Location + Google Places API + Error Handling |
| 2 | `2A202600543` | `Đỗ Phan Hà`       | Prompt Engineering + AI Engine |
| 3 | `2A202600818` | `Đỗ Tuấn Đạt`      | UI/UX + Frontend |
| 4 | `2A202600702` | `Hoàng Hiếu Trung` | Testing + Logging |
| 5 | `2A202600740` | `Đàm Xuân Giáp`    | Slide + Demo Script + Product Story |
| 6 | `2A202600555` | `Nguyễn Tùng Lâm`  | FastAPI Backend + Integration + Deploy |

> Ghi chú: Mỗi thành viên cần có ít nhất một commit thực chất trong repo để được tính điểm cá nhân.

---

## 2. Mô tả sản phẩm

**AI Local Guide** là prototype hỗ trợ khách du lịch hoặc người dùng không quen khu vực tìm quán ăn phù hợp theo vị trí hiện tại.

Thay vì phải mở Google Maps rồi tự nghĩ từ khóa tìm kiếm, người dùng chỉ cần trả lời một vài câu hỏi ngắn như:

- Đang muốn ăn bữa nào?
- Đi một mình, đi đôi, gia đình hay nhóm bạn?
- Muốn ăn đặc sản địa phương, ăn nhanh, bình dân hay thoải mái?
- Có yêu cầu đặc biệt như ăn chay, không cay, không hải sản không?

Sau đó hệ thống dùng vị trí hiện tại, Google Places API và AI để đề xuất **3 quán phù hợp nhất**, kèm lý do ngắn gọn và nút mở Google Maps để xem đường đi.

---

## 3. Pain point

Khách du lịch hoặc người dùng mới đến một khu vực thường gặp các vấn đề:

1. Không biết nên tìm từ khóa gì trên Google Maps.
2. Có quá nhiều quán ăn, khó chọn nhanh.
3. Rating cao chưa chắc phù hợp với nhu cầu cá nhân.
4. Không biết quán có đang mở cửa hay không.
5. Mất thời gian đọc nhiều review trước khi quyết định.

Ví dụ: Một người đang ở gần trường tại Hà Nội, muốn ăn trưa nhanh nhưng không quen khu vực. Nếu chỉ mở Google Maps và tìm “quán ăn gần đây”, kết quả trả về rất nhiều nhưng không giải thích quán nào phù hợp với nhu cầu cụ thể của người đó.

---

## 4. Giải pháp

AI Local Guide rút gọn quá trình chọn quán thành flow:

```text
Vị trí hiện tại
      ↓
Người dùng trả lời 4 câu hỏi MCQ
      ↓
Backend gọi Google Places API để lấy danh sách quán gần đó
      ↓
AI phân tích nhu cầu + danh sách quán
      ↓
Trả về 3 gợi ý phù hợp nhất
      ↓
Người dùng chọn quán và mở Google Maps để đi
```

Giá trị chính của sản phẩm:

- Giảm thời gian lựa chọn quán ăn.
- Cá nhân hóa theo ngữ cảnh bữa ăn.
- AI chỉ gợi ý, người dùng vẫn là người quyết định.
- Có xử lý các tình huống lỗi như không đủ quán, quán có thể đã đóng cửa, hoặc kết quả thiếu tin cậy.

---

## 5. AI Augment hay Automate?

Prototype chọn hướng:

## AI Augment — AI hỗ trợ, con người quyết định

AI không tự đặt bàn, không tự gọi món, không tự điều hướng người dùng. AI chỉ:

- Tổng hợp vị trí + nhu cầu + danh sách quán.
- Chọn ra 3 quán phù hợp nhất.
- Giải thích lý do đề xuất.
- Cảnh báo nếu kết quả chưa đủ tin cậy.

Người dùng vẫn giữ quyền quyết định cuối cùng:

- Chọn quán nào.
- Có mở Google Maps hay không.
- Có tin gợi ý của AI hay tự tìm tiếp.

Lý do chọn Augment:

- Dữ liệu từ Google Places có thể chưa chính xác hoàn toàn.
- Quán có thể thay đổi giờ mở cửa, giá cả hoặc tình trạng đông khách.
- Quyết định ăn uống mang tính cá nhân, nên AI chỉ nên hỗ trợ thay vì tự động hóa toàn bộ.

---

## 6. Lát cắt prototype

Prototype tập trung vào một lát cắt nhỏ nhưng đủ để demo end-to-end:

**Một người dùng đang ở một vị trí cụ thể, muốn tìm quán ăn gần đó, trả lời 4 câu hỏi MCQ, hệ thống trả về 3 quán phù hợp kèm lý do AI và link chỉ đường.**

### Input

- `lat`: vĩ độ vị trí hiện tại
- `lng`: kinh độ vị trí hiện tại
- `meal_time`: bữa ăn
- `group_type`: đi cùng ai
- `style`: phong cách bữa ăn
- `dietary`: yêu cầu đặc biệt

### Output

- 3 quán ăn được đề xuất
- Tên quán
- Địa chỉ
- Rating
- Lý do AI đề xuất
- Mức confidence
- Link Google Maps chỉ đường
- Warning nếu dữ liệu không lý tưởng

---

## 7. Luồng trải nghiệm chính

### Happy path

Người dùng chọn:

```text
Bữa trưa
Một mình
Đặc sản địa phương
Không có yêu cầu đặc biệt
```

Hệ thống trả về 3 quán gần vị trí hiện tại, mỗi quán có lý do đề xuất rõ ràng.

### Low-confidence path

Người dùng chọn:

```text
Ăn khuya
Ăn chay
Bán kính gần
```

Nếu kết quả ít hoặc dữ liệu chưa chắc chắn, hệ thống vẫn trả về gợi ý nhưng kèm cảnh báo.

Ví dụ:

```text
Kết quả có thể chưa tối ưu vì hiện có ít quán phù hợp đang mở cửa gần bạn.
```

### Failure path

Nếu không tìm thấy quán phù hợp, hệ thống hiển thị thông báo thân thiện:

```text
Hiện chưa tìm thấy quán phù hợp gần bạn. Bạn có thể thử mở rộng bán kính hoặc bỏ bớt điều kiện lọc.
```

### Correction path

Nếu người dùng đổi nhu cầu, ví dụ từ “không cay” sang “ăn chay”, hệ thống cập nhật profile và chạy lại gợi ý.

---

## 8. Kiến trúc hệ thống

```text
[Frontend UI]
     |
     |  MCQ answers + lat/lng
     v
[FastAPI Backend]
     |
     |----------------------|
     |                      |
     v                      v
[Google Places API]     [AI Engine]
     |                      |
     |                      v
     |              Chọn 3 quán phù hợp
     |              + sinh lý do đề xuất
     |
     v
[Response JSON]
     |
     v
[Result Cards trên UI]
```

---

## 9. Công nghệ sử dụng

### Frontend

- HTML / CSS / JavaScript hoặc React
- Mobile-first UI
- MCQ flow
- Result cards
- Loading state
- Error state

### Backend

- Python
- FastAPI
- Pydantic
- Uvicorn
- HTTPX

### AI / API

- Google Places API
- Google Maps direction link
- OpenAI / Anthropic / Gemini API
- Prompt Engineering
- JSON structured output

### Testing

- Manual test theo 4 paths
- Eval cases
- Log request / response
- Kiểm tra happy path, low-confidence, failure và correction

---

## 10. Cấu trúc repo

```text
Batch02-Day06-AI-Product-Hackathon-D2C401/
├── README.md
├── TEAM_TASKS.md
├── hackathon-rules.md
├── spec/
│   ├── README.md
│   └── spec.md
└── codebase/
    ├── README.md
    └── starter_v0/
        ├── artifacts/
        │   ├── system_prompt.md
        │   ├── tools.yaml
        │   ├── REPORT.md
        │   └── version_log.csv
        ├── tools/
        │   ├── clarify/
        │   ├── search_nearby/
        │   ├── get_reviews/
        │   └── format_recommendations/
        ├── data/
        │   ├── eval_base.json
        │   └── eval_group.json
        ├── providers/
        ├── ui/
        ├── scripts/
        ├── agent.py
        ├── chat.py
        ├── run_eval.py
        ├── run_single.py
        ├── versioning.py
        ├── env_loader.py
        └── .env.example
```

---

## 11. Cách chạy prototype

### Bước 1: Clone repo

```bash
git clone https://github.com/Dotuandat615/Batch02-Day06-AI-Product-Hackathon-D2C401.git
cd Batch02-Day06-AI-Product-Hackathon-D2C401
```

### Bước 2: Vào thư mục codebase

```bash
cd codebase/starter_v0
```

### Bước 3: Tạo file môi trường

```bash
cp .env.example .env
```

Sau đó điền API key vào file `.env`.

Ví dụ:

```env
GOOGLE_PLACES_API_KEY=your_google_places_api_key
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Bước 4: Cài dependencies

```bash
pip install -r requirements.txt
```

### Bước 5: Test provider

```bash
python scripts/preflight_provider.py
```

### Bước 6: Chạy thử một query

```bash
python run_single.py "Tôi đang ở Hà Nội, muốn ăn trưa gần đây, đi một mình, ưu tiên quán bình dân"
```

### Bước 7: Chạy chat CLI

```bash
python chat.py --provider gemini --version v0
```

Gõ `/exit` để thoát.

### Bước 8: Chạy eval

```bash
python run_eval.py --phase B --suite base --version v0 --provider gemini
python run_eval.py --phase B --suite group --version v0 --provider gemini --eval-cases data/eval_group.json
```

---

## 12. API chính dự kiến

### Endpoint

```http
POST /recommend
```

### Request mẫu

```json
{
  "lat": 21.0285,
  "lng": 105.8542,
  "mcq": {
    "meal_time": "Trưa",
    "group_type": "Một mình",
    "style": "Bình dân",
    "dietary": "Không có"
  }
}
```

### Response mẫu

```json
{
  "recommendations": [
    {
      "place_id": "abc123",
      "name": "Quán ăn phù hợp 1",
      "address": "Hoàn Kiếm, Hà Nội",
      "rating": 4.5,
      "reason": "Phù hợp vì gần vị trí hiện tại, giá bình dân và thích hợp cho bữa trưa một mình.",
      "confidence": "high",
      "maps_link": "https://www.google.com/maps/dir/?api=1&destination=21.0285,105.8542"
    }
  ],
  "warning": null
}
```

---

## 13. Kế hoạch kiểm thử

| Path | Input test | Kết quả mong đợi |
|---|---|---|
| Happy path | Trưa / Một mình / Bình dân / Không có | Trả về 3 quán phù hợp, confidence cao |
| Low-confidence | Khuya / Ăn chay / gần vị trí hiện tại | Có warning nếu ít kết quả |
| Failure path | Điều kiện quá hẹp hoặc khu vực ít quán | Thông báo không tìm thấy, đề xuất mở rộng bán kính |
| Correction path | Người dùng đổi yêu cầu ăn uống | Hệ thống cập nhật điều kiện và gợi ý lại |

---

## 14. Những lỗi đáng lo nhất và cách xử lý

### 1. Quán đã đóng cửa nhưng dữ liệu chưa cập nhật

**Rủi ro:** Người dùng đến nơi nhưng quán không mở.  
**Cách xử lý:** Hiển thị trạng thái mở cửa nếu có dữ liệu, gắn cảnh báo nếu thiếu thông tin, luôn cung cấp link Google Maps để người dùng kiểm tra lại.

### 2. AI gợi ý quán không đúng nhu cầu

**Rủi ro:** Người dùng mất niềm tin vào sản phẩm.  
**Cách xử lý:** Cho phép người dùng sửa lựa chọn MCQ và chạy lại gợi ý.

### 3. Không đủ kết quả trong bán kính gần

**Rủi ro:** Sản phẩm trả về rỗng hoặc trải nghiệm kém.  
**Cách xử lý:** Tự động mở rộng bán kính từ gần đến xa hơn, ví dụ 500m → 1km → 2km → 5km.

---

## 15. Phân công công việc

| Người            | Phần phụ trách | Deliverable |
|------------------|---|---|
| Phan Văn Hiếu    | Location + Google Places API | Hàm tìm quán gần vị trí, xử lý thiếu kết quả, tạo link Maps |
| Đỗ Phan Hà       | Prompt + AI Engine | System prompt, structured JSON output, lý do AI đề xuất |
| Đỗ Tuấn Đạt      | Frontend UI/UX | Giao diện MCQ, loading, result cards, error state |
| Hoàng Hiếu Trung | Testing + Logging | Test 4 paths, log request/response, bug report |
| Đàm Xuân Giáp    | Slide + Demo Script | Slide demo, product story, kịch bản trình bày |
| Nguyễn Tùng Lâm  | Backend + Integration | FastAPI endpoint, nối Places API + AI + UI, deploy hoặc chạy local |

---

## 16. Demo script ngắn

### 0:00 – 0:30: Problem

Người dùng đang ở một khu vực không quen, muốn ăn nhưng không biết tìm quán nào. Google Maps trả về nhiều kết quả nhưng chưa cá nhân hóa theo bữa ăn, nhóm đi cùng hoặc yêu cầu đặc biệt.

### 0:30 – 1:00: Solution

AI Local Guide cho phép người dùng trả lời 4 câu hỏi nhanh, sau đó AI đề xuất 3 quán phù hợp nhất theo vị trí và nhu cầu.

### 1:00 – 2:30: Happy path demo

Chọn vị trí hiện tại, chọn bữa trưa, đi một mình, phong cách bình dân, không yêu cầu đặc biệt. Hệ thống trả về 3 quán và lý do đề xuất.

### 2:30 – 3:30: Error / Low-confidence demo

Chọn điều kiện khó hơn như ăn khuya hoặc ăn chay. Hệ thống hiển thị warning nếu kết quả ít hoặc chưa đủ chắc chắn.

### 3:30 – 4:00: AI explanation

AI không tự quyết định thay người dùng. AI phân tích profile bữa ăn và danh sách quán, sau đó sinh lý do gợi ý.

### 4:00 – 5:00: Kết luận

Prototype chứng minh rằng AI có thể giảm thời gian chọn quán, cá nhân hóa trải nghiệm tìm kiếm và hỗ trợ người dùng ra quyết định tốt hơn.

---

## 17. Trạng thái hiện tại

- [x] Có ý tưởng sản phẩm
- [x] Có phân công nhóm
- [x] Có SPEC định hướng
- [x] Có codebase sandbox
- [x] Có prompt / tool / eval structure
- [x] Hoàn thiện API thật
- [x] Hoàn thiện UI demo
- [x] Test đủ 4 paths
- [x] Deploy hoặc chuẩn bị video backup

---

## 18. Kết luận

AI Local Guide là một prototype theo hướng AI Augment, giúp người dùng tìm quán ăn phù hợp nhanh hơn dựa trên vị trí và nhu cầu cá nhân. Sản phẩm không thay thế hoàn toàn quyết định của con người mà đóng vai trò như một trợ lý địa phương: gợi ý, giải thích và cảnh báo khi kết quả chưa chắc chắn.
