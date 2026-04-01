from pydantic import BaseModel

from app.schemas.common import UserProfile


class ProcessMealRequest(BaseModel):
    user_id: str
    user_profile: UserProfile
    user_instruction: str
    user_message: str


class MealAnalysisData(BaseModel):
    calories: float
    message: str
