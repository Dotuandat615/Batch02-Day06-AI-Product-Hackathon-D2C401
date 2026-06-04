import asyncio
import json
from ai_service import get_recommendations, build_user_prompt

# Data mock
MOCK_PLACES = [
    {
        "place_id": "ChIJD7fiBh9uCjERM_A4C1L0A3A",
        "name": "Bún cá Nha Trang Bà Bảy",
        "rating": 4.6,
        "formatted_address": "12 Bến Chợ, Nha Trang"
    },
    {
        "place_id": "ChIJb_xU6ZpuCjERCj5zJjZpZ1U",
        "name": "Bánh căn Mỹ Hòa",
        "rating": 4.4,
        "formatted_address": "Đường Trần Phú, Nha Trang"
    },
    {
        "place_id": "ChIJC6-N3A5uCjERZfH6pI3_QzA",
        "name": "Nem nướng Ninh Hòa Hai Bà",
        "rating": 4.7,
        "formatted_address": "Lô 6 Chợ Đầm, Nha Trang"
    }
]

async def run_tests():
    print("=== TEST HAPPY PATH ===")
    mcq_happy = {
        "meal_time": "Trưa",
        "group_type": "Một mình",
        "style": "Đặc sản địa phương",
        "dietary": "Không có"
    }
    prompt = build_user_prompt(mcq_happy, MOCK_PLACES)
    print("Prompt sẽ gửi đi:\n", prompt)
    
    result = await get_recommendations(mcq_happy, MOCK_PLACES)
    print("AI Response:\n", json.dumps(result, indent=2, ensure_ascii=False))
    print("\n" + "="*40 + "\n")

    print("=== TEST LOW-CONFIDENCE PATH ===")
    mcq_low = {
        "meal_time": "Khuya",
        "group_type": "Một mình",
        "style": "Đặc sản địa phương",
        "dietary": "Chay"
    }
    result = await get_recommendations(mcq_low, MOCK_PLACES)
    print("AI Response:\n", json.dumps(result, indent=2, ensure_ascii=False))
    print("\n" + "="*40 + "\n")

    print("=== TEST FAILURE PATH ===")
    result = await get_recommendations(mcq_low, [])
    print("AI Response:\n", json.dumps(result, indent=2, ensure_ascii=False))
    print("\n" + "="*40 + "\n")

if __name__ == "__main__":
    asyncio.run(run_tests())
