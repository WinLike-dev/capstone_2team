"""Draft generation node for responses and proposed plans."""
from __future__ import annotations

import json
import logging
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

        if intent == INTENT_APPROVAL:
            deps.trace.record_current_event(
                stage="generate",
                status="ok",
                title="Approval draft shortcut used",
                duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )
            return _build_approval_draft(state)

        context = _build_draft_context(state)
        system_prompt = _build_draft_system_prompt(state, failure_reason)

        try:
            raw = await deps.router.generate(
                system_prompt=system_prompt,
                user_content=context,
                response_schema=DraftResponse,
            )
            draft_result = DraftResponse.model_validate_json(raw)
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

        if not proposed_plan and intent not in {INTENT_PLAN, INTENT_MODIFY}:
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
        return {
            "draft_response": draft_text,
            "draft_components": draft_components,
            "proposed_plan": proposed_plan,
            "proposed_plan_type": proposed_plan_type,
            "proposed_plan_action": proposed_plan_action,
            "self_eval_count": 0,
            "self_eval_failure_reason": None,
        }

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


def _build_draft_context(state: GraphState) -> str:
    parts: list[str] = []

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
            for result in results[:3]
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


def _build_draft_system_prompt(state: GraphState, failure_reason: str | None) -> str:
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

    return "\n\n".join(section for section in sections if section)


def _build_components_from_result(draft_result: DraftResponse, state: GraphState) -> DraftComponents:
    payload = draft_result.model_dump()
    components = normalize_draft_components(payload)

    if not components["search_grounding_summary"] and state.get("search_results"):
        components["search_grounding_summary"] = "검색 결과를 참고해 핵심 근거만 정리했다."

    return components


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
