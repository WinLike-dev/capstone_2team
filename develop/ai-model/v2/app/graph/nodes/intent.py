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
INTENT_MODIFY = "수정"
INTENT_APPROVAL = "계획_승인"
INTENT_RECORD = "기록"
INTENT_INFO = "정보"
INTENT_FALLBACK = "fallback"
INTENT_CASUAL = "casual"
INTENT_SAFETY = "안전경고"
INTENT_HOME_RECOMMENDATION = "home_recommendation"

_SAFETY_PATTERNS = re.compile(
    r"자해|자살|죽고\s*싶|극단적\s*선택|위험|폭행|마약|과다\s*복용|"
    r"가슴.*조여|숨이?\s*차|호흡.*힘들|어지럽|쓰러질\s*것\s*같|실신|기절",
    re.IGNORECASE,
)

_CASUAL_PATTERNS = re.compile(
    r"^(안녕|하이|헬로|hello|hi|반가워|고마워|감사|굿밤|수고|바이|bye)[\s!?.]*$",
    re.IGNORECASE,
)

_INTENT_SYSTEM_PROMPT = load_prompt("nodes/intent/system.md")

_PLAN_DOMAIN_KEYWORDS = (
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
_PLAN_REQUEST_KEYWORDS = (
    "추천",
    "루틴",
    "플랜",
    "짜줘",
    "짤",
    "구성",
    "설계",
    "만들어",
    "추천해줘",
    "정리해줘",
    "제안",
)
_PLAN_EXCLUDE_KEYWORDS = (
    "수정",
    "바꿔",
    "변경",
    "교체",
    "조정",
    "낮춰",
    "높여",
    "승인",
    "확정",
    "반영",
    "적용",
    "진행",
    "기록",
    "추가",
    "삭제",
)
_MODIFY_KEYWORDS = (
    "수정",
    "바꿔",
    "변경",
    "교체",
    "조정",
    "낮춰",
    "높여",
    "다시",
    "줄여",
    "늘려",
    "빼고",
)
_APPROVAL_KEYWORDS = (
    "승인",
    "확정",
    "반영",
    "적용",
    "진행해",
    "진행하자",
    "이대로",
    "그대로",
    "오케이",
    "좋아",
    "좋습니다",
    "해줘",
)
_PLAN_REFERENCE_KEYWORDS = (
    "계획",
    "플랜",
    "루틴",
    "식단",
    "운동",
    "방금",
    "제안",
    "추천안",
    "수정안",
    "그거",
    "그걸",
    "이거",
    "이걸",
)
_PROFILE_FIELD_KEYWORDS = (
    "체중",
    "몸무게",
    "키",
    "알레르기",
    "부상",
    "부상 이력",
    "기저질환",
    "질환",
    "질병",
    "나이",
    "성별",
    "목표",
    "활동량",
)
_PROFILE_UPDATE_KEYWORDS = (
    "기록",
    "추가",
    "수정",
    "변경",
    "반영",
    "저장",
    "업데이트",
    "입력",
)


def make_intent_node(deps: NodeDeps):
    async def analyze_intent_node(state: GraphState) -> dict:
        if state.get("request_kind") == "home_recommendation":
            return _build_result(INTENT_HOME_RECOMMENDATION, state)

        message = state["user_message"]
        previous_intent = state.get("previous_intent")

        if _SAFETY_PATTERNS.search(message):
            return _build_result(INTENT_SAFETY, state)

        if _CASUAL_PATTERNS.match(message.strip()) and previous_intent != INTENT_CARE:
            return _build_result(INTENT_CASUAL, state)

        if _looks_like_plan_approval(message, state):
            return _build_result(INTENT_APPROVAL, state, confidence=0.94)

        if _looks_like_profile_record(message):
            return _build_result(INTENT_RECORD, state, confidence=0.9)

        if _looks_like_modify_request(message):
            return _build_result(
                INTENT_MODIFY,
                state,
                confidence=0.92,
                search_targets=["vdb_external", "web"],
            )

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
    has_domain_keyword = any(keyword in normalized for keyword in _PLAN_DOMAIN_KEYWORDS)
    has_request_keyword = any(keyword in normalized for keyword in _PLAN_REQUEST_KEYWORDS)
    has_excluded_keyword = any(keyword in normalized for keyword in _PLAN_EXCLUDE_KEYWORDS)
    return has_domain_keyword and has_request_keyword and not has_excluded_keyword


def _looks_like_modify_request(message: str) -> bool:
    normalized = message.strip().lower()
    has_domain_keyword = any(keyword in normalized for keyword in _PLAN_DOMAIN_KEYWORDS)
    has_modify_keyword = any(keyword in normalized for keyword in _MODIFY_KEYWORDS)
    return has_domain_keyword and has_modify_keyword


def _looks_like_plan_approval(message: str, state: GraphState) -> bool:
    normalized = message.strip().lower()
    has_approval_keyword = any(keyword in normalized for keyword in _APPROVAL_KEYWORDS)
    has_plan_reference = any(keyword in normalized for keyword in _PLAN_REFERENCE_KEYWORDS)
    has_modify_keyword = any(keyword in normalized for keyword in _MODIFY_KEYWORDS)
    has_profile_keyword = any(keyword in normalized for keyword in _PROFILE_FIELD_KEYWORDS)
    has_plan_context = bool(state.get("proposed_plan")) or state.get("previous_intent") in {
        INTENT_PLAN,
        INTENT_MODIFY,
        INTENT_APPROVAL,
    }
    return has_approval_keyword and (has_plan_reference or has_plan_context) and not (
        has_modify_keyword or has_profile_keyword
    )


def _looks_like_profile_record(message: str) -> bool:
    normalized = message.strip().lower()
    has_profile_field = any(keyword in normalized for keyword in _PROFILE_FIELD_KEYWORDS)
    has_update_keyword = any(keyword in normalized for keyword in _PROFILE_UPDATE_KEYWORDS)
    has_plan_domain = any(keyword in normalized for keyword in ("운동 계획", "식단 계획", "운동 루틴", "식단 루틴"))
    return has_profile_field and has_update_keyword and not has_plan_domain
