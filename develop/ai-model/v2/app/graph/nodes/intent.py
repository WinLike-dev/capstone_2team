"""Intent analysis node for Layer 2 routing."""
from __future__ import annotations

import logging
import re

from pydantic import BaseModel, Field

from app.core.conversation_state import infer_domain
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
    r"자해|자살|죽고\s*싶|극단적\s*선택|위험|실행|마약|과다\s*복용|과복용|"
    r"가슴.*조여|가슴.*아파|숨.*차|호흡.*힘들|어지럽|심한.*알레르기|기절|"
    r"약을.*많이.*먹|굶는?\s*식단|굶어서|단식.*살|일주일.*[5-9]\s*kg|"
    r"[5-9]\s*kg.*일주일|극단적.*다이어트|초저칼로리",
    re.IGNORECASE,
)
_CASUAL_PATTERNS = re.compile(
    r"^(안녕|하이|헬로|hello|hi|반가워|고마워|감사|수고|잘가|bye)[\s!?.]*$",
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
    "클라이밍",
    "러닝",
    "수영",
    "자전거",
    "걷기",
)
_PLAN_REQUEST_KEYWORDS = (
    "추천",
    "루틴",
    "플랜",
    "계획",
    "짜줘",
    "구성",
    "설계",
    "만들어",
    "추천해줘",
    "정리해줘",
    "제안",
    "뭐 하면",
    "뭐하면",
    "하면 돼",
    "하면 되",
)
_PLAN_EXCLUDE_KEYWORDS = (
    "수정",
    "바꿔",
    "변경",
    "교체",
    "조정",
    "빼",
    "추가",
    "확인",
    "확정",
    "반영",
    "적용",
    "진행",
    "기록",
    "체크",
)
_MODIFY_KEYWORDS = (
    "수정",
    "바꿔",
    "변경",
    "교체",
    "조정",
    "빼",
    "다시",
    "줄여",
    "늘려",
    "덜",
    "추가",
    "제외",
)
_APPROVAL_KEYWORDS = (
    "확인",
    "확정",
    "반영",
    "적용",
    "진행",
    "진행하자",
    "이대로",
    "그대로",
    "좋아",
    "좋습니다",
    "오케이",
)
_APPROVAL_COMMITMENT_KEYWORDS = (
    "진행",
    "적용",
    "반영",
    "해줘",
    "해줘요",
    "오케이",
    "좋아",
    "ok",
    "okay",
)
_EXPLICIT_PLAN_APPROVAL_PHRASES = (
    "좋아 진행해줘",
    "좋아 반영해줘",
    "좋아 적용해줘",
    "그대로 진행해줘",
    "그대로 적용해줘",
    "이 계획으로 진행해줘",
    "이 계획 반영해줘",
    "확정하고 반영해줘",
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
    "추천",
    "수정안",
    "그거",
    "그걸",
    "이거",
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
    "복용약",
    "나이",
    "성별",
    "목표",
    "활동량",
    "mbti",
    "별명",
)
_PROFILE_UPDATE_KEYWORDS = (
    "기록",
    "추가",
    "수정",
    "변경",
    "반영",
    "업데이트",
    "입력",
    "저장",
)
_CONTEXT_DEPENDENT_REFERENCES = (
    "그거",
    "그걸",
    "그걸로",
    "아까 말한 거",
    "그 방식",
    "방금 거",
    "저거",
)
_MEMORY_SAVE_KEYWORDS = (
    "기억해줘",
    "기억해 줘",
    "기억해",
    "잊지마",
    "잊지 마",
    "앞으로 내 별명은",
    "내 별명은",
)
_MEMORY_QUERY_KEYWORDS = (
    "기억나",
    "기억해?",
    "내가 뭐라고 했",
    "방금 내가 말한",
    "아까 내가 말한",
    "내 별명",
    "이전에 말한",
    "조금 전에 말한",
)
_PLAN_CONFIRMATION_REFERENCE_KEYWORDS = (
    "아까",
    "방금",
    "그전",
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
    "빼",
    "줄여",
    "늘려",
    "추가",
    "제외",
    "강도",
    "세트",
    "횟수",
    "시간",
    "칼로리",
    "식사",
    "재료",
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
_CARE_SUPPORT_MARKERS = (
    "지쳐",
    "지쳤",
    "힘들",
    "불안",
    "우울",
    "무기력",
    "걱정",
    "스트레스",
    "멘탈",
    "버겁",
    "외롭",
    "외로워",
    "실패",
    "못 하겠",
    "못하겠",
    "하기 싫",
    "하기싫",
    "망쳐",
    "망했",
    "부담",
    "겁나",
    "조급",
)
_INFO_REQUEST_MARKERS = (
    "왜",
    "이유",
    "근거",
    "알려줘",
    "어떤",
    "뭘",
    "무엇",
    "피해야",
    "괜찮",
    "가능",
    "해야",
    "해도 돼",
    "쉬어야",
    "어떻게",
    "대신",
)


def make_intent_node(deps: NodeDeps):
    async def analyze_intent_node(state: GraphState) -> dict:
        if state.get("request_kind") == "home_recommendation":
            return _build_result(INTENT_HOME_RECOMMENDATION, state)

        message = str(state["user_message"])
        routing_message = _routing_message(state, message)
        previous_intent = state.get("previous_intent")

        if _SAFETY_PATTERNS.search(message):
            return _build_result(INTENT_SAFETY, state)

        if _CASUAL_PATTERNS.match(message.strip()) and previous_intent != INTENT_CARE:
            return _build_result(INTENT_CASUAL, state)

        if _looks_like_memory_save_request(routing_message):
            return _build_result(
                INTENT_CASUAL,
                state,
                confidence=0.9,
                should_save_episode=True,
            )

        if _looks_like_memory_query(routing_message):
            return _build_result(
                INTENT_INFO,
                state,
                confidence=0.92,
                search_targets=[],
                requires_past_memory=False,
                short_term_memory_query=True,
            )

        if _looks_like_context_dependent_fallback(message, state):
            return _build_result(INTENT_FALLBACK, state, confidence=0.9)

        if _looks_like_context_setup(message) and not _looks_like_plan_request(routing_message):
            return _build_result(INTENT_CASUAL, state, confidence=0.82)

        if (
            _looks_like_question_followup(routing_message)
            and not _looks_like_plan_request(routing_message)
            and not _matches_hardcoded_confirmation_approval(message)
        ):
            return _build_result(
                INTENT_INFO,
                state,
                confidence=0.9,
                search_targets=["vdb_external"],
            )

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
                detail={"source": "hardcoded_phrase", "user_message": message},
            )
            return _build_result(INTENT_APPROVAL, state, confidence=0.99)

        if awaiting_plan_confirmation and _looks_like_explicit_plan_change(message, state):
            return _build_result(
                INTENT_MODIFY,
                state,
                confidence=0.93,
                search_targets=["vdb_external", "web"],
            )

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

        if awaiting_plan_confirmation and _looks_like_explicit_plan_change(routing_message, state):
            return _build_result(
                INTENT_MODIFY,
                state,
                confidence=0.93,
                search_targets=["vdb_external", "web"],
            )

        if not awaiting_plan_confirmation and _looks_like_plan_approval(routing_message, state):
            return _build_result(INTENT_APPROVAL, state, confidence=0.94)

        if _looks_like_care_request(routing_message):
            return _build_result(INTENT_CARE, state, confidence=0.88)

        if _looks_like_profile_record(routing_message):
            return _build_result(INTENT_RECORD, state, confidence=0.9)

        if _looks_like_modify_request(routing_message):
            return _build_result(
                INTENT_MODIFY,
                state,
                confidence=0.92,
                search_targets=["vdb_external", "web"],
            )

        if _looks_like_plan_request(routing_message):
            return _build_result(
                INTENT_PLAN,
                state,
                confidence=0.92,
                search_targets=["vdb_external", "vdb_user_important", "web"],
            )

        if _looks_like_info_request(routing_message):
            return _build_result(
                INTENT_INFO,
                state,
                confidence=0.88,
                search_targets=["vdb_external"],
            )

        context = _build_context_v3(state)
        user_content = (
            f"{context}\n\n[Original User Message]\n{message}\n\n[Resolved User Message]\n{routing_message}"
            if context
            else f"[Original User Message]\n{message}\n\n[Resolved User Message]\n{routing_message}"
        )

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
        output_intent = _coerce_llm_intent(output.intent, state, routing_message)

        return {
            "intent": output_intent,
            **_contract_fields(
                output_intent,
                state,
                record_type=output.record_type,
                modify_target=output.modify_target,
                profile_changes=profile_changes_dict,
                routing_message=routing_message,
                emotion_override={
                    "label": output.emotion.label,
                    "intensity": output.emotion.intensity,
                },
            ),
            "confidence": output.confidence,
            "emotion": {
                "label": output.emotion.label,
                "intensity": output.emotion.intensity,
            },
            "previous_intent": state.get("intent"),
            "previous_emotion": state.get("emotion"),
            "requires_past_memory": output.requires_past_memory,
            "should_save_episode": output.should_save_episode,
            "short_term_memory_query": False,
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
    requires_past_memory: bool = False,
    should_save_episode: bool = False,
    short_term_memory_query: bool = False,
) -> dict:
    is_profile_record = intent == INTENT_RECORD and _looks_like_profile_record(str(state.get("user_message") or ""))
    return {
        "intent": intent,
        **_contract_fields(intent, state),
        "confidence": confidence,
        "emotion": state.get("emotion") or {"label": "중립", "intensity": 0.0},
        "previous_intent": state.get("intent"),
        "previous_emotion": state.get("emotion"),
        "requires_past_memory": requires_past_memory,
        "should_save_episode": should_save_episode,
        "short_term_memory_query": short_term_memory_query,
        "has_fact_change": False,
        "record_type": "profile" if is_profile_record else None,
        "profile_changes": None,
        "is_today": None,
        "modify_target": None,
        "search_targets": search_targets or [],
        "search_retry_count": 0,
        "fallback_count": state.get("fallback_count", 0),
        "self_eval_count": 0,
    }


def _contract_fields(
    intent: str,
    state: GraphState,
    *,
    record_type: str | None = None,
    modify_target: str | None = None,
    profile_changes: dict | None = None,
    routing_message: str | None = None,
    emotion_override: dict | None = None,
) -> dict:
    action_intent = _action_intent_from_legacy(intent)
    support_mode = _support_mode(intent, state, routing_message, emotion_override)
    resolution = state.get("context_resolution") or {}
    resolved_domain = resolution.get("resolved_domain")
    active_proposal = state.get("active_proposal") or {}
    resolved_reference = resolution.get("resolved_reference")
    effective_message = routing_message or state.get("user_message")
    inferred_domain = infer_domain(effective_message)

    domain = "general"
    if action_intent == "safety":
        domain = "general"
    elif record_type == "profile" or profile_changes:
        domain = "profile"
    elif modify_target in {"workout", "diet"}:
        domain = modify_target
    elif resolved_domain in {"workout", "diet", "profile", "general"} and resolved_domain != "none":
        domain = resolved_domain
    elif action_intent in {"create", "modify", "approval"} and inferred_domain in {"workout", "diet"}:
        domain = inferred_domain
    elif action_intent == "approval" and state.get("proposed_plan_type") in {"workout", "diet"}:
        domain = str(state.get("proposed_plan_type"))
    elif resolved_reference == "active_proposal" and active_proposal.get("domain") in {"workout", "diet"}:
        domain = str(active_proposal["domain"])
    elif inferred_domain in {"workout", "diet", "profile"}:
        domain = inferred_domain
    else:
        domain = "general"

    ambiguous = bool(resolution.get("ambiguous")) or intent == INTENT_FALLBACK
    return {
        "action_intent": action_intent,
        "domain": domain,
        "support_mode": support_mode,
        "ambiguous": ambiguous,
    }


def _action_intent_from_legacy(intent: str) -> str:
    if intent == INTENT_PLAN:
        return "create"
    if intent == INTENT_MODIFY:
        return "modify"
    if intent == INTENT_INFO:
        return "info"
    if intent == INTENT_RECORD:
        return "record"
    if intent == INTENT_APPROVAL:
        return "approval"
    if intent == INTENT_CASUAL:
        return "casual"
    if intent == INTENT_SAFETY:
        return "safety"
    if intent == INTENT_HOME_RECOMMENDATION:
        return "home_recommendation"
    if intent == INTENT_CARE:
        return "casual"
    return "fallback"


def _support_mode(
    intent: str,
    state: GraphState,
    routing_message: str | None,
    emotion_override: dict | None = None,
) -> str:
    if intent == INTENT_CARE:
        return "care"

    normalized = str(routing_message or state.get("user_message") or "").lower()
    if any(marker in normalized for marker in _CARE_SUPPORT_MARKERS):
        return "care"

    emotion = emotion_override or state.get("emotion") or {}
    emotion_intensity = float(emotion.get("intensity") or 0.0)
    if emotion_intensity >= 0.6:
        return "care"

    emotion_label = str(emotion.get("label") or "").lower()
    if any(marker in emotion_label for marker in ("불안", "우울", "슬픔", "외로움", "stress", "anx", "sad")):
        return "care"

    return "normal"


def _coerce_llm_intent(intent: str, state: GraphState, routing_message: str) -> str:
    if intent == INTENT_APPROVAL and not _has_pending_plan_confirmation_v2(state):
        if _looks_like_modify_request(routing_message):
            return INTENT_MODIFY
        if _looks_like_plan_request(routing_message):
            return INTENT_PLAN
        if _looks_like_profile_record(routing_message):
            return INTENT_RECORD
        return INTENT_FALLBACK
    return intent


def _routing_message(state: GraphState, message: str) -> str:
    resolution = state.get("context_resolution") or {}
    resolved_reference = resolution.get("resolved_reference")
    resolved_text = str(resolution.get("resolved_text") or "").strip()
    confidence = float(resolution.get("confidence") or 0.0)
    if resolved_reference and resolved_reference != "none" and resolved_text and confidence >= 0.6:
        return resolved_text
    return message


def _latest_assistant_message(state: GraphState) -> str:
    recent_turns = (state.get("recent_dialogue") or {}).get("recent_turns") or []
    for turn in reversed(recent_turns):
        assistant_text = str(turn.get("assistant_text") or "").strip()
        if assistant_text:
            return assistant_text
    return ""


def _latest_assistant_message_v2(state: GraphState) -> str:
    return _latest_assistant_message(state)


def _build_context_v3(state: GraphState) -> str:
    parts: list[str] = []

    if state.get("previous_intent"):
        parts.append(f"이전 의도: {state['previous_intent']}")

    if state.get("previous_emotion"):
        emotion = state["previous_emotion"]
        parts.append(f"이전 감정: {emotion['label']} (강도 {emotion['intensity']:.1f})")

    latest_assistant = _latest_assistant_message_v2(state)
    if latest_assistant:
        parts.append(f"직전 AI 응답: {latest_assistant[:200]}")

    resolution = state.get("context_resolution") or {}
    if resolution.get("resolved_reference") != "none" and resolution.get("resolved_text"):
        parts.append(
            "Resolved context: "
            f"{resolution.get('resolved_reference')} / {resolution.get('resolved_domain')} / "
            f"{str(resolution.get('resolved_text') or '')[:200]}"
        )

    recent_turns = ((state.get("recent_dialogue") or {}).get("recent_turns") or [])[-2:]
    if recent_turns:
        parts.append(
            "Recent dialogue summary:\n"
            + "\n".join(
                f"- {turn.get('action_intent')}/{turn.get('domain')}: {turn.get('user_summary')}"
                for turn in recent_turns
            )
        )

    return "\n".join(parts)


def _has_pending_plan_confirmation_v2(state: GraphState) -> bool:
    if bool(state.get("awaiting_plan_confirmation")) and bool(state.get("proposed_plan")):
        return True
    active_proposal = state.get("active_proposal")
    return bool(active_proposal and active_proposal.get("items"))


def _matches_hardcoded_confirmation_approval(message: str) -> bool:
    normalized = re.sub(r"\s+", " ", message.strip().lower())
    if not normalized:
        return False

    if normalized in {phrase.lower() for phrase in _EXPLICIT_PLAN_APPROVAL_PHRASES}:
        return True

    has_plan_reference = any(keyword in normalized for keyword in _PLAN_REFERENCE_KEYWORDS)
    has_apply_verb = any(keyword in normalized for keyword in _APPROVAL_COMMITMENT_KEYWORDS)
    return has_plan_reference and has_apply_verb and not _looks_like_explicit_plan_change(message, {})


async def _classify_plan_confirmation(
    deps: NodeDeps,
    state: GraphState,
    message: str,
) -> PlanConfirmationDecision | None:
    latest_assistant = _latest_assistant_message_v2(state)
    proposed_plan = state.get("proposed_plan") or []
    proposed_plan_type = state.get("proposed_plan_type") or (state.get("active_proposal") or {}).get("domain") or ""
    proposed_plan_action = state.get("proposed_plan_action") or (state.get("active_proposal") or {}).get("write_mode") or ""
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
            detail={"error": str(exc), "user_message": message},
        )
        if _looks_like_plan_approval(message, state) or _looks_like_plan_acceptance_followup(message, state):
            deps.trace.record_current_event(
                stage="confirm_gate",
                status="ok",
                title="Heuristic confirmation fallback approved",
                detail={"reason": "heuristic_fallback", "user_message": message},
            )
            return PlanConfirmationDecision(approved=True, confidence=0.9, reason="heuristic_fallback")
        return None


def _has_recent_plan_intent(state: GraphState) -> bool:
    return state.get("intent") in {INTENT_PLAN, INTENT_MODIFY, INTENT_APPROVAL} or state.get("previous_intent") in {
        INTENT_PLAN,
        INTENT_MODIFY,
        INTENT_APPROVAL,
    }


def _looks_like_explicit_plan_change(message: str, state: GraphState | dict) -> bool:
    normalized = message.strip().lower()
    if not normalized:
        return False

    has_change_marker = any(marker in normalized for marker in _PLAN_CHANGE_MARKERS)
    has_modify_keyword = any(keyword in normalized for keyword in _MODIFY_KEYWORDS)
    has_commitment_keyword = any(keyword in normalized for keyword in _APPROVAL_COMMITMENT_KEYWORDS)
    has_confirmation_reference = any(keyword in normalized for keyword in _PLAN_CONFIRMATION_REFERENCE_KEYWORDS)
    looks_like_referential_acceptance = has_confirmation_reference and has_commitment_keyword

    if has_modify_keyword and not looks_like_referential_acceptance:
        return True
    if has_change_marker and not looks_like_referential_acceptance:
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
    has_commitment_keyword = any(keyword in normalized for keyword in _APPROVAL_COMMITMENT_KEYWORDS)
    has_reference = any(
        keyword in normalized
        for keyword in (*_PLAN_REFERENCE_KEYWORDS, *_PLAN_CONFIRMATION_REFERENCE_KEYWORDS)
    )

    if is_short_ack:
        return True
    return has_commitment_keyword and has_reference


def _assistant_requested_plan_confirmation(state: GraphState) -> bool:
    latest_assistant = _latest_assistant_message_v2(state).lower()
    if not latest_assistant:
        return False

    has_plan_reference = any(keyword in latest_assistant for keyword in _PLAN_REFERENCE_KEYWORDS)
    has_confirmation_prompt = any(keyword in latest_assistant for keyword in _APPROVAL_KEYWORDS)
    return has_plan_reference and has_confirmation_prompt


def _looks_like_plan_request(message: str) -> bool:
    normalized = message.strip().lower()
    has_domain_keyword = any(keyword in normalized for keyword in _PLAN_DOMAIN_KEYWORDS)
    has_request_keyword = any(keyword in normalized for keyword in _PLAN_REQUEST_KEYWORDS)
    has_excluded_keyword = any(keyword in normalized for keyword in _PLAN_EXCLUDE_KEYWORDS)
    return has_domain_keyword and has_request_keyword and not has_excluded_keyword


def _looks_like_care_request(message: str) -> bool:
    normalized = message.strip().lower()
    return any(marker in normalized for marker in _CARE_SUPPORT_MARKERS)


def _looks_like_context_setup(message: str) -> bool:
    normalized = message.strip().lower()
    return any(marker in normalized for marker in ("내 상황 기억", "내 조건 기억", "내 상황 고려", "내 조건 고려", "기억하고 답"))


def _looks_like_question_followup(message: str) -> bool:
    normalized = message.strip().lower()
    if any(marker in normalized for marker in ("왜", "이유", "근거", "설명", "어떻게", "피해야", "해도 돼", "괜찮", "쉬어야")):
        return True
    return normalized.endswith("?")


def _looks_like_info_request(message: str) -> bool:
    normalized = message.strip().lower()
    has_domain_keyword = any(keyword in normalized for keyword in _PLAN_DOMAIN_KEYWORDS) or any(
        keyword in normalized for keyword in _PROFILE_FIELD_KEYWORDS
    )
    if "내 조건" in normalized or "내 상황" in normalized:
        has_domain_keyword = True
    has_info_marker = any(marker in normalized for marker in _INFO_REQUEST_MARKERS)
    return has_domain_keyword and has_info_marker


def _looks_like_modify_request(message: str) -> bool:
    normalized = message.strip().lower()
    has_domain_keyword = any(keyword in normalized for keyword in _PLAN_DOMAIN_KEYWORDS)
    has_modify_keyword = any(keyword in normalized for keyword in _MODIFY_KEYWORDS)
    return has_domain_keyword and has_modify_keyword


def _looks_like_plan_approval(message: str, state: GraphState) -> bool:
    normalized = message.strip().lower()
    has_approval_keyword = any(keyword in normalized for keyword in _APPROVAL_KEYWORDS)
    has_commitment_keyword = any(keyword in normalized for keyword in _APPROVAL_COMMITMENT_KEYWORDS)
    has_explicit_approval_phrase = any(phrase in normalized for phrase in _EXPLICIT_PLAN_APPROVAL_PHRASES)
    has_plan_reference = any(keyword in normalized for keyword in _PLAN_REFERENCE_KEYWORDS)
    has_confirmation_reference = any(keyword in normalized for keyword in _PLAN_CONFIRMATION_REFERENCE_KEYWORDS)
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
    if has_plan_context and has_confirmation_reference and has_commitment_keyword and not has_profile_keyword:
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


def _looks_like_memory_save_request(message: str) -> bool:
    normalized = message.strip().lower()
    return any(keyword in normalized for keyword in _MEMORY_SAVE_KEYWORDS)


def _looks_like_memory_query(message: str) -> bool:
    normalized = message.strip().lower()
    has_memory_keyword = any(keyword in normalized for keyword in _MEMORY_QUERY_KEYWORDS)
    has_question_shape = (
        "?" in normalized
        or normalized.endswith("뭐야")
        or normalized.endswith("뭐지")
        or normalized.endswith("기억나")
    )
    return has_memory_keyword and has_question_shape


def _looks_like_context_dependent_fallback(message: str, state: GraphState) -> bool:
    resolution = state.get("context_resolution") or {}
    if resolution.get("resolved_reference") not in {None, "", "none"}:
        return False

    normalized = message.strip().lower()
    has_reference = any(keyword in normalized for keyword in _CONTEXT_DEPENDENT_REFERENCES)
    has_plan_context = (
        _has_pending_plan_confirmation_v2(state)
        or bool(state.get("proposed_plan"))
        or _has_recent_plan_intent(state)
        or bool((state.get("recent_dialogue") or {}).get("recent_turns"))
        or state.get("intent") in {INTENT_INFO, INTENT_RECORD}
        or state.get("previous_intent") in {INTENT_INFO, INTENT_RECORD}
    )
    return has_reference and not has_plan_context
