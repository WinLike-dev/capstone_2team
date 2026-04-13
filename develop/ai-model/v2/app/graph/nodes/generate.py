"""Draft generation node for responses and proposed plans."""
from __future__ import annotations

import json
import logging
import re
import time

from app.core.draft_contract import normalize_draft_components, render_draft_preview
from app.core.prompt_loader import compose_prompts, load_prompt
from app.graph.deps import NodeDeps
from app.schemas.home import HomeRecommendationResponse
from app.schemas.llm_responses import DraftResponse, SelfEvalResponse
from app.schemas.state import DraftComponents, GraphState
from app.services.home_recommendations import (
    PROMPT_PATH as _HOME_RECOMMENDATION_PROMPT,
    build_home_recommendation_prompt_input,
    empty_home_recommendations,
    kst_today_iso,
    normalize_home_recommendations,
)

logger = logging.getLogger(__name__)

INTENT_CARE = "공감_케어"
INTENT_PLAN = "계획"
INTENT_MODIFY = "수정"
INTENT_APPROVAL = "계획_승인"
INTENT_INFO = "정보"
INTENT_SAFETY = "안전경고"

_MENTAL_HEALTH_SAFETY_PATTERNS = re.compile(
    r"자해|자살|죽고\s*싶|극단적\s*선택|충동|해치고\s*싶|살고\s*싶지",
)
_PHYSICAL_SAFETY_PATTERNS = re.compile(
    r"가슴.*조여|숨이?\s*차|호흡.*힘들|어지럽|쓰러질\s*것\s*같|실신|기절|"
    r"과다\s*복용|심한\s*통증|출혈|피가\s*멈추지",
)

MAX_SELF_EVAL = 1
_SELF_EVAL_INTENTS = {INTENT_SAFETY, INTENT_CARE}

_PLAN_TYPE_KEYWORDS = {
    "diet": ("식단", "식사", "영양", "칼로리", "다이어트", "meal", "diet", "nutrition", "calorie"),
    "workout": ("운동", "러닝", "달리기", "헬스", "근력", "유산소", "웨이트", "exercise", "workout", "training", "run"),
}

_DRAFT_COMMON_PROMPT = "nodes/generate/draft_common.md"
_DRAFT_DEFAULT_PROMPT = "nodes/generate/draft_default.md"
_DRAFT_PROMPTS_BY_INTENT = {
    INTENT_PLAN: "nodes/generate/draft_plan.md",
    INTENT_MODIFY: "nodes/generate/draft_modify.md",
    INTENT_INFO: "nodes/generate/draft_info.md",
    INTENT_CARE: "nodes/generate/draft_care.md",
    INTENT_SAFETY: "nodes/generate/draft_safety.md",
}

_SELF_EVAL_PROMPT = load_prompt("nodes/generate/self_eval.md")

_SHORT_TERM_MEMORY_PROMPT = """Short-term memory mode:
- Answer from the recent chat history first.
- Prefer the user's earlier statements over generic health advice.
- Do not use search evidence, profile metadata, or plan context unless the recent chat itself mentions them.
- If the answer is not present in the recent chat history, say that you cannot confirm it from the recent conversation.
- Keep the answer direct and specific to the recall question.
"""

_ANTI_REPETITION_PROMPT = """Anti-repetition mode:
- Do not repeat the previous assistant response in the same or slightly different wording.
- If the user asks a follow-up, answer only the new or directly requested point.
- Avoid re-listing the same reasons or plan summary unless the user explicitly asks for them again.
"""

_SHORT_TERM_MEMORY_RECENT_LIMIT = 8
_REPETITION_OVERLAP_THRESHOLD = 0.8


def make_generate_node(deps: NodeDeps):
    async def generate_node(state: GraphState) -> dict:
        if state.get("response"):
            return {}

        started_at = time.perf_counter()
        intent = state.get("intent", "")
        eval_count = state.get("self_eval_count", 0)
        failure_reason = state.get("self_eval_failure_reason")
        deps.trace.record_current_event(
            stage="generate",
            status="info",
            title="Draft generation started",
            detail={"intent": intent, "self_eval_count": eval_count},
        )

        if state.get("request_kind") == "home_recommendation":
            return await _generate_home_recommendations(deps, state, started_at)

        if intent == INTENT_SAFETY:
            deps.trace.record_current_event(
                stage="generate",
                status="ok",
                title="Safety draft shortcut used",
                duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )
            return _build_safety_draft(state)

        if intent == INTENT_APPROVAL:
            deps.trace.record_current_event(
                stage="generate",
                status="ok",
                title="Approval draft shortcut used",
                duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )
            return _build_approval_draft_v2(state)

        direct_memory_draft = _build_direct_short_term_memory_draft(state)
        if direct_memory_draft is not None:
            deps.trace.record_current_event(
                stage="generate",
                status="ok",
                title="Direct short-term memory draft used",
                detail={"intent": intent},
                duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )
            return direct_memory_draft

        context = _build_draft_context(state)
        system_prompt = _build_draft_system_prompt(state, failure_reason)

        try:
            draft_result = await _request_draft_with_guardrails(
                deps=deps,
                state=state,
                system_prompt=system_prompt,
                user_content=context,
                failure_reason=failure_reason,
            )
            draft_components = _build_components_from_result(draft_result, state)
            draft_text = render_draft_preview(draft_components)
            proposed_plan = [
                item.model_dump() for item in draft_result.proposed_plan
            ] if draft_result.proposed_plan else []
            proposed_plan_type = _resolve_proposed_plan_type(state, draft_result, proposed_plan)
            proposed_plan_action = _resolve_proposed_plan_action(state, proposed_plan)
        except Exception as exc:
            logger.error("Draft generation failed: %s", exc)
            deps.trace.record_current_alert(
                severity="error",
                message="Draft generation failed",
                detail={"intent": intent, "error": str(exc)},
            )
            draft_components = normalize_draft_components(
                None,
                fallback_text="초안을 생성하는 중 오류가 발생했습니다. 다시 시도해 주세요.",
            )
            draft_text = render_draft_preview(draft_components)
            proposed_plan = []
            proposed_plan_type = None
            proposed_plan_action = None

        if intent not in {INTENT_PLAN, INTENT_MODIFY}:
            proposed_plan = []
            proposed_plan_type = None
            proposed_plan_action = None

        if not proposed_plan and intent == INTENT_APPROVAL:
            proposed_plan = state.get("proposed_plan")
            proposed_plan_type = state.get("proposed_plan_type")
            proposed_plan_action = state.get("proposed_plan_action")

        if intent in _SELF_EVAL_INTENTS:
            passed, reason = await _self_evaluate(deps, state, draft_text)
            if not passed:
                if eval_count < MAX_SELF_EVAL:
                    logger.info("Self-eval failed, retrying: count=%d reason=%s", eval_count, reason)
                    deps.trace.record_current_alert(
                        severity="warning",
                        message="Self-eval requested another generation pass",
                        detail={"reason": reason, "next_count": eval_count + 1},
                    )
                    return {
                        "self_eval_count": eval_count + 1,
                        "self_eval_failure_reason": reason,
                    }
                logger.warning("Self-eval retry limit reached, applying partial patch")
                deps.trace.record_current_alert(
                    severity="warning",
                    message="Self-eval retry limit reached; partial patch applied",
                    detail={"reason": reason},
                )
                draft_components = _apply_partial_patch(draft_components, reason)
                draft_text = render_draft_preview(draft_components)

        deps.trace.record_current_event(
            stage="generate",
            status="ok",
            title="Draft generation completed",
            detail={
                "intent": intent,
                "proposed_plan_count": len(proposed_plan or []),
                "proposed_plan_type": proposed_plan_type,
                "proposed_plan_action": proposed_plan_action,
            },
            duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
        )
        result = {
            "draft_response": draft_text,
            "draft_components": draft_components,
            "proposed_plan": proposed_plan,
            "proposed_plan_type": proposed_plan_type,
            "proposed_plan_action": proposed_plan_action,
            "self_eval_count": 0,
            "self_eval_failure_reason": None,
        }
        if intent in {INTENT_PLAN, INTENT_MODIFY} and proposed_plan:
            result["awaiting_plan_confirmation"] = True
        return result

    return generate_node


async def _generate_home_recommendations(
    deps: NodeDeps,
    state: GraphState,
    started_at: float,
) -> dict:
    scope = state.get("home_recommendation_scope") or "all"
    date = kst_today_iso()

    try:
        raw = await deps.router.generate(
            system_prompt=load_prompt(_HOME_RECOMMENDATION_PROMPT),
            user_content=build_home_recommendation_prompt_input(
                date=date,
                scope=scope,
                user_profile=state.get("user_profile") or {},
                today_plan=state.get("today_plan") or [],
            ),
            response_schema=HomeRecommendationResponse,
        )
        result = HomeRecommendationResponse.model_validate_json(raw)
        normalized = normalize_home_recommendations(
            result,
            scope=scope,
            date=date,
        )
    except Exception as exc:
        logger.error("Home recommendation generation failed: %s", exc)
        deps.trace.record_current_alert(
            severity="error",
            message="Home recommendation generation failed",
            detail={"scope": scope, "error": str(exc)},
        )
        normalized = empty_home_recommendations(date=date, scope=scope)

    deps.trace.record_current_event(
        stage="generate",
        status="ok",
        title="Home recommendations generated",
        detail={
            "scope": scope,
            "workout_slots": sum(
                1
                for item in normalized.workout.model_dump().values()
                if item is not None
            ),
            "diet_slots": sum(
                1
                for item in normalized.diet.model_dump().values()
                if item is not None
            ),
        },
        duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
    )
    return {
        "home_recommendations": normalized.model_dump(),
        "self_eval_count": 0,
        "self_eval_failure_reason": None,
    }


async def _request_draft_with_guardrails(
    deps: NodeDeps,
    state: GraphState,
    system_prompt: str,
    user_content: str,
    failure_reason: str | None,
) -> DraftResponse:
    raw = await deps.router.generate(
        system_prompt=system_prompt,
        user_content=user_content,
        response_schema=DraftResponse,
    )
    draft_result = DraftResponse.model_validate_json(raw)

    if not _needs_generate_retry(state, draft_result):
        return draft_result

    deps.trace.record_current_event(
        stage="generate",
        status="warning",
        title="Draft regeneration requested",
        detail={
            "short_term_memory_query": bool(state.get("short_term_memory_query")),
            "last_assistant_present": bool(state.get("last_assistant_message")),
        },
    )

    retry_raw = await deps.router.generate(
        system_prompt=_build_draft_system_prompt(
            state,
            failure_reason,
            reinforce_short_term=True,
            avoid_repetition=True,
        ),
        user_content=_build_draft_context(
            state,
            force_short_term=bool(state.get("short_term_memory_query")),
        ),
        response_schema=DraftResponse,
    )
    return DraftResponse.model_validate_json(retry_raw)


def _build_draft_context(state: GraphState, *, force_short_term: bool = False) -> str:
    if force_short_term or state.get("short_term_memory_query"):
        return _build_short_term_memory_context(state)

    parts: list[str] = []
    parts.append(f"[오늘 날짜]\n{kst_today_iso()}")

    messages = state.get("messages", [])
    if messages:
        history = "\n".join(
            f"{message['role']}: {message['content'][:200]}"
            for message in messages[-4:]
        )
        parts.append(f"[최근 대화]\n{history}")

    parts.append(f"[현재 질문]\n{state['user_message']}")

    results = state.get("search_results") or []
    if results:
        snippets = "\n".join(
            f"[{result.get('source', 'unknown')}] {result.get('text', '')[:200]}"
            for result in results[: _search_snippet_limit(state)]
        )
        parts.append(f"[참고 정보]\n{snippets}")

    modify_context = state.get("modify_plan_context")
    if modify_context:
        parts.append(f"[현재 전체 플랜]\n{json.dumps(modify_context, ensure_ascii=False)[:500]}")

    profile = state.get("user_profile")
    if profile:
        profile_copy = profile.copy()
        profile_copy.pop("mbti", None)
        parts.append(f"[사용자 프로필]\n{json.dumps(profile_copy, ensure_ascii=False)}")

    changes = state.get("profile_changes")
    if changes:
        parts.append(f"[프로필 변경 요청]\n{json.dumps(changes, ensure_ascii=False)}")

    return "\n\n".join(parts)


def _build_short_term_memory_context(state: GraphState) -> str:
    parts = [f"[Today]\n{kst_today_iso()}"]

    recent_messages = (state.get("messages") or [])[-_SHORT_TERM_MEMORY_RECENT_LIMIT:]
    if recent_messages:
        history = "\n".join(
            f"{message['role']}: {str(message.get('content') or '')[:240]}"
            for message in recent_messages
        )
        parts.append(f"[Recent Chat History]\n{history}")

    last_assistant_message = str(state.get("last_assistant_message") or "").strip()
    if last_assistant_message:
        parts.append(f"[Previous Assistant Response]\n{last_assistant_message[:400]}")

    parts.append(f"[Current Recall Question]\n{state['user_message']}")
    parts.append(
        "[Instruction]\nUse only the recent chat history above. "
        "If the answer is missing there, say you cannot confirm it from the recent conversation."
    )
    return "\n\n".join(parts)


def _search_snippet_limit(state: GraphState) -> int:
    if state.get("intent") == INTENT_INFO:
        return 2
    return 3


def _build_draft_system_prompt(
    state: GraphState,
    failure_reason: str | None,
    *,
    reinforce_short_term: bool = False,
    avoid_repetition: bool = False,
) -> str:
    intent = state.get("intent", "")
    intent_prompt = _DRAFT_PROMPTS_BY_INTENT.get(intent, _DRAFT_DEFAULT_PROMPT)

    sections = [compose_prompts(_DRAFT_COMMON_PROMPT, intent_prompt)]

    emotion = state.get("emotion") or {}
    sections.append(
        f"현재 사용자 감정: {emotion.get('label', '중립')} (강도 {emotion.get('intensity', 0.0):.1f})"
    )

    if state.get("search_quality") == "degraded":
        sections.append(
            "주의: 검색 결과가 충분하지 않으므로 일반 원칙 수준으로만 답하고, 근거의 한계를 분명히 드러낸다."
        )

    if failure_reason:
        sections.append(
            f"이전 Draft는 자기 평가를 통과하지 못했다. 실패 이유: {failure_reason}"
        )

    if reinforce_short_term or state.get("short_term_memory_query"):
        sections.append(_SHORT_TERM_MEMORY_PROMPT)

    if avoid_repetition or state.get("last_assistant_message"):
        sections.append(_ANTI_REPETITION_PROMPT)
        last_assistant_message = str(state.get("last_assistant_message") or "").strip()
        if last_assistant_message:
            sections.append(
                f"Previous assistant response to avoid repeating:\n{last_assistant_message[:400]}"
            )

    return "\n\n".join(section for section in sections if section)


def _build_components_from_result(draft_result: DraftResponse, state: GraphState) -> DraftComponents:
    payload = draft_result.model_dump()
    components = normalize_draft_components(payload)

    if not components["search_grounding_summary"] and state.get("search_results"):
        components["search_grounding_summary"] = "검색 결과를 참고해 핵심 근거만 정리했다."

    return components


def _build_direct_short_term_memory_draft(state: GraphState) -> dict | None:
    if not state.get("short_term_memory_query"):
        return None

    user_message = str(state.get("user_message") or "")
    alias = _extract_recent_alias(state)
    if alias and "\ubcc4\uba85" not in user_message:
        alias = None

    if alias:
        components = normalize_draft_components(
            {
                "core_message": f"\ubc29\uae08 \ub9d0\ud55c \ubcc4\uba85\uc740 '{alias}'\uc774\uc5d0\uc694.",
                "reason_points": [f"\ucd5c\uadfc \ub300\ud654\uc5d0\uc11c '{alias}'\ub77c\uace0 \ub9d0\ud588\uc5b4\uc694."],
                "suggested_action": "",
                "search_grounding_summary": "",
            }
        )
        return {
            "draft_response": render_draft_preview(components),
            "draft_components": components,
            "proposed_plan": [],
            "proposed_plan_type": None,
            "proposed_plan_action": None,
            "self_eval_count": 0,
            "self_eval_failure_reason": None,
        }

    recent_user_message = _latest_previous_user_message(state)
    if recent_user_message and _looks_like_recent_utterance_query(user_message):
        components = normalize_draft_components(
            {
                "core_message": f"\ubc29\uae08 \ub9d0\ud558\uc2e0 \ub0b4\uc6a9\uc740 \"{recent_user_message[:120]}\"\uc608\uc694.",
                "reason_points": [],
                "suggested_action": "",
                "search_grounding_summary": "",
            }
        )
        return {
            "draft_response": render_draft_preview(components),
            "draft_components": components,
            "proposed_plan": [],
            "proposed_plan_type": None,
            "proposed_plan_action": None,
            "self_eval_count": 0,
            "self_eval_failure_reason": None,
        }

    return None


def _extract_recent_alias(state: GraphState) -> str | None:
    alias_pattern = re.compile(
        r"(?:\ub0b4\s*\ubcc4\uba85(?:\uc740|\uc774)?|(?:\uc55e\uc73c\ub85c\s*)?\ub0b4\s*\ubcc4\uba85(?:\uc740|\uc774)?)\s*(?::|=)?\s*([^\n,.!?]+)"
    )
    for message in reversed(state.get("messages", [])):
        if message.get("role") != "user":
            continue
        content = str(message.get("content") or "")
        match = alias_pattern.search(content)
        if match:
            return match.group(1).strip(" \"'")
    return None


def _latest_previous_user_message(state: GraphState) -> str:
    for message in reversed(state.get("messages", [])):
        if message.get("role") == "user":
            return str(message.get("content") or "").strip()
    return ""


def _looks_like_recent_utterance_query(user_message: str) -> bool:
    normalized = re.sub(r"\s+", " ", user_message.strip().lower())
    if not normalized:
        return False
    markers = (
        "\ubc29\uae08",
        "\uc544\uae4c",
        "\uc870\uae08 \uc804",
        "\ub0b4\uac00 \ub9d0\ud55c",
        "\ubb50\ub77c\uace0 \ud588",
        "\ubb50\ub77c\uace0 \ub9d0\ud588",
    )
    return any(marker in normalized for marker in markers)


def _needs_generate_retry(state: GraphState, draft_result: DraftResponse) -> bool:
    if state.get("short_term_memory_query") and draft_result.search_grounding_summary:
        return True

    last_assistant_message = str(state.get("last_assistant_message") or "").strip()
    if not last_assistant_message:
        return False

    current_text = render_draft_preview(_build_components_from_result(draft_result, state))
    return _is_too_similar(current_text, last_assistant_message)


def _is_too_similar(current_text: str, previous_text: str) -> bool:
    current_tokens = set(_normalized_overlap_tokens(current_text))
    previous_tokens = set(_normalized_overlap_tokens(previous_text))
    if not current_tokens or not previous_tokens:
        return False
    if current_tokens == previous_tokens:
        return True
    overlap = len(current_tokens & previous_tokens) / max(len(current_tokens), len(previous_tokens))
    return overlap >= _REPETITION_OVERLAP_THRESHOLD


def _normalized_overlap_tokens(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return re.findall(r"[0-9a-z\uac00-\ud7a3]+", normalized)


def _build_approval_draft(state: GraphState) -> dict:
    proposed_plan = state.get("proposed_plan") or []
    if not proposed_plan:
        components = normalize_draft_components(
            {
                "core_message": "현재 승인 대기 중인 계획이 없습니다.",
                "suggested_action": "먼저 계획 제안을 받은 뒤 승인 요청을 해 주세요.",
            }
        )
        return {
            "draft_response": render_draft_preview(components),
            "draft_components": components,
            "proposed_plan": None,
            "proposed_plan_type": None,
            "proposed_plan_action": None,
            "self_eval_count": 0,
            "self_eval_failure_reason": None,
        }

    proposed_plan_type = state.get("proposed_plan_type")
    proposed_plan_action = state.get("proposed_plan_action") or "create"
    plan_label = "식단" if proposed_plan_type == "diet" else "운동"
    action_label = "수정안" if proposed_plan_action == "update" else "계획"

    components = normalize_draft_components(
        {
            "core_message": f"{plan_label} {action_label} 승인을 확인했다.",
            "suggested_action": "이제 저장 절차를 진행한다.",
            "search_grounding_summary": "",
        }
    )
    return {
        "draft_response": render_draft_preview(components),
        "draft_components": components,
        "proposed_plan": proposed_plan,
        "proposed_plan_type": proposed_plan_type,
        "proposed_plan_action": proposed_plan_action,
        "self_eval_count": 0,
        "self_eval_failure_reason": None,
    }


def _build_approval_draft_v2(state: GraphState) -> dict:
    proposed_plan = state.get("proposed_plan") or []
    if not proposed_plan:
        components = normalize_draft_components(
            {
                "core_message": "지금은 승인 대기 중인 계획이 없어요.",
                "suggested_action": "먼저 계획을 제안받은 뒤 승인 요청을 해주세요.",
            }
        )
        return {
            "draft_response": render_draft_preview(components),
            "draft_components": components,
            "proposed_plan": None,
            "proposed_plan_type": None,
            "proposed_plan_action": None,
            "self_eval_count": 0,
            "self_eval_failure_reason": None,
        }

    proposed_plan_type = state.get("proposed_plan_type")
    proposed_plan_action = state.get("proposed_plan_action") or "create"
    plan_label = "식단" if proposed_plan_type == "diet" else "운동"
    action_label = "수정안" if proposed_plan_action == "update" else "계획"

    components = normalize_draft_components(
        {
            "core_message": f"{plan_label} {action_label} 반영할게.",
            "suggested_action": "",
            "search_grounding_summary": "",
        }
    )
    return {
        "draft_response": render_draft_preview(components),
        "draft_components": components,
        "proposed_plan": proposed_plan,
        "proposed_plan_type": proposed_plan_type,
        "proposed_plan_action": proposed_plan_action,
        "self_eval_count": 0,
        "self_eval_failure_reason": None,
    }


def _build_safety_draft(state: GraphState) -> dict:
    safety_kind = _classify_safety_kind(state["user_message"])

    if safety_kind == "mental_health_crisis":
        components = normalize_draft_components(
            {
                "core_message": "지금 혼자 버티지 말고 즉시 사람과 연결되는 것이 우선입니다.",
                "reason_points": [
                    "현재 메시지는 자해나 자살 위험처럼 즉각적인 도움 연결이 필요한 상황으로 보입니다.",
                    "운동이나 식단 조언보다 안전 확보와 주변 도움 요청이 먼저입니다.",
                ],
                "suggested_action": (
                    "가까운 사람에게 지금 상태를 바로 알리고, 자살예방상담전화 109 "
                    "또는 정신건강상담전화 1577-0199에 즉시 연락하세요."
                ),
                "safety_notes": [
                    "혼자 있지 말고 주변 사람이나 보호자와 함께 있으세요.",
                    "위험한 물건이나 약물이 손에 닿지 않게 멀리하세요.",
                    "당장 위험이 크면 119 또는 가까운 응급실로 바로 도움을 요청하세요.",
                ],
                "approval_question": None,
                "search_grounding_summary": "",
            }
        )
    else:
        components = normalize_draft_components(
            {
                "core_message": "이건 운동 조언보다 즉시 응급 대응이 우선일 수 있는 증상입니다.",
                "reason_points": [
                    "가슴 통증, 호흡 곤란, 심한 어지럼, 실신감, 과다 복용 의심은 응급 평가가 필요할 수 있습니다.",
                    "운동을 계속하거나 집에서 버티는 것보다 즉시 중단하고 상태를 확인받는 것이 안전합니다.",
                ],
                "suggested_action": (
                    "지금 바로 운동을 멈추고 앉거나 누워 안정을 취한 뒤, 증상이 계속되면 119에 연락하거나 "
                    "가까운 응급실로 가세요."
                ),
                "safety_notes": [
                    "혼자 이동하지 말고 가능하면 주변 사람에게 도움을 요청하세요.",
                    "가슴 통증, 숨참, 의식 저하, 경련, 심한 출혈이 있으면 지체하지 말고 119를 부르세요.",
                    "증상이 가라앉더라도 원인 확인 전에는 운동을 다시 하지 마세요.",
                ],
                "approval_question": None,
                "search_grounding_summary": "",
            }
        )

    return {
        "draft_response": render_draft_preview(components),
        "draft_components": components,
        "proposed_plan": None,
        "proposed_plan_type": None,
        "proposed_plan_action": None,
        "self_eval_count": 0,
        "self_eval_failure_reason": None,
    }


def _classify_safety_kind(message: str) -> str:
    if _MENTAL_HEALTH_SAFETY_PATTERNS.search(message):
        return "mental_health_crisis"
    if _PHYSICAL_SAFETY_PATTERNS.search(message):
        return "physical_emergency"
    return "physical_emergency"


def _resolve_proposed_plan_type(
    state: GraphState,
    draft_result: DraftResponse,
    proposed_plan: list[dict],
) -> str | None:
    if not proposed_plan:
        return None

    modify_target = state.get("modify_target")
    if modify_target in {"workout", "diet"}:
        return modify_target

    if draft_result.proposed_plan_type in {"workout", "diet"}:
        return draft_result.proposed_plan_type

    return _infer_plan_type_from_message(state["user_message"])


def _resolve_proposed_plan_action(state: GraphState, proposed_plan: list[dict]) -> str | None:
    if not proposed_plan:
        return None
    if state.get("intent") == INTENT_MODIFY:
        return "update"
    return "create"


def _infer_plan_type_from_message(message: str) -> str | None:
    lowered = message.lower()
    diet_hits = sum(1 for keyword in _PLAN_TYPE_KEYWORDS["diet"] if keyword in lowered)
    workout_hits = sum(1 for keyword in _PLAN_TYPE_KEYWORDS["workout"] if keyword in lowered)

    if diet_hits > workout_hits:
        return "diet"
    if workout_hits > diet_hits:
        return "workout"
    return None


async def _self_evaluate(deps: NodeDeps, state: GraphState, response: str) -> tuple[bool, str]:
    emotion = state.get("emotion") or {}
    user_content = (
        f"감정 상태: {emotion.get('label', '중립')} (강도 {emotion.get('intensity', 0):.1f})\n"
        f"사용자 메시지: {state['user_message']}\n"
        f"생성된 Draft:\n{response}"
    )

    try:
        raw = await deps.router.generate(
            system_prompt=_SELF_EVAL_PROMPT,
            user_content=user_content,
            response_schema=SelfEvalResponse,
        )
        result = SelfEvalResponse.model_validate_json(raw)
        return result.passed, result.reason
    except Exception as exc:
        logger.warning("Self-eval failed, passing through: %s", exc)
        return True, ""


def _apply_partial_patch(components: DraftComponents, reason: str) -> DraftComponents:
    patched = normalize_draft_components(dict(components))
    safety_line = "증상이 심하거나 위험하다고 느껴지면 전문가 상담이나 지역 응급 지원을 우선해 주세요."

    if safety_line not in patched["safety_notes"]:
        patched["safety_notes"].append(safety_line)

    if reason and not patched["search_grounding_summary"]:
        patched["search_grounding_summary"] = f"검토 메모: {reason}"

    return patched
