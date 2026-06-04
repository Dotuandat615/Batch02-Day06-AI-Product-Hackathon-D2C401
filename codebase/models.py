from pydantic import BaseModel

class MCQ(BaseModel):
    meal_time: str
    group_type: str
    style: str
    dietary: str

class RecommendRequest(BaseModel):
    lat: float
    lng: float
    mcq: MCQ
