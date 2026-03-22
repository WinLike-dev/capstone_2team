from fastapi import APIRouter, BackgroundTasks, Request

from app.schemas.common import SuccessResponse
from app.schemas.recommend import RecommendRequest
from app.services.recommend_service import recommend as handle_recommend

router = APIRouter(tags=["recommend"])


@router.post("/recommend", response_model=SuccessResponse)
async def recommend_endpoint(
    body: RecommendRequest,
    request: Request,
    background_tasks: BackgroundTasks,
) -> SuccessResponse:
    """운동/식단 추천 서비스 파이프라인을 호출한다."""
    return await handle_recommend(body, request, background_tasks)
