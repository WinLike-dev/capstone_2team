import logging
from fastapi import APIRouter, HTTPException, status

from models.request_models import GenerateRequest
from models.response_models import GenerateResponse, ErrorResponse
from chains.health_chain import run_health_chain

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["AI Generate"])


@router.post(
    "/generate",
    response_model=GenerateResponse,
    responses={
        500: {"model": ErrorResponse, "description": "AI 처리 중 내부 오류"},
    },
    summary="AI 헬스케어 응답 생성",
    description=(
        "사용자의 채팅 메시지와 컨텍스트(키, 체중, MBTI 등)를 받아 "
        "AI 라우터가 의도를 분류한 뒤 Gemini로 맞춤 응답을 생성합니다.\n\n"
        "**인텐트 분류**\n"
        "- 1. 단순 질문 → action_type: advice\n"
        "- 2. 계획 추가/수정 → action_type: ui_update, widget: plan_editor\n"
        "- 3. 사용자 정보 수정 → action_type: ui_update, widget: profile_editor\n"
        "- 4. 식단 구성 → action_type: ui_update, widget: diet_planner"
    ),
)
async def generate(request: GenerateRequest) -> GenerateResponse:
    """
    POST /api/v1/generate

    [흐름]
    1. AI 라우터: 사용자 발화를 1~4 인텐트로 분류
    2. 메인 AI: 인텐트별 특화 프롬프트 + 사용자 DB 기반 답변 생성
    3. 응답 래핑: GenerateResponse 형태로 반환
    """
    logger.info(
        "generate 요청 수신. user_id=%s, message=%r",
        request.user_id,
        request.current_message[:50],
    )

    try:
        result = await run_health_chain(request)
        return GenerateResponse(**result)
    except Exception as e:
        logger.exception("AI 체인 실행 중 예외 발생. user_id=%s", request.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 처리 중 오류가 발생했습니다: {str(e)}",
        )
