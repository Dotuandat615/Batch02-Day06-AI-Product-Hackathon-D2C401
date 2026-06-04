# Tool Folder Contract

Mỗi tool nằm trong folder riêng:

```text
tools/<tool_name>/
  TOOL.md   # frontmatter + mô tả tool
  tool.py   # implementation (hoặc mock stub)
```

`tools/__init__.py` là registry. `agent.py`, `chat.py`, và `run_eval.py`
import `TOOL_FUNCTIONS` từ registry này.

## Các tool hiện có

| Tool | Loại | Mô tả | Status |
|---|---|---|---|
| `clarify` | control | Hỏi MCQ / hỏi bổ sung thông tin | ✅ Hoạt động |
| `search_local` | live_api | Tìm quán ăn và chi tiết gần vị trí GPS (SerpAPI) | ✅ Hoạt động |
| `format_recommendations` | local_formatter | Format 3 quán gợi ý cho user | ✅ Hoạt động |

## Frontmatter Fields (TOOL.md)

```yaml
---
name: tool_name
track: core | bonus
kind: live_api | local_formatter | control
provider: Provider name if any
requires_env: [ENV_VAR]
inputs: [arg_name]
outputs: [field_name]
side_effect: false | true
---
```

## Thêm tool mới

1. Tạo folder `tools/<tên_tool>/`
2. Viết `TOOL.md` (frontmatter + mô tả)
3. Viết `tool.py` (function implementation)
4. Thêm import + entry vào `tools/__init__.py` → `TOOL_FUNCTIONS`
5. Thêm declaration vào `artifacts/tools.yaml`
6. Thêm eval case vào `data/eval_base.json` hoặc `data/eval_group.json`

> **QUAN TRỌNG:** Tên tool phải sync across: `tools.yaml` ↔ `__init__.py` ↔ `eval_*.json`
