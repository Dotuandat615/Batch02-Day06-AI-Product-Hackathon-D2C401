from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from places_service import search_nearby, get_place_details, expand_radius_if_needed, build_maps_link
from ai_service import get_recommendations
from logger import log_request, log_places_result, log_ai_response, log_error
from models import RecommendRequest

import os

app = FastAPI(title="AI Food Recommender")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.post("/recommend")
async def recommend(req: RecommendRequest):
    log_request(req.mcq.model_dump(), req.lat, req.lng)
    try:
        # 1. Lấy danh sách quán, tự mở rộng bán kính nếu cần
        radius = 500
        places = []
        while len(places) < 3 and radius <= 5000:
            places = await search_nearby(req.lat, req.lng, radius)
            new_radius = expand_radius_if_needed(places, radius)
            if new_radius == radius:
                break
            radius = new_radius

        log_places_result(len(places), radius)

        if not places:
            return {"error": "no_places_found", "message": "Không tìm thấy quán nào gần đây."}

        # 2. Gọi AI
        ai_result = await get_recommendations(req.mcq.model_dump(), places)
        log_ai_response(ai_result.get("recommendations", []), ai_result.get("warning"))

        # 3. Enrich với Maps link
        for rec in ai_result["recommendations"]:
            place = next((p for p in places if p["place_id"] == rec["place_id"]), None)
            if place:
                loc = place["geometry"]["location"]
                rec["maps_link"] = build_maps_link(loc["lat"], loc["lng"])
                rec["name"] = place.get("name")
                rec["address"] = place.get("vicinity")
                rec["rating"] = place.get("rating")

        return ai_result

    except Exception as e:
        log_error("recommend", str(e))
        return {"error": "server_error", "message": "Có lỗi xảy ra, vui lòng thử lại."}

@app.get("/health")
def health():
    return {"status": "ok"}

# Serve frontend
os.makedirs("frontend", exist_ok=True)
if not os.path.exists("frontend/index.html"):
    with open("frontend/index.html", "w", encoding="utf-8") as f:
        f.write("<h1>Frontend Placeholder</h1>")

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
