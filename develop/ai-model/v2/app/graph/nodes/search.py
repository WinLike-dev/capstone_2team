"""Search pipeline node for vector and web retrieval."""
from __future__ import annotations

import asyncio
import logging
import time

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
_WEB_ENABLED_INTENTS = {INTENT_PLAN, INTENT_INFO}
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
        query = state.get("search_query") or state["user_message"]
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

        raw_results = await _parallel_search(deps, state["user_id"], query, query_vec, targets)
        merged_results = _merge_results(raw_results)

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
            new_query = await _regenerate_query(deps, state["user_message"], merged_results)
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


def _normalize_targets(state: GraphState, query: str, targets: list[str]) -> list[str]:
    normalized = list(dict.fromkeys(targets))
    intent = state.get("intent")

    if intent == INTENT_MODIFY:
        return [target for target in normalized if target != "web"]

    if intent == INTENT_INFO and "web" in normalized and not _info_needs_web(query):
        return [target for target in normalized if target != "web"]

    return normalized


def _info_needs_web(query: str) -> bool:
    normalized = query.strip().lower()
    return any(keyword in normalized for keyword in _INFO_WEB_KEYWORDS)


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
) -> list[dict]:
    tasks = []
    for target in targets:
        if target == "vdb_memory":
            tasks.append(deps.pinecone.search_memory(user_id, vector, TOP_K))
        elif target == "vdb_user_important":
            tasks.append(deps.pinecone.search_important(user_id, vector, TOP_K))
        elif target == "vdb_external":
            tasks.append(deps.pinecone.search_external(vector, TOP_K))
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
