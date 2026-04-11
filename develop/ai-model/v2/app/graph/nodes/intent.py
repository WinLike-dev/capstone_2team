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
INTENT_FALLBACK = "fallback"
INTENT_CASUAL = "casual"
INTENT_SAFETY = "안전경고"
INTENT_HOME_RECOMMENDATION = "home_recommendation"

_SAFETY_PATTERNS = re.compile(
    r"자해|자살|죽고\s*싶|극단적\s*선택|위험|폭행|마약|과다\s*복용",
    re.IGNORECASE,
)

_CASUAL_PATTERNS = re.compile(
    r"^(안녕|하이|헬로|hello|hi|반가워|고마워|감사|굿밤|잘자|바이|bye)[\s!?.]*$",
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
