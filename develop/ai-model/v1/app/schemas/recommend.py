from pydantic import BaseModel

from app.schemas.common import UserProfile


class RecommendRequest(BaseModel):
    user_id: str
    user_profile: UserProfile
    user_instruction: str


class RecommendedExercise(BaseModel):
    name: str
    burn_calories: float


class RecommendedMeal(BaseModel):
    name: str
    calories: float


class RecommendationData(BaseModel):
    recommended_exercise: RecommendedExercise
    recommended_meal: RecommendedMeal
