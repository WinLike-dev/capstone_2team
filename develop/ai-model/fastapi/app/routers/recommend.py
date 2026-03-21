from fastapi import APIRouter

from app.schemas.common import SuccessResponse
from app.schemas.recommend import (
    RecommendationData,
    RecommendedExercise,
    RecommendedMeal,
    RecommendRequest,
)

router = APIRouter(tags=["recommend"])


@router.post("/recommend", response_model=SuccessResponse)
async def recommend(request: RecommendRequest) -> SuccessResponse:
    """스텁: Phase 3에서 실제 Gemini 호출로 교체."""
    stub_data = RecommendationData(
        recommended_exercise=RecommendedExercise(name="조깅", burn_calories=300.0),
        recommended_meal=RecommendedMeal(name="닭가슴살 샐러드", calories=400.0),
    )
    return SuccessResponse(data=stub_data.model_dump())
