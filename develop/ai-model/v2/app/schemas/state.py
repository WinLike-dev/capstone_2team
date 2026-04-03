"""LangGraph GraphState — 전체 대화 State 정의.

Layer 4 데이터 흐름 기반:
  - user_profile / today_plan: WAS에서 로드한 세션 캐시
  - emotion / intent: 의도 분석 결과
  - search_results / search_quality: 검색 파이프라인 결과
  - pending_writes: WAS 쓰기 실패 큐
  - messages: 최근 N턴 대화 기록
"""
from __future__ import annotations

from typing import Annotated, Any, Optional

from typing_extensions import TypedDict

from app.core.config import get_settings

# ---------------------------------------------------------------------------
# 메시지 리듀서: 최근 MAX_MESSAGES 개만 유지
# ---------------------------------------------------------------------------

def _append_messages(existing: list[dict], new: list[dict] | dict) -> list[dict]:
    if isinstance(new, dict):
        new = [new]
    combined = existing + new
    max_n = get_settings().MAX_MESSAGES
    return combined[-max_n:]


# ---------------------------------------------------------------------------
# 서브 타입
# ---------------------------------------------------------------------------

class EmotionState(TypedDict):
    label: str       # 예: "슬픔", "기쁨", "불안", "중립"
    intensity: float  # 0.0 ~ 1.0


class PendingWrite(TypedDict):
    """WAS 쓰기 실패 시 다음 턴 재시도용 큐 항목."""
    write_type: str   # "profile" | "plan_check" | "plan_create" | "plan_update"
    payload: dict[str, Any]


# ---------------------------------------------------------------------------
# GraphState
# ---------------------------------------------------------------------------

class GraphState(TypedDict):
    # ── 요청 컨텍스트 ────────────────────────────────────────────────────────
    user_id: str
    user_message: str

    # ── 세션 캐시 (WAS에서 첫 턴에 로드) ───────────────────────────────────
    user_profile: Optional[dict[str, Any]]
    today_plan: Optional[list[dict[str, Any]]]

    # ── 턴 추적 ──────────────────────────────────────────────────────────────
    turn_count: int
    is_session_start: bool

    # ── 의도 분석 결과 ────────────────────────────────────────────────────────
    intent: str                           # 공감_케어|기록|계획|수정|정보|안전경고|fallback|casual
    confidence: float
    emotion: Optional[EmotionState]
    previous_intent: Optional[str]
    previous_emotion: Optional[EmotionState]

    # ── 의도별 조건부 속성 ────────────────────────────────────────────────────
    requires_past_memory: bool
    should_save_episode: bool
    has_fact_change: bool
    record_type: Optional[str]            # "profile" | "plan_check"
    profile_changes: Optional[dict[str, Any]]
    is_today: Optional[bool]
    modify_target: Optional[str]          # "workout" | "diet"
    search_targets: list[str]             # ["vdb_memory", "vdb_user_important", "vdb_external", "web"]
    modify_plan_context: Optional[dict[str, Any]]  # 수정 의도 전체 플랜 (transient)

    # ── 검색 파이프라인 ───────────────────────────────────────────────────────
    search_results: list[dict[str, Any]]
    search_quality: str                   # "ok" | "degraded"
    search_retry_count: int
    search_query: Optional[str]           # 재생성된 검색 쿼리

    # ── WAS 쓰기 큐 ──────────────────────────────────────────────────────────
    pending_writes: list[PendingWrite]

    # ── 응답 생성 ─────────────────────────────────────────────────────────────
    response: Optional[str]
    self_eval_count: int
    self_eval_failure_reason: Optional[str]

    # ── Fallback ─────────────────────────────────────────────────────────────
    fallback_count: int
    needs_clarification: bool

    # ── 대화 이력 ─────────────────────────────────────────────────────────────
    summary: Optional[str]
    messages: Annotated[list[dict[str, Any]], _append_messages]
