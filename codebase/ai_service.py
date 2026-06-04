import anthropic
import os
import json

# Sử dụng python-dotenv nếu có file .env
from dotenv import load_dotenv
load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", "YOUR_API_KEY"))

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
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_prompt(mcq, places)}]
    )
    return json.loads(response.content[0].text)
