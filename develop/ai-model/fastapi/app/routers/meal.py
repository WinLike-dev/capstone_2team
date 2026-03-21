from fastapi import APIRouter

from app.schemas.common import SuccessResponse
from app.schemas.meal import MealAnalysisData, ProcessMealRequest

router = APIRouter(tags=["meal"])


@router.post("/process-meal", response_model=SuccessResponse)
async def process_meal(request: ProcessMealRequest) -> SuccessResponse:
    """스텁: Phase 3에서 실제 Gemini 호출로 교체."""
    stub_data = MealAnalysisData(
        calories=350.0,
        message="식단이 기록되었습니다. 균형 잡힌 식사입니다.",
    )
    return SuccessResponse(data=stub_data.model_dump())
