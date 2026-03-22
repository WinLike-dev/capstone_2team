from fastapi import APIRouter, BackgroundTasks, Request

from app.schemas.common import SuccessResponse
from app.schemas.meal import ProcessMealRequest
from app.services.meal_service import process_meal as handle_process_meal

router = APIRouter(tags=["meal"])


@router.post("/process-meal", response_model=SuccessResponse)
async def process_meal_endpoint(
    body: ProcessMealRequest,
    request: Request,
    background_tasks: BackgroundTasks,
) -> SuccessResponse:
    """식단 분석 서비스 파이프라인을 호출한다."""
    return await handle_process_meal(body, request, background_tasks)
