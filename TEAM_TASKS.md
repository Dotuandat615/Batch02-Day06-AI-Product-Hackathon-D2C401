# Phân công & Hướng dẫn thực hiện — Day 06 Hackathon
**Sản phẩm:** Location-based Food Recommendation (AI Local Guide)
**Track:** Food & Local Delivery | **Deadline:** 23:59 ngày 04/06/2026

---

## Tổng quan kiến trúc

```
[Mobile UI]  ──MCQ answers──►  [FastAPI Backend]
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            [Places API]    [AI Engine]      [Logger]
            (Google)        (Claude/GPT)     (file/console)
                    │               │
                    └───────┬───────┘
                            ▼
                    [3 quán + lý do]  ──►  [UI Result cards]
```

**Stack đề xuất:** FastAPI (Python) · React hoặc plain HTML/JS · Google Places API · Anthropic/OpenAI API

---

## Người 1 — Location + Maps API + Error Handling

**Phụ trách:** Lấy dữ liệu quán từ Google Places, xử lý toàn bộ lỗi liên quan đến data.

### Nhiệm vụ chính

**Google Places API**
- Đăng ký API key trên [Google Cloud Console](https://console.cloud.google.com), bật `Places API` và `Maps JavaScript API`
- Gọi `Nearby Search` để lấy danh sách quán theo tọa độ + bán kính
- Lấy thêm chi tiết: tên, địa chỉ, rating, `opening_hours`, ảnh, số review
- Tạo deep-link Google Maps chỉ đường: `https://www.google.com/maps/dir/?api=1&destination=LAT,LNG`

**Error Handling** *(thêm vào scope)*
- Quán đóng cửa: kiểm tra `opening_hours.open_now`, lọc ra hoặc gắn badge `⚠️ Có thể đã đóng`
- Không đủ kết quả (< 3 quán): tự động mở rộng bán kính từ 500m → 1km → 2km → 5km
- Review quá cũ (> 6 tháng): gắn badge `⏱ Cập nhật: X tháng trước`
- Mất kết nối / API lỗi: trả về `{"error": "places_unavailable", "fallback": true}` để UI hiện thông báo thân thiện

### Sơ lược code

```python
# places_service.py
import httpx

PLACES_API_KEY = "YOUR_API_KEY"
NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

async def search_nearby(lat: float, lng: float, radius: int = 500, keyword: str = "restaurant"):
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "keyword": keyword,
        "key": PLACES_API_KEY,
        "language": "vi",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(NEARBY_URL, params=params)
    results = resp.json().get("results", [])
    return results

async def get_place_details(place_id: str) -> dict:
    params = {
        "place_id": place_id,
        "fields": "name,rating,opening_hours,formatted_address,user_ratings_total,photos",
        "key": PLACES_API_KEY,
        "language": "vi",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(DETAILS_URL, params=params)
    return resp.json().get("result", {})

def expand_radius_if_needed(results: list, current_radius: int) -> int:
    """Trả về bán kính mới nếu kết quả < 3"""
    if len(results) < 3 and current_radius < 5000:
        return min(current_radius * 2, 5000)
    return current_radius

def build_maps_link(lat: float, lng: float) -> str:
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"
```

### Checkpoint
- **11:00** — Mock data tĩnh (3 quán hardcode) để P3 và P6 build UI
- **13:00** — Places API gọi thật, error handling hoàn chỉnh

---

## Người 2 — Prompt Engineering + AI Engine

**Phụ trách:** Thiết kế prompt, gọi AI API, sinh gợi ý và lý do phù hợp.

### Nhiệm vụ chính

- Viết system prompt: AI đóng vai Local Guide, tổng hợp MCQ + danh sách quán → chọn 3 phù hợp nhất
- Sinh lý do ngắn gọn (~1 câu) cho từng quán theo profile người dùng
- Xử lý low-confidence: ít quán, rating thấp, review cũ
- Trả về JSON có cấu trúc rõ ràng để UI render

### Sơ lược prompt

```python
# ai_service.py
import anthropic

client = anthropic.Anthropic(api_key="YOUR_API_KEY")

SYSTEM_PROMPT = """Bạn là một Local Guide am hiểu ẩm thực địa phương Việt Nam.
Nhiệm vụ: Nhận danh sách quán ăn gần đó và profile bữa ăn của user, chọn 3 quán phù hợp nhất.

Trả về JSON theo đúng format sau, KHÔNG có text nào khác:
{
  "recommendations": [
    {
      "place_id": "...",
      "reason": "Lý do 1 câu tại sao phù hợp với user",
      "confidence": "high" | "medium" | "low"
    }
  ],
  "warning": null | "Chuỗi cảnh báo nếu kết quả không lý tưởng"
}"""

def build_user_prompt(mcq: dict, places: list) -> str:
    profile = f"""Profile bữa ăn:
- Bữa: {mcq['meal_time']}
- Đi cùng: {mcq['group_type']}
- Phong cách: {mcq['style']}
- Yêu cầu đặc biệt: {mcq['dietary']}

Danh sách quán (tối đa 10):
"""
    for p in places[:10]:
        profile += f"- {p['name']} | rating: {p.get('rating','?')} | {p.get('formatted_address','')}\n"
    return profile

async def get_recommendations(mcq: dict, places: list) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_prompt(mcq, places)}]
    )
    import json
    return json.loads(response.content[0].text)
```

### Checkpoint
- **11:00** — Prompt draft hoàn chỉnh, test offline bằng mock data
- **13:00** — AI gọi thật, JSON trả về đúng format

---

## Người 3 — UI/UX + Frontend

**Phụ trách:** Toàn bộ giao diện người dùng, mobile-first.

### Nhiệm vụ chính

- Màn hình 1: Splash — hiển thị vị trí GPS phát hiện được
- Màn hình 2–5: 4 màn MCQ — mỗi màn 1 câu, tap để chọn, nút "Tiếp theo"
- Màn hình 6: Loading — "AI đang tìm quán phù hợp..."
- Màn hình 7: Kết quả — 3 card quán với tên, khoảng cách, rating, lý do AI, nút "Xem đường đi"
- Màn hình 8: Error state — thông báo thân thiện khi không tìm thấy

### Sơ lược cấu trúc (React)

```jsx
// App.jsx — state machine đơn giản
const SCREENS = ['location', 'q1', 'q2', 'q3', 'q4', 'loading', 'results', 'error'];

const MCQ_CONFIG = [
  { id: 'meal_time', question: 'Bữa ăn này là bữa nào?',
    options: ['🌅 Sáng', '☀️ Trưa', '🌙 Tối', '🌃 Khuya'] },
  { id: 'group_type', question: 'Bạn ăn cùng ai?',
    options: ['👤 Một mình', '👫 Đôi', '👨‍👩‍👧 Gia đình', '👥 Nhóm bạn (3+)'] },
  { id: 'style', question: 'Phong cách bữa ăn?',
    options: ['🍜 Đặc sản địa phương', '🍱 Nhanh - gọn', '🕯️ Thoải mái', '💰 Bình dân'] },
  { id: 'dietary', question: 'Yêu cầu đặc biệt?',
    options: ['🥗 Chay', '🚫 Không hải sản', '🌶️ Không cay', '✅ Không có'] },
];

// ResultCard.jsx
function ResultCard({ rank, name, address, distance, rating, reason, mapsLink, confidence }) {
  return (
    <div className="result-card">
      <span className="rank">#{rank}</span>
      <h3>{name}</h3>
      <p>📍 {address} · {distance}</p>
      <p>⭐ {rating} {confidence === 'low' && <span className="warning">⚠️ Review cũ</span>}</p>
      <p className="reason">💡 {reason}</p>
      <a href={mapsLink} target="_blank">🗺️ Xem đường đi</a>
    </div>
  );
}
```

### Checkpoint
- **11:00** — UI 4 màn MCQ + result screen với data tĩnh
- **13:00** — Kết nối API, trạng thái loading và error hiển thị đúng

---

## Người 4 — Testing + Logging

**Phụ trách:** Đảm bảo 4 paths chạy đúng, log để debug và minh chứng khi demo.

### Nhiệm vụ chính

**Testing — 4 paths từ SPEC**

| Path | Input MCQ | Kết quả mong đợi |
|---|---|---|
| Happy | Trưa / Một mình / Đặc sản / Không yêu cầu | 3 quán, confidence high, lý do rõ |
| Low-confidence | Chay / Khuya | Hiện warning "review cũ", vẫn có 3 gợi ý |
| Failure | Hủ tiếu chay / Khuya / 500m | AI báo không tìm thấy, đề xuất mở rộng |
| Correction | Bất kỳ / vị trí không có quán | Tự động thử bán kính 1km, 2km, 5km |

**Logging** *(thêm vào scope)*

```python
# logger.py
import logging, json
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()  # cũng in ra console
    ]
)
logger = logging.getLogger("foodai")

def log_request(mcq: dict, lat: float, lng: float):
    logger.info(f"REQUEST | lat={lat} lng={lng} | mcq={json.dumps(mcq, ensure_ascii=False)}")

def log_places_result(count: int, radius: int):
    logger.info(f"PLACES | found={count} quán | radius={radius}m")

def log_ai_response(recommendations: list, warning: str | None):
    logger.info(f"AI_RESP | recs={len(recommendations)} | warning={warning}")

def log_error(stage: str, error: str):
    logger.error(f"ERROR | stage={stage} | {error}")
```

**Test script để chạy tay nhanh**

```bash
# test_paths.sh — chạy trước demo
echo "=== Happy path ==="
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"lat":12.238791,"lng":109.196749,"mcq":{"meal_time":"Trưa","group_type":"Một mình","style":"Đặc sản địa phương","dietary":"Không có"}}'

echo "=== Failure path ==="
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"lat":12.238791,"lng":109.196749,"mcq":{"meal_time":"Khuya","group_type":"Một mình","style":"Đặc sản địa phương","dietary":"Chay"}}'
```

### Checkpoint
- **13:00** — Test script 4 paths viết xong, chạy được
- **15:30** — Bug report nộp cho P6, log file sẵn sàng cho demo

---

## Người 5 — Slide + Demo Script

**Phụ trách:** Nội dung trình bày, đảm bảo demo trôi chảy trong 5 phút.

### Cấu trúc slide (6 slide)

| # | Slide | Nội dung |
|---|---|---|
| 1 | Problem | Quote user: *"Mở Google Maps rồi không biết gõ gì"* · 61% rời app sau search đầu tiên |
| 2 | Solution | AI Local Guide · 4 tap → 3 gợi ý · không cần gõ |
| 3 | Augment vs Automate | AI gợi ý, human quyết định · sơ đồ đơn giản |
| 4 | Live demo | (chuyển sang app) |
| 5 | Failure modes | Quán đóng cửa, review cũ, không tìm thấy → cách xử lý |
| 6 | Lessons learned | Điều làm được · Điều chưa build · Nếu có thêm 1 ngày |

### Demo script 5 phút

```
0:00 – 0:30  [P5] Giới thiệu bài toán — Minh ở Nha Trang, đói, không biết ăn gì
0:30 – 1:00  [P5] Giải pháp — 4 MCQ, AI tổng hợp, 3 gợi ý
1:00 – 2:30  [P3] Live demo — Happy path (tap MCQ → loading → 3 kết quả → mở Maps)
2:30 – 3:30  [P4] Error case — chọn "Khuya + Chay" → AI hiện warning
3:30 – 4:00  [P2] Giải thích AI làm gì — prompt, lý do gợi ý
4:00 – 5:00  [P5] Lessons + Q&A setup
```

### Checkpoint
- **15:30** — Slide hoàn chỉnh, dry run ≥ 1 lần có bấm giờ
- **16:00** — Mỗi người thuộc phần mình nói

---

## Người 6 — FastAPI Backend + Integration + Deploy

**Phụ trách:** Backend chính, nối tất cả service lại, deploy có URL live.

### Cấu trúc project

```
codebase/
├── main.py              ← FastAPI app, định nghĩa routes
├── places_service.py    ← Code của Người 1
├── ai_service.py        ← Code của Người 2
├── logger.py            ← Code của Người 4
├── models.py            ← Pydantic schemas
├── requirements.txt
└── frontend/            ← Build của Người 3
    └── index.html
```

### FastAPI — endpoint chính

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from places_service import search_nearby, get_place_details, expand_radius_if_needed, build_maps_link
from ai_service import get_recommendations
from logger import log_request, log_places_result, log_ai_response, log_error

app = FastAPI(title="AI Food Recommender")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class MCQ(BaseModel):
    meal_time: str
    group_type: str
    style: str
    dietary: str

class RecommendRequest(BaseModel):
    lat: float
    lng: float
    mcq: MCQ

@app.post("/recommend")
async def recommend(req: RecommendRequest):
    log_request(req.mcq.dict(), req.lat, req.lng)
    try:
        # 1. Lấy danh sách quán, tự mở rộng bán kính nếu cần
        radius = 500
        places = []
        while len(places) < 3 and radius <= 5000:
            places = await search_nearby(req.lat, req.lng, radius)
            new_radius = expand_radius_if_needed(places, radius)
            if new_radius == radius:
                break
            radius = new_radius

        log_places_result(len(places), radius)

        if not places:
            return {"error": "no_places_found", "message": "Không tìm thấy quán nào gần đây."}

        # 2. Gọi AI
        ai_result = await get_recommendations(req.mcq.dict(), places)
        log_ai_response(ai_result.get("recommendations", []), ai_result.get("warning"))

        # 3. Enrich với Maps link
        for rec in ai_result["recommendations"]:
            place = next((p for p in places if p["place_id"] == rec["place_id"]), None)
            if place:
                loc = place["geometry"]["location"]
                rec["maps_link"] = build_maps_link(loc["lat"], loc["lng"])
                rec["name"] = place.get("name")
                rec["address"] = place.get("vicinity")
                rec["rating"] = place.get("rating")

        return ai_result

    except Exception as e:
        log_error("recommend", str(e))
        return {"error": "server_error", "message": "Có lỗi xảy ra, vui lòng thử lại."}

@app.get("/health")
def health():
    return {"status": "ok"}

# Serve frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

```
# requirements.txt
fastapi
uvicorn
httpx
anthropic
python-dotenv
```

### Deploy lên Render (miễn phí, nhanh nhất)

```bash
# 1. Push code lên GitHub repo nhóm
# 2. Vào https://render.com → New Web Service → kết nối repo
# 3. Build command:  pip install -r requirements.txt
# 4. Start command:  uvicorn main:app --host 0.0.0.0 --port $PORT
# 5. Thêm Environment Variables: PLACES_API_KEY, ANTHROPIC_API_KEY
# → Render tự deploy, có URL dạng https://ten-app.onrender.com
```

> **Phương án dự phòng:** Nếu deploy không kịp, chạy local và dùng `ngrok http 8000` để có URL public tạm thời.

### Checkpoint
- **13:00** — App chạy end-to-end trên local, P4 test được
- **15:30** — Có URL live (Render) hoặc video backup 2 phút quay sẵn

---

## Timeline tổng hợp

| Giờ | P1 | P2 | P3 | P4 | P5 | P6 |
|---|---|---|---|---|---|---|
| Sáng | Đăng ký API key, mock data | Viết + test prompt offline | Build UI 4 MCQ + result tĩnh | Viết test script 4 paths | Làm slide 1–3 | Setup FastAPI, kết nối P1+P2 |
| **11:00 CP1** | Mock data giao P6 | Prompt draft xong | UI chạy với mock data | Test case viết xong | Slide 1–3 xong | App chạy local với mock |
| Trưa | Gắn Places API thật, error handling | Test AI với data thật | Nối UI với API | Chạy test thật, ghi log | Slide 4–6 + demo script | Gắn AI thật, test tích hợp |
| **13:00 CP2** | Places API + errors hoàn chỉnh | AI JSON đúng format | UI full flow hoàn chỉnh | 4 paths pass | Demo script xong | End-to-end chạy được |
| Chiều | Hỗ trợ P6 fix bug | Tinh chỉnh prompt | Fix bug UI | Bug report, kiểm tra log | Dry run ≥ 1 lần | Deploy Render / quay backup |
| **15:30 CP3** | — | — | — | Log file sẵn sàng | Slide + script hoàn chỉnh | URL live hoặc video backup |
| **16:00 Demo** | Trả lời Q&A phần Places/error | Trả lời Q&A phần AI/prompt | Live demo UI | Show error case + log | Dẫn chương trình | Deploy sẵn sàng |

---

## Câu hỏi mọi người phải trả lời được khi bị hỏi

- **Augment hay Automate?** → Augment. AI gợi ý, user quyết định đi quán nào.
- **Failure mode chính?** → Quán đóng cửa không cập nhật trên Maps. Mitigation: badge cảnh báo + link kiểm tra Maps.
- **Phần mình làm gì?** → Mỗi người tự chuẩn bị 2–3 câu mô tả phần của mình.
- **Tại sao không dùng Foody/Google Maps thôi?** → Foody không filter context (bữa nào, mấy người, phong cách). AI tổng hợp profile người dùng và sinh lý do match — đây là giá trị thêm.
