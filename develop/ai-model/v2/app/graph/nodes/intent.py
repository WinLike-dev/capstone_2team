"""Intent analysis node for Layer 2 routing."""
from __future__ import annotations

import logging
import re

from pydantic import BaseModel, Field

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

_PLAN_CONFIRMATION_SYSTEM_PROMPT = """You are a narrow classifier for plan confirmation in a health coaching chat.

Decide only whether the user's latest message approves the already proposed plan.

Return approved=true only when all of these are true:
- The assistant previously proposed or modified a plan and is waiting for confirmation.
- The user is accepting, confirming, applying, or proceeding with that existing plan.
- The user is not introducing any new change request, constraint, or modification.

Return approved=false when any of these are true:
- The user requests a new change, replacement, deletion, addition, or adjustment.
- The user asks a new question or goes off topic.
- The user expresses dislike/rejection without clearly approving the current plan.
- The message is ambiguous.
"""


class PlanConfirmationDecision(BaseModel):
    approved: bool = Field(description="Whether the user approved the currently proposed plan")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str = Field(default="")

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
    "저장해",
)
_APPROVAL_COMMITMENT_KEYWORDS = (
    "?뱀씤",
    "?뺤젙",
    "諛섏쁺",
    "?곸슜",
    "吏꾪뻾",
    "洹몃?濡",
    "醫뗭븘",
    "醫뗭뒿?덈떎",
    "?ㅼ???",
    "ok",
    "okay",
)
_EXPLICIT_PLAN_APPROVAL_PHRASES = (
    "좋아요",
    "좋습니다",
    "진행해줘",
    "진행해 줘",
    "반영해줘",
    "반영해 줘",
    "적용해줘",
    "적용해 줘",
    "그대로 적용해줘",
    "그대로 적용해 줘",
    "이 계획으로 진행해줘",
    "이 계획으로 진행해 줘",
    "일정에 반영해줘",
    "일정에 반영해 줘",
    "확정하고 반영해줘",
    "확정하고 반영해 줘",
    "확인했어",
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
_CONTEXT_DEPENDENT_REFERENCES = (
    "그거",
    "그걸",
    "이거",
    "이걸",
    "아까 말한 거",
    "그 방식",
    "저 방식",
    "방금 거",
    "저거",
)


_PLAN_CONFIRMATION_REFERENCE_KEYWORDS = (
    "아까",
    "방금",
    "그전",
    "그 전에",
    "이전",
    "그거",
    "그걸",
    "그 계획",
    "그 운동",
    "그 식단",
    "그대로",
)

_PLAN_CHANGE_MARKERS = (
    "말고",
    "대신",
    "바꿔",
    "변경",
    "조정",
    "낮춰",
    "높여",
    "줄여",
    "늘려",
    "빼고",
    "빼줘",
    "추가",
    "추가해",
    "제외",
    "강도",
    "세트",
    "횟수",
    "시간",
    "칼로리",
    "아침",
    "점심",
    "저녁",
)

_SHORT_APPROVAL_RESPONSES = (
    "응",
    "네",
    "좋아",
    "좋아요",
    "좋습니다",
    "오케이",
    "okay",
    "ok",
)

_HARDCODED_CONFIRMATION_APPROVAL_PHRASES = (
    "좋아요. 방금 수정한 계획으로 진행해줘.",
    "좋아요 방금 수정한 계획으로 진행해줘",
    "수정된 계획 확인했어. 그대로 적용해줘.",
    "수정된 계획 확인했어 그대로 적용해줘",
    "수정한 계획으로 진행해줘",
    "수정된 계획 그대로 적용해줘",
    "수정된 계획 반영해줘",
    "방금 수정한 계획으로 진행해줘",
    "방금 수정한 계획 적용해줘",
    "방금 수정한 계획 반영해줘",
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

        if _looks_like_context_dependent_fallback(message, state):
            return _build_result(INTENT_FALLBACK, state, confidence=0.9)

        awaiting_plan_confirmation = _has_pending_plan_confirmation_v2(state)
        if awaiting_plan_confirmation:
            deps.trace.record_current_event(
                stage="confirm_gate",
                status="info",
                title="Plan confirmation gate entered",
                detail={
                    "awaiting_plan_confirmation": True,
                    "has_proposed_plan": bool(state.get("proposed_plan")),
                    "proposed_plan_count": len(state.get("proposed_plan") or []),
                    "proposed_plan_type": state.get("proposed_plan_type"),
                    "proposed_plan_action": state.get("proposed_plan_action"),
                    "last_assistant_excerpt": _latest_assistant_message_v2(state)[:200],
                    "user_message": message,
                },
            )

        if awaiting_plan_confirmation and _matches_hardcoded_confirmation_approval(message):
            deps.trace.record_current_event(
                stage="confirm_gate",
                status="ok",
                title="Hardcoded confirmation approval matched",
                detail={
                    "source": "hardcoded_phrase",
                    "user_message": message,
                },
            )
            return _build_result(INTENT_APPROVAL, state, confidence=0.99)

        if awaiting_plan_confirmation:
            decision = await _classify_plan_confirmation(deps, state, message)
            if decision is not None and decision.approved:
                return _build_result(
                    INTENT_APPROVAL,
                    state,
                    confidence=max(0.9, float(decision.confidence or 0.0)),
                )
            deps.trace.record_current_event(
                stage="confirm_gate",
                status="warn",
                title="Confirmation gate fell through to general routing",
                detail={
                    "user_message": message,
                    "decision_present": decision is not None,
                    "approved": bool(decision.approved) if decision is not None else None,
                    "confidence": float(decision.confidence or 0.0) if decision is not None else None,
                    "reason": decision.reason if decision is not None else "no_decision",
                },
            )

        if not awaiting_plan_confirmation and _looks_like_plan_approval(message, state):
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

        context = _build_context_v3(state)
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


def _latest_assistant_message(state: GraphState) -> str:
    messages = state.get("messages") or []
    for message in reversed(messages):
        if message.get("role") == "assistant":
            return str(message.get("content") or "")
    return ""


def _latest_assistant_message_v2(state: GraphState) -> str:
    if state.get("last_assistant_message"):
        return str(state.get("last_assistant_message") or "")
    return _latest_assistant_message(state)


def _build_context_v3(state: GraphState) -> str:
    parts: list[str] = []

    if state.get("previous_intent"):
        parts.append(f"이전 의도: {state['previous_intent']}")

    if state.get("previous_emotion"):
        emotion = state["previous_emotion"]
        parts.append(f"이전 감정: {emotion['label']} (강도 {emotion['intensity']:.1f})")

    if state.get("summary"):
        parts.append(f"대화 요약: {state['summary']}")

    latest_assistant = _latest_assistant_message_v2(state)
    if latest_assistant:
        parts.append(f"직전 AI 응답: {latest_assistant[:200]}")

    return "\n".join(parts)


def _has_pending_plan_confirmation_v2(state: GraphState) -> bool:
    return bool(state.get("awaiting_plan_confirmation")) and bool(state.get("proposed_plan"))


def _matches_hardcoded_confirmation_approval(message: str) -> bool:
    normalized = re.sub(r"\s+", " ", message.strip().lower())
    if not normalized:
        return False

    if normalized in {
        phrase.lower() for phrase in _HARDCODED_CONFIRMATION_APPROVAL_PHRASES
    }:
        return True

    has_modified_plan_reference = any(
        phrase in normalized
        for phrase in (
            "수정된 계획",
            "수정한 계획",
            "방금 수정한 계획",
        )
    )
    has_apply_verb = any(
        phrase in normalized
        for phrase in (
            "진행해줘",
            "진행해 줘",
            "적용해줘",
            "적용해 줘",
            "반영해줘",
            "반영해 줘",
        )
    )
    has_acceptance_prefix = normalized.startswith("좋아요") or normalized.startswith("좋습니다")
    if has_modified_plan_reference and has_apply_verb:
        return True
    if "그대로" in normalized and has_apply_verb and "계획 확인" in normalized:
        return True
    if has_acceptance_prefix and has_modified_plan_reference and has_apply_verb:
        return True
    return False


async def _classify_plan_confirmation(
    deps: NodeDeps,
    state: GraphState,
    message: str,
) -> PlanConfirmationDecision | None:
    latest_assistant = _latest_assistant_message_v2(state)
    proposed_plan = state.get("proposed_plan") or []
    proposed_plan_type = state.get("proposed_plan_type") or ""
    proposed_plan_action = state.get("proposed_plan_action") or ""
    user_content = (
        "[Assistant Plan Response]\n"
        f"{latest_assistant[:800]}\n\n"
        "[Proposed Plan Meta]\n"
        f"plan_type={proposed_plan_type}\n"
        f"plan_action={proposed_plan_action}\n"
        f"item_count={len(proposed_plan)}\n\n"
        "[User Message]\n"
        f"{message}"
    )

    try:
        raw = await deps.router.generate(
            system_prompt=_PLAN_CONFIRMATION_SYSTEM_PROMPT,
            user_content=user_content,
            response_schema=PlanConfirmationDecision,
        )
        decision = PlanConfirmationDecision.model_validate_json(raw)
        deps.trace.record_current_event(
            stage="confirm_gate",
            status="ok" if decision.approved else "warn",
            title="LLM confirmation decision",
            detail={
                "approved": decision.approved,
                "confidence": decision.confidence,
                "reason": decision.reason,
                "user_message": message,
                "last_assistant_excerpt": latest_assistant[:200],
                "proposed_plan_count": len(proposed_plan),
                "proposed_plan_type": proposed_plan_type,
                "proposed_plan_action": proposed_plan_action,
            },
        )
        return decision
    except Exception as exc:
        logger.warning("Plan confirmation classification failed, falling back: %s", exc)
        deps.trace.record_current_alert(
            severity="warning",
            message="Plan confirmation classification failed",
            detail={
                "error": str(exc),
                "user_message": message,
            },
        )
        if _looks_like_plan_approval(message, state) or _looks_like_plan_acceptance_followup(message, state):
            deps.trace.record_current_event(
                stage="confirm_gate",
                status="ok",
                title="Heuristic confirmation fallback approved",
                detail={
                    "reason": "heuristic_fallback",
                    "user_message": message,
                },
            )
            return PlanConfirmationDecision(approved=True, confidence=0.9, reason="heuristic_fallback")
        return None


def _build_context_v2(state: GraphState) -> str:
    parts: list[str] = []

    if state.get("previous_intent"):
        parts.append(f"이전 의도: {state['previous_intent']}")

    if state.get("previous_emotion"):
        emotion = state["previous_emotion"]
        parts.append(f"이전 감정: {emotion['label']} (강도 {emotion['intensity']:.1f})")

    if state.get("summary"):
        parts.append(f"대화 요약: {state['summary']}")

    latest_assistant = _latest_assistant_message_v2(state)
    if latest_assistant:
        parts.append(f"직전 AI 응답: {latest_assistant[:200]}")

    return "\n".join(parts)


def _has_pending_plan_confirmation(state: GraphState) -> bool:
    return _has_pending_plan_confirmation_v2(state)


def _has_recent_plan_intent(state: GraphState) -> bool:
    return state.get("intent") in {
        INTENT_PLAN,
        INTENT_MODIFY,
        INTENT_APPROVAL,
    } or state.get("previous_intent") in {
        INTENT_PLAN,
        INTENT_MODIFY,
        INTENT_APPROVAL,
    }


def _looks_like_explicit_plan_change(message: str, state: GraphState) -> bool:
    normalized = message.strip().lower()
    if not normalized or not _has_pending_plan_confirmation_v2(state):
        return False

    has_change_marker = any(marker in normalized for marker in _PLAN_CHANGE_MARKERS)
    has_modify_keyword = any(keyword in normalized for keyword in _MODIFY_KEYWORDS)
    has_contrast_marker = any(marker in normalized for marker in ("말고", "대신", "빼고"))
    has_commitment_keyword = any(
        keyword in normalized for keyword in _APPROVAL_COMMITMENT_KEYWORDS
    )
    has_confirmation_reference = any(
        keyword in normalized for keyword in _PLAN_CONFIRMATION_REFERENCE_KEYWORDS
    )
    looks_like_referential_acceptance = has_confirmation_reference and has_commitment_keyword

    if has_modify_keyword and not looks_like_referential_acceptance:
        return True
    if has_change_marker and (has_contrast_marker or not looks_like_referential_acceptance):
        return True
    return False


def _looks_like_plan_acceptance_followup(message: str, state: GraphState) -> bool:
    normalized = message.strip().lower()
    if not normalized or not _has_pending_plan_confirmation_v2(state):
        return False
    if _looks_like_explicit_plan_change(message, state):
        return False
    if _looks_like_profile_record(message):
        return False
    if _SAFETY_PATTERNS.search(message):
        return False

    is_short_ack = normalized in {item.lower() for item in _SHORT_APPROVAL_RESPONSES}
    has_commitment_keyword = any(
        keyword in normalized for keyword in _APPROVAL_COMMITMENT_KEYWORDS
    )
    has_reference = any(
        keyword in normalized
        for keyword in (
            *_PLAN_REFERENCE_KEYWORDS,
            *_PLAN_CONFIRMATION_REFERENCE_KEYWORDS,
        )
    )
    latest_assistant = _latest_assistant_message_v2(state).lower()
    assistant_requested_confirmation = _assistant_requested_plan_confirmation(state)
    message_is_question = "?" in normalized or normalized.endswith("까") or normalized.endswith("나요")
    appears_off_topic = (
        not has_reference
        and not has_commitment_keyword
        and not any(keyword in latest_assistant for keyword in _PLAN_REFERENCE_KEYWORDS)
    )

    if message_is_question or appears_off_topic:
        return False
    if is_short_ack:
        return True
    return has_commitment_keyword or (assistant_requested_confirmation and has_reference)


def _assistant_requested_plan_confirmation(state: GraphState) -> bool:
    latest_assistant = _latest_assistant_message_v2(state).lower()
    if not latest_assistant:
        return False

    has_plan_reference = any(
        keyword in latest_assistant for keyword in _PLAN_REFERENCE_KEYWORDS
    )
    has_confirmation_prompt = any(
        keyword in latest_assistant for keyword in _APPROVAL_KEYWORDS
    ) or "吏꾪뻾 ?щ?" in latest_assistant

    return has_plan_reference and has_confirmation_prompt


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
    has_commitment_keyword = any(
        keyword in normalized for keyword in _APPROVAL_COMMITMENT_KEYWORDS
    )
    has_explicit_approval_phrase = any(
        phrase in normalized for phrase in _EXPLICIT_PLAN_APPROVAL_PHRASES
    )
    has_plan_reference = any(keyword in normalized for keyword in _PLAN_REFERENCE_KEYWORDS)
    has_confirmation_reference = any(
        keyword in normalized for keyword in _PLAN_CONFIRMATION_REFERENCE_KEYWORDS
    )
    has_modify_keyword = any(keyword in normalized for keyword in _MODIFY_KEYWORDS)
    has_profile_keyword = any(keyword in normalized for keyword in _PROFILE_FIELD_KEYWORDS)
    has_plan_context = (
        _has_pending_plan_confirmation_v2(state)
        or bool(state.get("proposed_plan"))
        or _has_recent_plan_intent(state)
        or _assistant_requested_plan_confirmation(state)
    )
    if has_plan_context and has_explicit_approval_phrase and not has_profile_keyword:
        return True
    if (
        has_plan_context
        and has_confirmation_reference
        and has_commitment_keyword
        and not has_profile_keyword
        and not _looks_like_explicit_plan_change(message, state)
    ):
        return True
    if not has_approval_keyword:
        return False
    if not (has_plan_reference or has_plan_context):
        return False
    if has_profile_keyword:
        return False
    if has_modify_keyword and not (has_plan_context and has_commitment_keyword):
        return False
    return True


def _looks_like_profile_record(message: str) -> bool:
    normalized = message.strip().lower()
    has_profile_field = any(keyword in normalized for keyword in _PROFILE_FIELD_KEYWORDS)
    has_update_keyword = any(keyword in normalized for keyword in _PROFILE_UPDATE_KEYWORDS)
    has_plan_domain = any(keyword in normalized for keyword in ("운동 계획", "식단 계획", "운동 루틴", "식단 루틴"))
    return has_profile_field and has_update_keyword and not has_plan_domain


def _looks_like_context_dependent_fallback(message: str, state: GraphState) -> bool:
    normalized = message.strip().lower()
    has_reference = any(keyword in normalized for keyword in _CONTEXT_DEPENDENT_REFERENCES)
    has_plan_context = (
        _has_pending_plan_confirmation_v2(state)
        or bool(state.get("proposed_plan"))
        or _has_recent_plan_intent(state)
        or state.get("intent") in {INTENT_INFO, INTENT_RECORD}
        or state.get("previous_intent") in {INTENT_INFO, INTENT_RECORD}
    )
    return has_reference and not has_plan_context
