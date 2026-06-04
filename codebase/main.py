from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

# Cấu hình log
from logger import log_error

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

def inject_gps(
    messages: list,
    lat: float | None,
    lng: float | None,
    fallback_system: str = "",
) -> list:
    """
    Inject GPS coordinates into the system message so the LLM passes them to tools.

    - Nếu lat/lng là None → trả về messages không đổi.
    - Nếu đã có system message → append GPS note vào cuối.
    - Nếu chưa có system message → tạo mới từ fallback_system + GPS note, chèn vào đầu.
    - Không mutate list đầu vào.
    """
    if lat is None or lng is None:
        return messages

    gps_note = (
        f"\n\n[GPS] Vị trí thật của người dùng: lat={lat}, lng={lng}. "
        f"Khi gọi search_nearby_restaurants, LUÔN truyền lat={lat} và lng={lng}."
    )
    msgs = list(messages)
    sys_idx = next((i for i, m in enumerate(msgs) if m["role"] == "system"), None)
    if sys_idx is not None:
        msgs[sys_idx] = {**msgs[sys_idx], "content": msgs[sys_idx]["content"] + gps_note}
    else:
        msgs.insert(0, {"role": "system", "content": fallback_system + gps_note})
    return msgs


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        messages = [{"role": msg.role, "content": msg.content} for msg in req.messages]
        messages = inject_gps(messages, req.lat, req.lng, fallback_system=system_prompt)

        result = run_model_tool_loop(
            provider=provider,
            messages=messages,
            tools=openai_tools,
            model=default_model,
            max_tool_rounds=4,
        )
        return result
    except Exception as e:
        log_error("chat_endpoint", str(e))
        return {"error": "server_error", "message": str(e)}

@app.get("/health")
def health():
    return {"status": "ok"}

import re

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
