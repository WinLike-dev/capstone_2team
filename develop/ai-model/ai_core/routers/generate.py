import logging
from fastapi import APIRouter, HTTPException, status

from models.request_models import AIChatRequest, MealRequest, RecommendRequest
from models.response_models import AIChatResponse, MealResponse, RecommendResponse, ErrorResponse
from chains.health_chain import run_chat_chain, run_meal_chain, run_recommend_chain

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Core"])


# ──────────────────────────────────────────────────────────────────────────────
# POST /ai-chat — 채팅 (모드 1~6, Router AI 경유)
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/ai-chat",
    response_model=AIChatResponse,
    responses={500: {"model": ErrorResponse}},
    summary="AI 채팅 (모드 1~6)",
    description=(
        "사용자 채팅 메시지를 Router AI가 모드 1~6으로 분류한 후 Worker AI가 응답을 생성합니다.\n\n"
        "**필수 필드**: `user_message`만 전송하면 됩니다.\n\n"
        "| 모드 | 설명 |\n"
        "|------|------|\n"
        "| 1 | 단순 대화/질문 |\n"
        "| 2 | 운동 플랜 작성 |\n"
        "| 3 | 운동 플랜 수정 |\n"
        "| 4 | 식단 플랜 작성 |\n"
        "| 5 | 식단 플랜 수정 |\n"
        "| 6 | 사용자 정보 수정 |"
    ),
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {
                        "user_message": "1주일 운동 루틴 짜줘"
                    }
                }
            }
        }
    },
)
async def ai_chat(request: AIChatRequest) -> AIChatResponse:
    logger.info(
        "/ai-chat 요청. user_id=%s, message=%r",
        request.user_id,
        request.user_message[:50],
    )
    try:
        result = await run_chat_chain(request)
        return AIChatResponse(**result)
    except Exception as e:
        logger.exception("/ai-chat 예외. user_id=%s", request.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ──────────────────────────────────────────────────────────────────────────────
# POST /process-meal — 식단 기록 (모드 7, Router AI 바이패스)
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/process-meal",
    response_model=MealResponse,
    responses={500: {"model": ErrorResponse}},
    summary="식단 기록 (모드 7)",
    description=(
        "사용자가 먹은 식사를 텍스트로 입력하면 Gemini가 칼로리를 분석하고 피드백을 반환합니다.\n\n"
        "Router AI를 거치지 않고 Worker AI Mode 7로 직행합니다.\n\n"
        "**요청 예시** `user_message`: `'점심에 닭가슴살 샐러드 먹었어'`"
    ),
)
async def process_meal(request: MealRequest) -> MealResponse:
    logger.info(
        "/process-meal 요청. user_id=%s, message=%r",
        request.user_id,
        request.user_message[:50],
    )
    try:
        result = await run_meal_chain(request)
        return MealResponse(**result)
    except Exception as e:
        logger.exception("/process-meal 예외. user_id=%s", request.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ──────────────────────────────────────────────────────────────────────────────
# POST /recommend — 운동·식단 추천 (모드 8, AI 전체 바이패스)
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/recommend",
    response_model=RecommendResponse,
    responses={500: {"model": ErrorResponse}},
    summary="운동·식단 추천 (모드 8)",
    description=(
        "사용자 프로필(BMI, 목표, 활동량)을 기반으로 맞춤 운동과 식단을 추천합니다.\n\n"
        "Router AI와 Worker AI를 모두 거치지 않으며, 배경 실행 또는 새로고침 시 호출됩니다.\n\n"
        "사용자가 추천 항목을 수락하면 `/confirm-recommendation` (WAS 담당)으로 캘린더에 등록합니다."
    ),
)
async def recommend(request: RecommendRequest) -> RecommendResponse:
    logger.info("/recommend 요청. user_id=%s", request.user_id)
    try:
        result = await run_recommend_chain(request)
        return RecommendResponse(**result)
    except Exception as e:
        logger.exception("/recommend 예외. user_id=%s", request.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
