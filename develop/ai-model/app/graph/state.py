"""
헬스 메이트 - LangGraph StateGraph 공유 상태(State) 정의

모든 노드는 이 TypedDict를 입력으로 받고,
변경할 필드만 dict로 반환하여 상태를 업데이트한다.
"""
from typing import Optional
from typing_extensions import TypedDict


class HealthMateState(TypedDict):
    # ── 입력 ──────────────────────────────────────────
    user_input: str             # 사용자 원문 입력

    # ── Super Agent 출력 ───────────────────────────────
    intent: Optional[str]       # '운동' 또는 '식단'
    confidence: Optional[float] # 의도 확신도 (0.0 ~ 1.0)

    # ── 전문가 노드 출력 ────────────────────────────────
    expert_advice: Optional[str]  # 운동 or 식단 전문가 조언

    # ── 플랜 초안 생성 출력 ─────────────────────────────
    draft_plan: Optional[str]   # 생성된 플랜 초안

    # ── 최종 답변 평가 출력 ─────────────────────────────
    is_safe: Optional[bool]     # 평가 통과 여부 (True=PASS / False=FAIL)

    # ── 최종 출력 ──────────────────────────────────────
    final_plan: Optional[str]   # 최종 승인된 맞춤형 플랜
    error_message: Optional[str] # 재질문 안내 메시지
