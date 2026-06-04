from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import re
import time
from pathlib import Path

# Tích hợp Logger (Person 4 — Hoàng Hiếu Trung)
from logger import log_request, log_places_result, log_ai_response, log_agent_metrics, log_error

# Import cho Agent
from models import ChatRequest
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from chat import run_model_tool_loop

app = FastAPI(title="AI Food Recommender Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo Agent components (load 1 lần lúc startup)
ROOT = Path(__file__).parent
SYSTEM_PROMPT_PATH = ROOT / "artifacts" / "system_prompt.md"
TOOLS_PATH = ROOT / "artifacts" / "tools.yaml"

system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
tool_declarations = load_tool_declarations(TOOLS_PATH)
openai_tools = to_openai_tools(tool_declarations)

# Dùng provider anthropic (hoặc đổi thành gemini/openai nếu muốn)
provider = make_provider("openai")
default_model = getattr(provider, "default_model", None)

@app.post("/chat")
async def chat(req: ChatRequest):
    # [1] Log request ngay khi nhận — ghi nhận toạ độ và preview message
    msg_preview = req.messages[-1].content[:80] if req.messages else ""
    log_request({"message": msg_preview}, req.lat or 0.0, req.lng or 0.0)

    t0 = time.perf_counter()
    try:
        messages = [{"role": msg.role, "content": msg.content} for msg in req.messages]

        # Inject GPS vào system message khi frontend đã lấy được vị trí thật.
        # Nếu không inject, LLM sẽ gọi tool mà không có lat/lng → tool fallback sang IP.
        if req.lat is not None and req.lng is not None:
            gps_note = (
                f"\n\n[GPS] Vị trí thật của người dùng: lat={req.lat}, lng={req.lng}. "
                f"Khi gọi search_nearby_restaurants, LUÔN truyền lat={req.lat} và lng={req.lng}."
            )
            sys_idx = next((i for i, m in enumerate(messages) if m["role"] == "system"), None)
            if sys_idx is not None:
                messages[sys_idx] = {**messages[sys_idx],
                                     "content": messages[sys_idx]["content"] + gps_note}
            else:
                messages.insert(0, {"role": "system", "content": system_prompt + gps_note})


        result = run_model_tool_loop(
            provider=provider,
            messages=messages,
            tools=openai_tools,
            model=default_model,
            max_tool_rounds=4,
        )

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        tool_events = result.get("tool_events", [])

        # [2] Log places result — trích từ kết quả search_nearby
        for event in tool_events:
            if event.get("tool") == "search_nearby":
                search_res = event.get("result", {})
                places_count = len(search_res.get("places", []))
                radius = search_res.get("radius", 500)
                log_places_result(places_count, radius)
                break

        # [3] Log AI response — trích cards từ format_recommendations
        fmt_events = [e for e in tool_events if e.get("tool") == "format_recommendations"]
        cards = fmt_events[-1].get("result", {}).get("cards", []) if fmt_events else []
        warning = None
        for event in tool_events:
            w = event.get("result", {})
            if isinstance(w, dict) and w.get("warning"):
                warning = w["warning"]
                break
        log_ai_response(cards, warning)

        # [4] Log agent metrics — latency + model + parse success
        log_agent_metrics(
            latency_ms=elapsed_ms,
            prompt_tokens=0,       # Tool-calling loop không expose token count
            completion_tokens=0,
            model=default_model or "unknown",
            parsing_success=isinstance(result, dict) and "status" in result,
        )

        return result

    except Exception as e:
        log_error("chat_endpoint", str(e))
        return {"error": "server_error", "message": str(e)}

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def get_metrics():
    """
    Endpoint của Person 4 (Tester/Logger)
    Đọc file app.log và tính toán các metrics (Observability)
    """
    log_file = "app.log"
    if not os.path.exists(log_file):
        return {"status": "no_logs", "message": "Chưa có file app.log"}
        
    stats = {
        "total_requests": 0,
        "total_places_found": 0,
        "total_ai_responses": 0,
        "avg_latency_ms": 0,
        "errors": 0
    }
    
    latency_sum = 0
    latency_count = 0
    
    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "[1] REQUEST" in line:
                    stats["total_requests"] += 1
                elif "[2] PLACES" in line:
                    match = re.search(r"found=(\d+)", line)
                    if match:
                        stats["total_places_found"] += int(match.group(1))
                elif "[3] AI_RESP" in line:
                    stats["total_ai_responses"] += 1
                elif "[4] AGENT_METRICS" in line:
                    match = re.search(r"latency=(\d+)ms", line)
                    if match:
                        latency_sum += int(match.group(1))
                        latency_count += 1
                elif "ERROR |" in line:
                    stats["errors"] += 1
                    
        if latency_count > 0:
            stats["avg_latency_ms"] = round(latency_sum / latency_count, 2)
            
        return {"status": "success", "data": stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Serve frontend
os.makedirs("frontend", exist_ok=True)
if not os.path.exists("frontend/index.html"):
    with open("frontend/index.html", "w", encoding="utf-8") as f:
        f.write("<h1>Frontend Placeholder</h1>")

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
