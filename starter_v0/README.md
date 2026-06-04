# 🍜 AI Local Food Guide — Eval & Prompt Engineering Sandbox

> Folder này là **sandbox** để team tinh chỉnh prompt, viết eval test, và phát triển tool stubs.
> Backend chính (FastAPI) nằm ở `../codebase/`.

## Cấu trúc thư mục

```
starter_v0/
├── artifacts/              ← Prompt + Tool declarations (P2 sửa ở đây)
│   ├── system_prompt.md    ← System prompt cho AI Local Guide
│   ├── tools.yaml          ← Khai báo tools (tên, mô tả, params)
│   ├── REPORT.md           ← Ghi kết quả eval
│   └── version_log.csv     ← Lịch sử thay đổi prompt/tools
│
├── tools/                  ← Tool implementations (P1 implement API thật)
│   ├── clarify/            ← Hỏi MCQ / hỏi bổ sung thông tin
│   ├── search_nearby/      ← 🔧 Stub — tìm quán gần vị trí
│   ├── get_reviews/        ← 🔧 Stub — lấy review quán
│   ├── format_recommendations/ ← Format 3 quán gợi ý
│   ├── __init__.py         ← Registry (mapping tên → function)
│   ├── _shared.py          ← Utility chung (haversine, maps link)
│   └── README.md           ← Hướng dẫn thêm tool mới
│
├── data/                   ← Eval test cases (P4 viết ở đây)
│   ├── eval_base.json      ← Cases cơ bản (KHÔNG sửa)
│   └── eval_group.json     ← Cases team tự thêm
│
├── providers/              ← LLM provider adapters (OpenAI, Anthropic, Gemini)
├── agent.py                ← FoodGuideAgent — agent loop
├── chat.py                 ← Interactive chat CLI
├── run_eval.py             ← Chạy eval tự động
├── run_single.py           ← Chạy 1 query nhanh
├── versioning.py           ← Hash prompt+tools để track version
├── env_loader.py           ← Load .env
├── ui/                     ← Frontend (P3 build ở đây)
├── scripts/                ← Utility scripts
└── .env.example            ← Template env vars
```

---

## Ai làm gì trong folder này?

| Vai trò | File cần sửa | Việc cần làm |
|---|---|---|
| **P1** (Places API) | `tools/search_nearby/tool.py`, `tools/get_reviews/tool.py` | Thay mock data bằng Google Places API thật |
| **P2** (Prompt) | `artifacts/system_prompt.md`, `artifacts/tools.yaml` | Tinh chỉnh prompt, mô tả tool |
| **P3** (UI/UX) | `ui/` | Build frontend |
| **P4** (Testing) | `data/eval_group.json` | Viết thêm eval cases cho 4 paths |
| **P6** (Backend) | Xem `../codebase/` | Tích hợp vào FastAPI |

---

## Cách chạy

### 1. Setup

```bash
cd starter_v0
cp .env.example .env
# Điền API key vào .env

pip install -r requirements.txt
```

### 2. Chat thử (interactive)

```bash
python chat.py --provider gemini --version v0
```

Gõ tin nhắn, AI sẽ trả lời và gọi tools. Gõ `/exit` để thoát.

### 3. Chạy 1 query nhanh

```bash
python run_single.py "Tôi ở Nha Trang, muốn ăn trưa đặc sản địa phương"
```

### 4. Chạy eval

```bash
# Eval base (cases có sẵn)
python run_eval.py --phase B --suite base --version v0 --provider gemini

# Eval group (cases team tự viết)
python run_eval.py --phase B --suite group --version v0 --provider gemini --eval-cases data/eval_group.json
```

### 5. Test provider connection

```bash
python scripts/preflight_provider.py
```

---

## Hướng dẫn viết Eval Cases (cho P4)

Mở `data/eval_group.json`, thêm case vào mảng `"cases"`:

```json
{
  "id": "G01_ten_case",
  "phase": "B",
  "suite": "group",
  "input": "Câu người dùng gõ vào",
  "failure_type": "wrong_tool | wrong_arg_value | missing_info | out_of_scope | unnecessary_tool | wrong_boundary",
  "expect": {
    "tool_calls": [{"name": "search_nearby", "args": {"lat": 12.238, "lng": 109.196}}]
  },
  "metadata": {
    "skill": "tên_kỹ_năng",
    "difficulty": "easy | medium | hard",
    "what_it_tests": "Mô tả ngắn case này test gì"
  }
}
```

### 4 Paths cần cover

| Path | Ví dụ input | Expect |
|---|---|---|
| ✅ Happy | "Ở NT, trưa, một mình, đặc sản, không yêu cầu" | `search_nearby` với đủ args |
| ⚠️ Low-confidence | "Ở NT, khuya, chay" | `search_nearby` → kết quả ít, warning |
| ❌ Failure | "Hủ tiếu chay 2h sáng, cách 500m" | `search_nearby` → không kết quả |
| 🔄 Correction | Multi-turn: thay đổi bữa/yêu cầu | Carry-over + correction |

### Multi-turn case

```json
{
  "id": "G02_multiturn_example",
  "phase": "B",
  "suite": "group",
  "turns": [
    {"role": "user", "content": "Tìm quán ăn trưa gần 12.238, 109.196"},
    {"role": "user", "content": "Tôi ăn chay nhé"},
    {"role": "user", "content": "Tìm quán chay giúp tôi"}
  ],
  "failure_type": "wrong_arg_value",
  "expect": {"tool_calls": [{"name": "search_nearby", "args": {"keyword": "chay"}}]},
  "metadata": {"skill": "multiturn_dietary", "difficulty": "hard", "what_it_tests": "Bổ sung yêu cầu qua nhiều lượt."}
}
```

> **Lưu ý:** `failure_type` cho phép: `wrong_tool`, `wrong_arg_value`, `wrong_boundary`, `unnecessary_tool`, `out_of_scope`, `missing_info`

---

## Hướng dẫn sửa System Prompt (cho P2)

Mở `artifacts/system_prompt.md` và chỉnh trực tiếp. Mỗi lần sửa:

1. Tăng version: `--version v1`, `v2`, ...
2. Chạy eval để so sánh:
   ```bash
   python run_eval.py --phase B --suite base --version v1 --provider gemini
   ```
3. Ghi kết quả vào `artifacts/REPORT.md`
4. Ghi thay đổi vào `artifacts/version_log.csv`

---

## Hướng dẫn implement Tool thật (cho P1)

Mở `tools/search_nearby/tool.py`:
1. Tìm comment `# TODO (P1):`
2. Thay mock data bằng gọi Google Places API thật
3. Giữ nguyên signature function và format return

Tương tự cho `tools/get_reviews/tool.py`.

> **Quan trọng:** Nếu đổi tên tool, phải sync 3 nơi:
> `artifacts/tools.yaml` ↔ `tools/__init__.py` ↔ `data/eval_*.json`

---

## Hướng dẫn thêm Tool mới

1. Tạo folder `tools/<tên_tool>/`
2. Viết `TOOL.md` (xem mẫu trong `tools/clarify/TOOL.md`)
3. Viết `tool.py` (function nhận args, trả dict)
4. Thêm import vào `tools/__init__.py`
5. Thêm entry vào `TOOL_FUNCTIONS` dict
6. Thêm declaration vào `artifacts/tools.yaml`
7. Thêm eval case vào `data/eval_group.json`
