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

@app.post("/chat")
async def chat(req: ChatRequest):
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
        return result
    except Exception as e:
        log_error("chat_endpoint", str(e))
        return {"error": "server_error", "message": str(e)}

@app.get("/health")
def health():
    return {"status": "ok"}

# Serve frontend
os.makedirs("frontend", exist_ok=True)
if not os.path.exists("frontend/index.html"):
    with open("frontend/index.html", "w", encoding="utf-8") as f:
        f.write("<h1>Frontend Placeholder</h1>")

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
