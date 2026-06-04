import sys
import json
import os
from pathlib import Path
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from chat import run_model_tool_loop

def main():
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No query provided"}))
        return
        
    query = sys.argv[1]
    
    ROOT = Path(__file__).parent
    ARTIFACTS_DIR = ROOT / "artifacts"
    load_lab_env(ROOT)
    
    provider = make_provider("gemini")
    
    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    system_prompt = system_prompt_path.read_text(encoding="utf-8") if system_prompt_path.exists() else "You are a helpful research agent."
    
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    tool_declarations = load_tool_declarations(tools_path) if tools_path.exists() else []
    openai_tools = to_openai_tools(tool_declarations) if tool_declarations else []
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]
    
    try:
        old_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w', encoding='utf-8')
        result = run_model_tool_loop(
            provider=provider,
            messages=messages,
            tools=openai_tools,
            model=None,
            max_tool_rounds=2
        )
        sys.stdout.close()
        sys.stdout = old_stdout
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        sys.stdout = old_stdout
        print(json.dumps({"error": str(e)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
