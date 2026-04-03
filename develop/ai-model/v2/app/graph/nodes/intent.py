"""의도 분석 노드 — Layer 2 구현.

1단계: 규칙 기반 사전 필터
  - 금칙어 매칭 → is_safety
  - 인사 패턴 매칭 → is_casual (단, previous_intent가 공감_케어면 스킵)

2단계: Flash-Lite 정밀 분석
  - intent / confidence / emotion
  - has_fact_change / requires_past_memory
  - 의도별 조건부 속성
"""
from __future__ import annotations

import json
import logging
import re

from app.graph.deps import NodeDeps
from app.schemas.intent import IntentOutput
from app.schemas.state import GraphState

logger = logging.getLogger(__name__)

# ── 규칙 기반 패턴 ────────────────────────────────────────────────────────────

_SAFETY_PATTERNS = re.compile(
    r"자살|자해|죽고싶|죽겠|극단적\s*선택|학대|폭행|마약|약물\s*남용",
    re.IGNORECASE,
)

_CASUAL_PATTERNS = re.compile(
    r"^(안녕|ㅎㅇ|하이|헬로|hi|hello|반가워|방가|ㅋ+|ㅎ+|감사|고마워|고맙|잘있어|잘가|바이|bye)[\s!?.]*$",
    re.IGNORECASE,
)

_INTENT_SYSTEM_PROMPT = """
당신은 헬스 AI 챗봇의 의도 분석 전문가입니다.
사용자 메시지를 분석하여 정확한 의도와 감정을 JSON으로 반환하세요.

의도 분류:
- 공감_케어: 감정 표현, 힘들다, 고민, 스트레스, 위로가 필요한 경우
- 기록: 오늘 운동/식단 완료 기록, 체중/키 등 프로필 변경
- 계획: 운동/식단 계획 생성 요청
- 수정: 기존 운동/식단 계획 수정 요청
- 정보: 운동 방법, 영양, 건강 정보 질문
- 안전경고: 위험한 행동, 자해, 극단적 다이어트 등
- fallback: 위 어느 것에도 해당하지 않거나 불명확한 경우

search_targets 선택:
- 공감_케어 (requires_past_memory=true): ["vdb_memory"]
- 계획: ["vdb_external", "vdb_user_important"]
- 수정: ["vdb_external"]
- 정보: ["vdb_external"]
- 기록/공감_케어(false)/fallback: []
"""


def make_intent_node(deps: NodeDeps):
    async def analyze_intent_node(state: GraphState) -> dict:
        message = state["user_message"]

        # ── 1단계: 규칙 기반 필터 ────────────────────────────────────────────
        if _SAFETY_PATTERNS.search(message):
            return _build_result("안전경고", state)

        prev_intent = state.get("previous_intent")
        if _CASUAL_PATTERNS.match(message.strip()) and prev_intent != "공감_케어":
            return _build_result("casual", state)

        # ── 2단계: Flash-Lite 정밀 분석 ──────────────────────────────────────
        context = _build_context(state)
        try:
            raw = await deps.router.generate(
                system_prompt=_INTENT_SYSTEM_PROMPT,
                user_content=f"{context}\n\n현재 메시지: {message}",
                response_schema=IntentOutput,
            )
            output = IntentOutput.model_validate_json(raw)
        except Exception as e:
            logger.warning("의도 분석 실패, fallback 적용: %s", e)
            return _build_result("fallback", state)

        return {
            "intent": output.intent,
            "confidence": output.confidence,
            "emotion": {"label": output.emotion.label, "intensity": output.emotion.intensity},
            "previous_intent": state.get("intent"),
            "previous_emotion": state.get("emotion"),
            "requires_past_memory": output.requires_past_memory,
            "should_save_episode": output.should_save_episode,
            "has_fact_change": output.has_fact_change,
            "record_type": output.record_type,
            "profile_changes": output.profile_changes,
            "is_today": output.is_today,
            "modify_target": output.modify_target,
            "search_targets": output.search_targets,
            "search_retry_count": 0,
            "fallback_count": state.get("fallback_count", 0),
            "self_eval_count": 0,
        }

    return analyze_intent_node


def _build_result(intent: str, state: GraphState) -> dict:
    return {
        "intent": intent,
        "confidence": 1.0,
        "emotion": state.get("emotion") or {"label": "중립", "intensity": 0.0},
        "previous_intent": state.get("intent"),
        "previous_emotion": state.get("emotion"),
        "requires_past_memory": False,
        "should_save_episode": False,
        "has_fact_change": False,
        "record_type": None,
        "profile_changes": None,
        "is_today": None,
        "modify_target": None,
        "search_targets": [],
        "search_retry_count": 0,
        "self_eval_count": 0,
    }


def _build_context(state: GraphState) -> str:
    parts = []
    if state.get("previous_intent"):
        parts.append(f"이전 의도: {state['previous_intent']}")
    if state.get("previous_emotion"):
        em = state["previous_emotion"]
        parts.append(f"이전 감정: {em['label']} (강도 {em['intensity']:.1f})")
    if state.get("summary"):
        parts.append(f"대화 요약: {state['summary']}")
    return "\n".join(parts) if parts else ""
