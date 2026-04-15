"""Search pipeline node for vector and web retrieval."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from app.core.conversation_state import infer_domain
from app.core.prompt_loader import load_prompt
from app.graph.deps import NodeDeps
from app.schemas.llm_responses import QueryRegenResponse, SearchEvalResponse
from app.schemas.state import GraphState

logger = logging.getLogger(__name__)

INTENT_CARE = "공감_케어"
INTENT_PLAN = "계획"
INTENT_MODIFY = "수정"
INTENT_INFO = "정보"

TOP_K = 8
_WEB_ENABLED_INTENTS = {INTENT_INFO}
_ACCEPT_SCORE_BY_INTENT = {
    INTENT_INFO: 0.6,
    INTENT_PLAN: 0.55,
    INTENT_MODIFY: 0.5,
}
_RETRY_SCORE_BY_INTENT = {
    INTENT_INFO: 0.25,
    INTENT_PLAN: 0.25,
    INTENT_MODIFY: 0.0,
}
_MAX_RETRY_BY_INTENT = {
    INTENT_INFO: 0,
    INTENT_PLAN: 0,
    INTENT_MODIFY: 0,
}
_INFO_WEB_KEYWORDS = (
    "최신",
    "최근",
    "요즘",
    "뉴스",
    "연구",
    "논문",
    "업데이트",
    "근거",
    "가이드라인",
    "권고",
)

_EVAL_SYSTEM_PROMPT = load_prompt("nodes/search/eval.md")
_QUERY_REGEN_PROMPT = load_prompt("nodes/search/query_regen.md")


def make_search_node(deps: NodeDeps):
    async def search_node(state: GraphState) -> dict:
        started_at = time.perf_counter()
        query = state.get("search_query") or _resolved_query(state)
        targets = list(state.get("search_targets") or [])
        retry_count = state.get("search_retry_count", 0)
        intent = state.get("intent", "")
        deps.trace.record_current_event(
            stage="search",
            status="info",
            title="Search started",
            detail={"intent": intent, "targets": targets, "retry_count": retry_count},
        )

        query = _augment_query(query, state)
        targets = _normalize_targets(state, query, targets)
        external_filter, relaxed_external_filter = _build_external_filters(state, query)

        if intent in _WEB_ENABLED_INTENTS and "vdb_external" in targets and "web" not in targets:
            targets.append("web")

        if not targets:
            deps.trace.record_current_event(
                stage="search",
                status="ok",
                title="Search skipped",
                detail={"reason": "no_targets"},
                duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )
            return {"search_results": [], "search_quality": "ok"}

        try:
            query_vec = await deps.embed.embed(query)
        except Exception as exc:
            logger.error("Embedding failed: %s", exc)
            deps.trace.record_current_alert(
                severity="error",
                message="Embedding failed before search",
                detail={"error": str(exc)},
            )
            return _degraded(state, intent)

        raw_results = await _parallel_search(
            deps,
            state["user_id"],
            query,
            query_vec,
            targets,
            external_filter=external_filter,
        )
        merged_results = _merge_results(raw_results)
        merged_results = await _expand_external_results_if_needed(
            deps,
            query_vec,
            targets,
            merged_results,
            strict_filter=external_filter,
            relaxed_filter=relaxed_external_filter,
        )

        if _should_skip_eval(state, merged_results):
            deps.trace.record_current_event(
                stage="search",
                status="ok",
                title="Search completed with lightweight policy",
                detail={"results": len(merged_results), "reason": _skip_eval_reason(state, merged_results)},
                duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )
            return {
                "search_results": merged_results,
                "search_quality": "ok" if merged_results else "degraded",
                "search_retry_count": retry_count,
            }

        score = await _evaluate(deps, query, merged_results)
        logger.info("Search quality score=%.2f retry=%d", score, retry_count)

        accept_score = _accept_score_for_intent(intent)
        if score >= accept_score:
            deps.trace.record_current_event(
                stage="search",
                status="ok",
                title="Search completed",
                detail={"score": score, "accept_score": accept_score, "results": len(merged_results)},
                duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )
            return {
                "search_results": merged_results,
                "search_quality": "ok",
                "search_retry_count": retry_count,
            }

        max_retry = _max_retry_for_intent(intent)
        if retry_count >= max_retry:
            deps.trace.record_current_alert(
                severity="warning",
                message="Search degraded after retry limit",
                detail={"score": score, "retry_count": retry_count, "max_retry": max_retry},
            )
            return _degraded(state, intent)

        retry_score = _retry_score_for_intent(intent)
        if score < retry_score:
            new_query = await _regenerate_query(deps, _resolved_query(state), merged_results)
            deps.trace.record_current_event(
                stage="search",
                status="warn",
                title="Search query regenerated",
                detail={"score": score, "retry_score": retry_score, "new_query": new_query},
                duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )
            return {
                "search_query": new_query,
                "search_retry_count": retry_count + 1,
            }

        deps.trace.record_current_event(
            stage="search",
            status="warn",
            title="Search retry requested",
            detail={"score": score, "retry_count": retry_count + 1, "accept_score": accept_score},
            duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
        )
        return {"search_retry_count": retry_count + 1}

    return search_node


def _augment_query(query: str, state: GraphState) -> str:
    if state.get("search_query"):
        return query

    profile = state.get("user_profile") or {}
    additions: list[str] = []

    if profile.get("goal"):
        additions.append(f"목표:{profile['goal']}")
    if profile.get("injury_history"):
        additions.append(f"부상:{profile['injury_history']}")

    if not additions:
        return query
    return f"{query} [{', '.join(additions)}]"


def _resolved_query(state: GraphState) -> str:
    resolution = state.get("context_resolution") or {}
    resolved_text = str(resolution.get("resolved_text") or "").strip()
    resolved_reference = resolution.get("resolved_reference")
    confidence = float(resolution.get("confidence") or 0.0)

    if resolved_reference and resolved_reference != "none" and resolved_text and confidence >= 0.6:
        return resolved_text
    return str(state.get("user_message") or "")


def _normalize_targets(state: GraphState, query: str, targets: list[str]) -> list[str]:
    normalized = list(dict.fromkeys(targets))
    intent = state.get("intent")
    action_intent = state.get("action_intent")

    if action_intent in {"create", "modify"} or intent == INTENT_MODIFY:
        return [target for target in normalized if target != "web"]

    if intent == INTENT_INFO and "web" in normalized and not _info_needs_web(query):
        return [target for target in normalized if target != "web"]

    return normalized


def _info_needs_web(query: str) -> bool:
    normalized = query.strip().lower()
    return any(keyword in normalized for keyword in _INFO_WEB_KEYWORDS)


def _build_external_filters(state: GraphState, query: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    domain = _resolved_domain(state, query)
    action_intent = str(state.get("action_intent") or "")
    category_candidates = _external_categories_for_domain(domain)
    use_case_candidates = _external_use_cases_for_request(domain, action_intent, query)
    population_candidates = _external_populations_for_profile(state)
    clauses: list[dict[str, Any]] = []
    relaxed_filter: dict[str, Any] | None = None

    if category_candidates:
        clauses.append({"category": {"$in": category_candidates}})
    if use_case_candidates:
        clauses.append({"use_case": {"$in": use_case_candidates}})
    if population_candidates:
        clauses.append({"population": {"$in": population_candidates}})

    if not clauses:
        return None, None
    if category_candidates:
        relaxed_filter = {"category": {"$in": category_candidates}}
    if len(clauses) == 1:
        return clauses[0], relaxed_filter if relaxed_filter != clauses[0] else None
    return {"$and": clauses}, relaxed_filter


def _resolved_domain(state: GraphState, query: str) -> str:
    domain = str(state.get("domain") or "").strip()
    if domain in {"workout", "diet", "profile", "general"}:
        return domain
    resolution = state.get("context_resolution") or {}
    resolved_domain = str(resolution.get("resolved_domain") or "").strip()
    if resolved_domain in {"workout", "diet", "profile", "general"} and resolved_domain != "none":
        return resolved_domain
    return infer_domain(query)


def _external_categories_for_domain(domain: str) -> list[str]:
    if domain == "workout":
        return [
            "workout_resistance_guidelines",
            "workout_technique",
            "workout_program_design",
            "hypertrophy_volume",
            "hypertrophy_frequency",
            "cardio_guidelines",
            "hiit_programming",
            "hiit_efficiency",
            "mobility_pnf",
            "stretching_performance",
        ]
    if domain == "diet":
        return [
            "nutrition_kdri",
            "nutrition_protein",
            "nutrition_timing",
            "nutrition_allergy",
            "supplement_creatine",
            "supplement_omega3",
            "physique_cutting",
        ]
    return []


def _external_use_cases_for_request(domain: str, action_intent: str, query: str) -> list[str]:
    normalized = query.lower()
    if domain == "workout":
        use_cases = {
            "create": [
                "program_design",
                "novice_programming",
                "intermediate_programming",
                "cardio_programming",
                "mobility",
                "coaching",
            ],
            "modify": [
                "program_adjustment",
                "fatigue_management",
                "injury_prevention",
                "risk_screening",
                "mobility",
                "coaching",
            ],
            "info": [
                "program_design",
                "technique_cueing",
                "evidence_interpretation",
                "injury_prevention",
                "risk_screening",
                "mobility",
                "coaching",
            ],
        }.get(action_intent, ["program_design", "coaching", "evidence_interpretation"])
        if any(keyword in normalized for keyword in ("통증", "부상", "아픔", "무릎", "허리", "어깨")):
            use_cases.extend(["injury_prevention", "risk_screening", "mobility"])
        return list(dict.fromkeys(use_cases))

    if domain == "diet":
        use_cases = {
            "create": [
                "meal_planning",
                "training_day_nutrition",
                "muscle_gain",
                "fat_loss",
                "coaching",
            ],
            "modify": [
                "meal_planning",
                "fat_loss",
                "allergy_safe_planning",
                "coaching",
            ],
            "info": [
                "meal_planning",
                "training_day_nutrition",
                "supplement_use",
                "allergy_safe_planning",
                "evidence_interpretation",
                "coaching",
            ],
        }.get(action_intent, ["meal_planning", "coaching", "evidence_interpretation"])
        if any(keyword in normalized for keyword in ("알레르기", "유당", "갑각류", "계란", "우유", "견과")):
            use_cases.append("allergy_safe_planning")
        if any(keyword in normalized for keyword in ("보충제", "크레아틴", "오메가3")):
            use_cases.append("supplement_use")
        return list(dict.fromkeys(use_cases))

    return []


def _external_populations_for_profile(state: GraphState) -> list[str]:
    profile = state.get("user_profile") or {}
    populations: list[str] = []
    age = profile.get("age")
    if isinstance(age, (int, float)) and age >= 65:
        populations.append("older_adults")

    allergy_value = profile.get("allergies") or profile.get("allergy") or []
    if isinstance(allergy_value, list):
        allergy_text = " ".join(str(item) for item in allergy_value).lower()
    else:
        allergy_text = str(allergy_value).lower()
    if allergy_text:
        populations.append("food_allergy")

    return list(dict.fromkeys(populations))


def _should_skip_eval(state: GraphState, results: list[dict]) -> bool:
    if not results:
        return False
    intent = state.get("intent")

    if intent == INTENT_MODIFY:
        modify_context = state.get("modify_plan_context") or {}
        items = modify_context.get("items")
        return isinstance(items, list) and len(items) > 0

    if intent == INTENT_INFO:
        return _has_sufficient_info_results(results)

    return False


def _skip_eval_reason(state: GraphState, results: list[dict]) -> str:
    intent = state.get("intent")
    if intent == INTENT_MODIFY:
        return "modify_context_present"
    if intent == INTENT_INFO and _has_sufficient_info_results(results):
        return "info_results_sufficient"
    return "none"


def _has_sufficient_info_results(results: list[dict]) -> bool:
    strong_results = [
        result
        for result in results
        if float(result.get("score", 0.0) or 0.0) >= 0.55
        and len(str(result.get("text") or "")) >= 80
        and result.get("source") in {"external", "web", "important"}
    ]
    return len(strong_results) >= 2


def _accept_score_for_intent(intent: str) -> float:
    return _ACCEPT_SCORE_BY_INTENT.get(intent, 0.6)


def _retry_score_for_intent(intent: str) -> float:
    return _RETRY_SCORE_BY_INTENT.get(intent, 0.25)


def _max_retry_for_intent(intent: str) -> int:
    return _MAX_RETRY_BY_INTENT.get(intent, 0)


async def _parallel_search(
    deps: NodeDeps,
    user_id: str,
    query: str,
    vector: list[float],
    targets: list[str],
    *,
    external_filter: dict[str, Any] | None = None,
) -> list[dict]:
    tasks = []
    for target in targets:
        if target == "vdb_memory":
            tasks.append(deps.pinecone.search_memory(user_id, vector, TOP_K))
        elif target == "vdb_user_important":
            tasks.append(deps.pinecone.search_important(user_id, vector, TOP_K))
        elif target == "vdb_external":
            tasks.append(deps.pinecone.search_external(vector, TOP_K, metadata_filter=external_filter))
        elif target == "web":
            tasks.append(_web_search(deps, query))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    combined: list[dict] = []
    for result in results:
        if isinstance(result, list):
            combined.extend(result)
        else:
            logger.warning("Search target failed and was ignored: %s", result)
    return combined


async def _expand_external_results_if_needed(
    deps: NodeDeps,
    vector: list[float],
    targets: list[str],
    merged_results: list[dict],
    *,
    strict_filter: dict[str, Any] | None,
    relaxed_filter: dict[str, Any] | None,
) -> list[dict]:
    if "vdb_external" not in targets:
        return merged_results

    external_results = [result for result in merged_results if result.get("source") == "external"]
    if len(external_results) >= 2:
        return merged_results

    expanded_results = list(merged_results)
    if relaxed_filter and relaxed_filter != strict_filter:
        relaxed_results = await deps.pinecone.search_external(vector, TOP_K, metadata_filter=relaxed_filter)
        expanded_results = _merge_results(expanded_results + relaxed_results)
        external_results = [result for result in expanded_results if result.get("source") == "external"]
        if len(external_results) >= 2:
            return expanded_results

    if strict_filter:
        semantic_results = await deps.pinecone.search_external(vector, TOP_K)
        expanded_results = _merge_results(expanded_results + semantic_results)

    return expanded_results


async def _web_search(deps: NodeDeps, query: str) -> list[dict]:
    try:
        return await deps.router.search_web(query, max_results=min(TOP_K, 5))
    except Exception as exc:
        logger.warning("Web search failed and was ignored: %s", exc)
        return []


def _merge_results(results: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique: list[dict] = []

    for result in sorted(results, key=lambda item: item.get("score", 0.0), reverse=True):
        text = result.get("text", "")
        if text and text not in seen:
            seen.add(text)
            unique.append(result)

    return unique[:5]


async def _evaluate(deps: NodeDeps, query: str, results: list[dict]) -> float:
    if not results:
        return 0.0

    snippets = "\n".join(
        f"[{result.get('source', 'unknown')}] {result.get('text', '')[:200]}"
        for result in results[:5]
    )
    user_content = f"질문: {query}\n\n검색 결과:\n{snippets}"

    try:
        raw = await deps.router.generate(
            system_prompt=_EVAL_SYSTEM_PROMPT,
            user_content=user_content,
            response_schema=SearchEvalResponse,
        )
        evaluation = SearchEvalResponse.model_validate_json(raw)
        return evaluation.score
    except Exception as exc:
        logger.warning("Search evaluation failed, defaulting to 0.5: %s", exc)
        return 0.5


async def _regenerate_query(deps: NodeDeps, original: str, results: list[dict]) -> str:
    snippets = "\n".join(result.get("text", "")[:100] for result in results[:3])
    user_content = f"원래 질문: {original}\n\n부실했던 검색 결과:\n{snippets}"

    try:
        raw = await deps.router.generate(
            system_prompt=_QUERY_REGEN_PROMPT,
            user_content=user_content,
            response_schema=QueryRegenResponse,
        )
        regenerated = QueryRegenResponse.model_validate_json(raw)
        return regenerated.query
    except Exception:
        return original


def _degraded(state: GraphState, intent: str) -> dict:
    if intent == INTENT_CARE:
        return {
            "search_results": [],
            "search_quality": "degraded",
            "requires_past_memory": False,
        }

    return {
        "search_results": state.get("search_results") or [],
        "search_quality": "degraded",
    }
