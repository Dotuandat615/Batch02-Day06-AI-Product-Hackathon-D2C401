import json

SYSTEM_PROMPT = """Bạn là một Local Guide am hiểu ẩm thực địa phương Việt Nam.
Nhiệm vụ: Nhận danh sách quán ăn gần đó và profile bữa ăn của user, chọn ra đúng 3 quán phù hợp nhất.

Các nguyên tắc bắt buộc:
1. TUYỆT ĐỐI CHỈ chọn quán từ danh sách "Danh sách quán" được cung cấp. Không tự bịa thêm quán.
2. Với các yêu cầu đặc biệt (Chay, Dị ứng, v.v.): Nếu không tìm thấy quán đáp ứng 100%, hãy chọn quán gần đúng nhất nhưng PHẢI set "confidence": "low" và giải thích ở phần "warning".
3. Xử lý Low-confidence: Nếu quán có ít review, review quá cũ, hoặc thông tin giờ mở cửa không chắc chắn (đặc biệt khi ăn Khuya), set "confidence" là "low" hoặc "medium" và thêm "warning".
4. Lý do ("reason"): Cực kỳ ngắn gọn (khoảng 1 câu), giải thích trực tiếp tại sao quán này hợp với các tiêu chí (Bữa ăn, Đi cùng, Phong cách, Yêu cầu đặc biệt).

Trả về JSON theo đúng format sau, KHÔNG có text nào khác (kể cả markdown ```json):
{
  "recommendations": [
    {
      "place_id": "...",
      "reason": "Lý do 1 câu tại sao phù hợp với user",
      "confidence": "high" | "medium" | "low"
    }
  ],
  "warning": null | "Chuỗi cảnh báo nếu dữ liệu không chắc chắn hoặc không đáp ứng đủ yêu cầu"
}"""

def build_user_prompt(mcq: dict, places: list) -> str:
    profile = f"""Profile bữa ăn:
- Bữa: {mcq.get('meal_time', '')}
- Đi cùng: {mcq.get('group_type', '')}
- Phong cách: {mcq.get('style', '')}
- Yêu cầu đặc biệt: {mcq.get('dietary', '')}

Danh sách quán (tối đa 10):
"""
    for p in places[:10]:
        profile += f"- {p.get('name', '')} | rating: {p.get('rating','?')} | {p.get('vicinity', p.get('formatted_address', ''))}\n"
    return profile

async def get_recommendations(mcq: dict, places: list) -> dict:
    """
    Hàm giả lập (mock-up) AI trả về kết quả dựa trên các kịch bản.
    Giúp team ghép nối mà không tốn API.
    """
    # 1. Failure Path (Empty places)
    if not places:
        return {
            "recommendations": [],
            "warning": "Hiện tại không tìm thấy quán nào đáp ứng đầy đủ các tiêu chí bạn yêu cầu."
        }

    try:
        from providers.openai_provider import OpenAIProvider
        provider = OpenAIProvider()
        
        prompt = build_user_prompt(mcq, places)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        response = provider.complete(
            messages=messages,
            response_format={"type": "json_object"}
        )
        
        if response.text:
            return json.loads(response.text)
        
    except Exception as e:
        print(f"AI API Error: {e}")
        
    return {
        "recommendations": [],
        "warning": "Hệ thống AI đang bận hoặc gặp lỗi xử lý, vui lòng thử lại sau."
    }
