"""Intent analysis node for Layer 2 routing."""
from __future__ import annotations

import logging
import re

from app.core.prompt_loader import load_prompt
from app.graph.deps import NodeDeps
from app.schemas.intent import IntentOutput
from app.schemas.state import GraphState

logger = logging.getLogger(__name__)

INTENT_CARE = "공감_케어"
INTENT_PLAN = "계획"
INTENT_FALLBACK = "fallback"
INTENT_CASUAL = "casual"
INTENT_SAFETY = "안전경고"
INTENT_HOME_RECOMMENDATION = "home_recommendation"

_SAFETY_PATTERNS = re.compile(
    r"자해|자살|죽고\s*싶|극단적\s*선택|위험|폭행|마약|과다\s*복용",
    re.IGNORECASE,
)

_CASUAL_PATTERNS = re.compile(
    r"^(안녕|하이|헬로|hello|hi|반가워|고마워|감사|굿굿|수고|바이|bye)[\s!?.]*$",
    re.IGNORECASE,
)

_INTENT_SYSTEM_PROMPT = load_prompt("nodes/intent/system.md")


def make_intent_node(deps: NodeDeps):
    async def analyze_intent_node(state: GraphState) -> dict:
        if state.get("request_kind") == "home_recommendation":
            return _build_result(INTENT_HOME_RECOMMENDATION, state)

        message = state["user_message"]

        if _SAFETY_PATTERNS.search(message):
            return _build_result(INTENT_SAFETY, state)

        previous_intent = state.get("previous_intent")
        if _CASUAL_PATTERNS.match(message.strip()) and previous_intent != INTENT_CARE:
            return _build_result(INTENT_CASUAL, state)

        # Generic workout and diet recommendation requests were frequently
        # misclassified as fallback or record. Route them to plan/search first.
        if _looks_like_plan_request(message):
            return _build_result(
                INTENT_PLAN,
                state,
                confidence=0.92,
                search_targets=["vdb_external", "vdb_user_important", "web"],
            )

        context = _build_context(state)
        user_content = f"{context}\n\n현재 메시지: {message}" if context else f"현재 메시지: {message}"

        try:
            raw = await deps.router.generate(
                system_prompt=_INTENT_SYSTEM_PROMPT,
                user_content=user_content,
                response_schema=IntentOutput,
            )
            output = IntentOutput.model_validate_json(raw)
        except Exception as exc:
            logger.warning("Intent analysis failed, using fallback: %s", exc)
            return _build_result(INTENT_FALLBACK, state)

        profile_changes_dict = None
        if output.profile_changes:
            profile_changes_dict = {item.field: item.value for item in output.profile_changes}

        return {
            "intent": output.intent,
            "confidence": output.confidence,
            "emotion": {
                "label": output.emotion.label,
                "intensity": output.emotion.intensity,
            },
            "previous_intent": state.get("intent"),
            "previous_emotion": state.get("emotion"),
            "requires_past_memory": output.requires_past_memory,
            "should_save_episode": output.should_save_episode,
            "has_fact_change": output.has_fact_change,
            "record_type": output.record_type,
            "profile_changes": profile_changes_dict,
            "is_today": output.is_today,
            "modify_target": output.modify_target,
            "search_targets": output.search_targets,
            "search_retry_count": 0,
            "fallback_count": state.get("fallback_count", 0),
            "self_eval_count": 0,
        }

    return analyze_intent_node


def _build_result(
    intent: str,
    state: GraphState,
    *,
    confidence: float = 1.0,
    search_targets: list[str] | None = None,
) -> dict:
    return {
        "intent": intent,
        "confidence": confidence,
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
        "search_targets": search_targets or [],
        "search_retry_count": 0,
        "fallback_count": state.get("fallback_count", 0),
        "self_eval_count": 0,
    }


def _build_context(state: GraphState) -> str:
    parts: list[str] = []

    if state.get("previous_intent"):
        parts.append(f"이전 의도: {state['previous_intent']}")

    if state.get("previous_emotion"):
        emotion = state["previous_emotion"]
        parts.append(f"이전 감정: {emotion['label']} (강도 {emotion['intensity']:.1f})")

    if state.get("summary"):
        parts.append(f"대화 요약: {state['summary']}")

    return "\n".join(parts)


def _looks_like_plan_request(message: str) -> bool:
    normalized = message.strip().lower()

    domain_keywords = (
        "운동",
        "식단",
        "식사",
        "메뉴",
        "루틴",
        "플랜",
        "계획",
        "workout",
        "diet",
        "meal",
    )
    request_keywords = (
        "추천",
        "루틴",
        "플랜",
        "계획",
        "짜줘",
        "구성",
        "알려줘",
        "만들어",
        "추천해줘",
        "정리해줘",
    )
    exclude_keywords = (
        "수정",
        "바꿔",
        "변경",
        "교체",
        "확정",
        "승인",
        "체크",
        "기록",
    )

    has_domain_keyword = any(keyword in normalized for keyword in domain_keywords)
    has_request_keyword = any(keyword in normalized for keyword in request_keywords)
    has_excluded_keyword = any(keyword in normalized for keyword in exclude_keywords)

    return has_domain_keyword and has_request_keyword and not has_excluded_keyword
