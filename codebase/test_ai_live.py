import asyncio
import json
import os
import sys
from pathlib import Path

# Add the codebase directory to sys.path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_service import get_recommendations
from tools.search_nearby.tool import MOCK_PLACES
from env_loader import load_lab_env

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"

# Load environment variables from .env
load_lab_env(ROOT)

async def run_eval():
    eval_file = DATA_DIR / "eval_group.json"
    if not eval_file.exists():
        print(f"Eval file not found: {eval_file}")
        return
        
    with open(eval_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    cases = data.get("cases", [])
    if not cases:
        print("No test cases found.")
        return
        
    print(f"Loaded {len(cases)} test cases from {eval_file.name}")
    print("="*50)
    
    for case in cases:
        case_id = case.get("id", "unknown")
        print(f"\n=== Running Test Case: {case_id} ===")
        mcq = case.get("mcq", {})
        
        if case.get("empty_places"):
            places = []
        else:
            places = MOCK_PLACES
            
        print("Input MCQ:", json.dumps(mcq, ensure_ascii=False))
        
        # Call the real AI service
        result = await get_recommendations(mcq, places)
        
        print("\nAI Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(run_eval())
