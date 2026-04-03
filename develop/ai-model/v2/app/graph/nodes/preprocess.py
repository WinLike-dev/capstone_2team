"""전처리 노드 — Layer 3 전처리 상세 구현.

1. 턴별 State 초기화 (search_results · search_quality · profile_changes → reset)
2. pending_writes 재시도
3. 세션 첫 턴: WAS API 동기 호출 → user_profile + today_plan 캐싱
4. 이후 턴: State 캐시 사용
5. 턴 카운터 임계값 도달 시 대화 요약
"""
from __future__ import annotations

import json
import logging

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.graph.deps import NodeDeps
from app.schemas.state import GraphState

logger = logging.getLogger(__name__)

_SUMMARY_SYSTEM_PROMPT = """
당신은 대화 요약 전문가입니다.
주어진 대화에서 핵심 사실(운동 기록, 식단, 건강 변화 등)만 간결하게 요약하세요.
기존 user_profile에 이미 있는 정보는 제외하세요.
JSON 형식: {"summary": "...", "key_facts": ["...", "..."]}
"""


def make_preprocess_node(deps: NodeDeps):
    async def preprocess_node(state: GraphState) -> dict:
        settings = get_settings()
        updates: dict = {}

        # ── 1. 턴별 State 초기화 ────────────────────────────────────────────
        updates["search_results"] = []
        updates["search_quality"] = "ok"
        updates["profile_changes"] = None
        updates["modify_plan_context"] = None
        updates["self_eval_failure_reason"] = None
        updates["needs_clarification"] = False

        # ── 2. pending_writes 재시도 ─────────────────────────────────────────
        pending = list(state.get("pending_writes", []))
        still_pending = []
        for write in pending:
            try:
                await _execute_write(deps, state["user_id"], write)
                logger.info("pending_write 재시도 성공: %s", write["write_type"])
            except ExternalServiceError:
                still_pending.append(write)
                logger.warning("pending_write 재시도 실패 유지: %s", write["write_type"])
        updates["pending_writes"] = still_pending

        # ── 3/4. 세션 첫 턴 WAS 호출 vs 캐시 사용 ────────────────────────────
        if state.get("is_session_start", True):
            try:
                profile = await deps.was.get_user_profile(state["user_id"])
                today_plan = await deps.was.get_today_plan(state["user_id"])
                updates["user_profile"] = profile
                updates["today_plan"] = today_plan
                updates["is_session_start"] = False
                logger.info("세션 첫 턴 WAS 로드 완료: user_id=%s", state["user_id"])
            except ExternalServiceError as e:
                logger.error("세션 초기화 WAS 호출 실패: %s", e)
                updates["user_profile"] = state.get("user_profile")
                updates["today_plan"] = state.get("today_plan")
                updates["is_session_start"] = False

        # ── 5. 대화 요약 (임계값 배수 턴에서 실행) ──────────────────────────
        turn = state.get("turn_count", 0) + 1
        updates["turn_count"] = turn

        if turn > 0 and turn % settings.SUMMARY_TURN_INTERVAL == 0:
            messages = state.get("messages", [])
            if messages:
                await _run_summary(deps, state, messages, updates)

        return updates

    return preprocess_node


async def _execute_write(deps: NodeDeps, user_id: str, write: dict) -> None:
    wtype = write["write_type"]
    payload = write["payload"]
    if wtype == "profile":
        await deps.was.put_user_profile(user_id, payload)
    elif wtype == "plan_check":
        await deps.was.put_plan_check(user_id, payload["item_id"])
    elif wtype == "plan_create":
        await deps.was.post_plan_create(user_id, payload)
    elif wtype == "plan_update":
        await deps.was.put_plan_update(user_id, payload)


async def _run_summary(deps: NodeDeps, state: GraphState, messages: list, updates: dict) -> None:
    """오래된 메시지를 요약하고 핵심 팩트를 vdb_user_important에 저장."""
    conv_text = "\n".join(
        f"{m['role']}: {m['content']}" for m in messages
    )
    existing_profile = json.dumps(state.get("user_profile") or {}, ensure_ascii=False)
    user_content = f"user_profile 기존 필드:\n{existing_profile}\n\n대화:\n{conv_text}"

    try:
        raw = await deps.router.generate(
            system_prompt=_SUMMARY_SYSTEM_PROMPT,
            user_content=user_content,
            response_schema=dict,
        )
        result = json.loads(raw)
        updates["summary"] = result.get("summary", "")

        # 핵심 팩트 → vdb_user_important 저장
        key_facts: list[str] = result.get("key_facts", [])
        for fact in key_facts:
            vec = await deps.embed.embed(fact)
            await deps.pinecone.upsert_important(state["user_id"], vec, fact)

        logger.info("대화 요약 완료, 핵심 팩트 %d개 저장", len(key_facts))
    except Exception as e:
        logger.warning("대화 요약 실패 (무시): %s", e)
