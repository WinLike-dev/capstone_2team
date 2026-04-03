"""검색 파이프라인 노드 — Layer 3 검색 파이프라인 상세 구현.

1. search_targets 기반 VDB 병렬 검색
2. 결과 병합 (중복 제거 · 우선순위 정렬 · 출처 태깅)
3. Flash-Lite 결과 평가 (score 산출)
4. score < 0.4: 쿼리 재생성 → 재시도
   score 0.4~0.7: 검색 재시도
   score > 0.7: 통과
5. max_retry=3 초과 시 Graceful Degradation
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from app.graph.deps import NodeDeps
from app.schemas.state import GraphState

logger = logging.getLogger(__name__)

MAX_RETRY = 3
TOP_K = 5

_EVAL_SYSTEM_PROMPT = """
당신은 검색 결과 품질 평가 전문가입니다.
사용자 질문에 대한 검색 결과의 관련성을 0.0~1.0 점수로 평가하세요.
JSON: {"score": 0.0~1.0, "reason": "한 줄 이유"}
"""

_QUERY_REGEN_PROMPT = """
검색 결과가 부족합니다. 사용자 질문에 더 적합한 검색 쿼리를 한 문장으로 재생성하세요.
JSON: {"query": "재생성된 검색 쿼리"}
"""


def make_search_node(deps: NodeDeps):
    async def search_node(state: GraphState) -> dict:
        query = state.get("search_query") or state["user_message"]
        targets = state.get("search_targets") or []
        retry_count = state.get("search_retry_count", 0)
        intent = state.get("intent", "")

        if not targets:
            return {"search_results": [], "search_quality": "ok"}

        # ── 벡터 임베딩 ──────────────────────────────────────────────────────
        try:
            query_vec = await deps.embed.embed(query)
        except Exception as e:
            logger.error("임베딩 생성 실패: %s", e)
            return _degraded(state, intent)

        # ── 병렬 검색 ────────────────────────────────────────────────────────
        raw_results = await _parallel_search(deps, state["user_id"], query_vec, targets)

        # ── 결과 병합 ────────────────────────────────────────────────────────
        merged = _merge_results(raw_results)

        # ── Flash-Lite 품질 평가 ─────────────────────────────────────────────
        score = await _evaluate(deps, query, merged)
        logger.info("검색 품질 평가: score=%.2f, retry=%d", score, retry_count)

        if score >= 0.7:
            return {"search_results": merged, "search_quality": "ok", "search_retry_count": retry_count}

        if retry_count >= MAX_RETRY:
            return _degraded(state, intent)

        if score < 0.4:
            # 쿼리 재생성 후 재시도
            new_query = await _regenerate_query(deps, state["user_message"], merged)
            return {
                "search_query": new_query,
                "search_retry_count": retry_count + 1,
            }
        else:
            # 검색 재시도 (동일 쿼리)
            return {"search_retry_count": retry_count + 1}

    return search_node


# ── 병렬 검색 ─────────────────────────────────────────────────────────────────

async def _parallel_search(
    deps: NodeDeps, user_id: str, vec: list[float], targets: list[str]
) -> list[dict]:
    tasks = []
    for target in targets:
        if target == "vdb_memory":
            tasks.append(deps.pinecone.search_memory(user_id, vec, TOP_K))
        elif target == "vdb_user_important":
            tasks.append(deps.pinecone.search_important(user_id, vec, TOP_K))
        elif target == "vdb_external":
            tasks.append(deps.pinecone.search_external(vec, TOP_K))
        elif target == "web":
            tasks.append(_web_search_stub(vec))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    combined: list[dict] = []
    for r in results:
        if isinstance(r, list):
            combined.extend(r)
        else:
            logger.warning("검색 일부 실패 (무시): %s", r)
    return combined


async def _web_search_stub(_vec: list[float]) -> list[dict]:
    """웹 검색 플레이스홀더 — 향후 Google Search API 연동."""
    return []


# ── 결과 병합 ─────────────────────────────────────────────────────────────────

def _merge_results(results: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique: list[dict] = []
    for r in sorted(results, key=lambda x: x.get("score", 0.0), reverse=True):
        text = r.get("text", "")
        if text and text not in seen:
            seen.add(text)
            unique.append(r)
    return unique[:10]


# ── Flash-Lite 품질 평가 ──────────────────────────────────────────────────────

async def _evaluate(deps: NodeDeps, query: str, results: list[dict]) -> float:
    if not results:
        return 0.0
    snippets = "\n".join(f"[{r.get('source', 'unknown')}] {r.get('text', '')[:200]}" for r in results[:5])
    user_content = f"질문: {query}\n\n검색 결과:\n{snippets}"
    try:
        raw = await deps.router.generate(
            system_prompt=_EVAL_SYSTEM_PROMPT,
            user_content=user_content,
            response_schema=dict,
        )
        return float(json.loads(raw).get("score", 0.5))
    except Exception as e:
        logger.warning("품질 평가 실패, 기본값 0.5 사용: %s", e)
        return 0.5


# ── 쿼리 재생성 ────────────────────────────────────────────────────────────────

async def _regenerate_query(deps: NodeDeps, original: str, results: list[dict]) -> str:
    snippets = "\n".join(r.get("text", "")[:100] for r in results[:3])
    user_content = f"원래 질문: {original}\n\n기존 검색 결과(불충분):\n{snippets}"
    try:
        raw = await deps.router.generate(
            system_prompt=_QUERY_REGEN_PROMPT,
            user_content=user_content,
            response_schema=dict,
        )
        return json.loads(raw).get("query", original)
    except Exception:
        return original


# ── Graceful Degradation ──────────────────────────────────────────────────────

def _degraded(state: GraphState, intent: str) -> dict:
    if intent == "공감_케어":
        return {
            "search_results": [],
            "search_quality": "degraded",
            "requires_past_memory": False,
        }
    return {
        "search_results": state.get("search_results") or [],
        "search_quality": "degraded",
    }
