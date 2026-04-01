"""
헬스 메이트 - FastAPI 라우터

/health-plan 엔드포인트에서 LangGraph 파이프라인을 호출하고
최종 결과를 JSON으로 반환한다.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.graph.pipeline import graph

router = APIRouter(prefix="/api/v1", tags=["HealthMate"])


# ── 요청/응답 스키마 ──────────────────────────────────────────────────────────

class PlanRequest(BaseModel):
    user_input: str = Field(
        ...,
        min_length=2,
        description="사용자의 운동 또는 식단 관련 질문",
        examples=["체중 감량을 위한 일주일 운동 루틴을 알려줘"],
    )


class PlanResponse(BaseModel):
    intent: str | None = Field(None, description="파악된 의도 (운동/식단)")
    confidence: float | None = Field(None, description="의도 파악 확신도")
    final_plan: str | None = Field(None, description="최종 승인된 맞춤형 플랜")
    error_message: str | None = Field(None, description="재질문 요청 시 안내 메시지")
    is_safe: bool | None = Field(None, description="플랜 안전성 평가 결과")


# ── 엔드포인트 ────────────────────────────────────────────────────────────────

@router.post(
    "/health-plan",
    response_model=PlanResponse,
    summary="맞춤형 헬스 플랜 생성",
    description=(
        "사용자의 운동 또는 식단 관련 질문을 입력하면 "
        "LangGraph 파이프라인을 통해 맞춤형 플랜을 생성합니다."
    ),
)
async def generate_health_plan(request: PlanRequest) -> PlanResponse:
    """
    LangGraph 파이프라인 실행 흐름:
      Super Agent → (Expert) → Plan Draft → Evaluator → [Reask or END]
    """
    # 초기 상태 구성: user_input만 주입하고 나머지는 None으로 초기화
    initial_state = {
        "user_input": request.user_input,
        "intent": None,
        "confidence": None,
        "expert_advice": None,
        "draft_plan": None,
        "is_safe": None,
        "final_plan": None,
        "error_message": None,
    }

    try:
        # 그래프 동기 실행 (비동기 환경에서는 ainvoke 사용 가능)
        result = await graph.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파이프라인 실행 오류: {str(e)}")

    return PlanResponse(
        intent=result.get("intent"),
        confidence=result.get("confidence"),
        final_plan=result.get("final_plan"),
        error_message=result.get("error_message"),
        is_safe=result.get("is_safe"),
    )


@router.get("/health", summary="서버 상태 확인")
async def health_check():
    """서버 및 파이프라인 로드 상태를 확인한다."""
    return {"status": "ok", "pipeline": "loaded"}
