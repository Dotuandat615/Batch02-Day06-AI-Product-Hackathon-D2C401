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
        # Chuyển đổi tin nhắn cho provider, luôn prepend system_prompt
        user_messages = [{"role": msg.role, "content": msg.content} for msg in req.messages]
        
        # Nhúng toạ độ GPS vào system_prompt nếu client gửi kèm
        sp = system_prompt
        if req.lat is not None and req.lng is not None:
            sp = f"[Vị trí người dùng: lat={req.lat:.6f}, lng={req.lng:.6f}]\n\n" + sp
        
        messages = [{"role": "system", "content": sp}] + user_messages
        
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

class NoCacheStaticFiles(StaticFiles):
    def is_not_modified(self, response_headers, req_headers) -> bool:
        return False

    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

app.mount("/", NoCacheStaticFiles(directory="frontend", html=True), name="frontend")

