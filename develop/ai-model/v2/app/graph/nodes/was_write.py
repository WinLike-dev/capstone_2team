"""비동기 WAS 쓰기 — Layer 3 비동기 WAS 쓰기 구현.

응답 출력 후 백그라운드에서 실행된다.
실패 시 State.pending_writes에 기록 → 다음 턴 전처리에서 재시도.

FastAPI BackgroundTasks에서 호출되는 함수로 구현.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.core.exceptions import ExternalServiceError
from app.graph.deps import NodeDeps
from app.schemas.state import PendingWrite

logger = logging.getLogger(__name__)

_PLAN_EXTRACT_PROMPT = """\
아래 AI 응답에서 운동/식단 계획 데이터를 JSON으로 추출하세요.
응답에 구체적인 계획이 없으면 has_plan: false를 반환하세요.

JSON 형식:
{
  "has_plan": true/false,
  "plan_type": "workout" | "diet",
  "items": [
    {"name": "항목명", "detail": "상세 내용 (세트/횟수/시간/칼로리 등)", "day": "요일 또는 날짜"}
  ]
}
"""

_PLAN_MODIFY_PROMPT = """\
아래 원본 플랜과 AI 수정 응답을 비교하여, 수정이 반영된 최종 플랜을 JSON으로 반환하세요.
변경된 부분만이 아닌, 수정이 적용된 **전체** 플랜을 반환해야 합니다.
응답에 실질적인 수정이 없으면 has_changes: false를 반환하세요.

JSON 형식:
{
  "has_changes": true/false,
  "plan_type": "workout" | "diet",
  "items": [
    {"name": "항목명", "detail": "상세 내용", "day": "요일 또는 날짜"}
  ]
}
"""


async def execute_was_writes(
    deps: NodeDeps,
    user_id: str,
    intent: str,
    response: str,
    profile_changes: dict[str, Any] | None,
    today_plan: list[dict] | None,
    search_results: list[dict] | None,
    modify_target: str | None,
    modify_plan_context: dict | None,
) -> list[PendingWrite]:
    """WAS 쓰기 실행. 실패한 항목은 pending_writes로 반환."""
    pending: list[PendingWrite] = []

    # ── profile 변경 ──────────────────────────────────────────────────────────
    if intent == "기록" and profile_changes:
        # plan_check 완료 처리
        if "item_id" in profile_changes:
            write: PendingWrite = {"write_type": "plan_check", "payload": profile_changes}
            try:
                await deps.was.put_plan_check(user_id, profile_changes["item_id"])
                logger.info("plan_check WAS 쓰기 성공: %s", profile_changes["item_id"])
            except ExternalServiceError as e:
                logger.warning("plan_check WAS 쓰기 실패: %s", e)
                pending.append(write)
        else:
            write = {"write_type": "profile", "payload": profile_changes}
            try:
                await deps.was.put_user_profile(user_id, profile_changes)
                logger.info("profile WAS 쓰기 성공")
            except ExternalServiceError as e:
                logger.warning("profile WAS 쓰기 실패: %s", e)
                pending.append(write)

    # ── 계획 생성 ─────────────────────────────────────────────────────────────
    if intent == "계획" and response:
        plan_payload = await _extract_plan_from_response(deps, response)
        if plan_payload:
            write = {"write_type": "plan_create", "payload": plan_payload}
            try:
                await deps.was.post_plan_create(user_id, plan_payload)
                logger.info("plan_create WAS 쓰기 성공")
            except ExternalServiceError as e:
                logger.warning("plan_create WAS 쓰기 실패: %s", e)
                pending.append(write)
        else:
            logger.info("응답에서 구조화된 플랜을 추출하지 못함, WAS 쓰기 스킵")

    # ── 수정 ──────────────────────────────────────────────────────────────────
    if intent == "수정" and modify_plan_context and response:
        modified_payload = await _extract_modified_plan(deps, modify_plan_context, response)
        if modified_payload:
            write = {"write_type": "plan_update", "payload": modified_payload}
            try:
                await deps.was.put_plan_update(user_id, modified_payload)
                logger.info("plan_update WAS 쓰기 성공")
            except ExternalServiceError as e:
                logger.warning("plan_update WAS 쓰기 실패: %s", e)
                pending.append(write)
        else:
            logger.info("수정된 플랜을 추출하지 못함, WAS 쓰기 스킵")

    return pending


async def _extract_plan_from_response(deps: NodeDeps, response: str) -> dict | None:
    """LLM 응답 텍스트에서 구조화된 플랜 데이터를 추출한다."""
    try:
        raw = await deps.router.generate(
            system_prompt=_PLAN_EXTRACT_PROMPT,
            user_content=f"AI 응답:\n{response}",
            response_schema=dict,
        )
        result = json.loads(raw)
        if result.get("has_plan") and result.get("items"):
            return result
        return None
    except Exception as e:
        logger.warning("플랜 추출 실패: %s", e)
        return None


async def _extract_modified_plan(
    deps: NodeDeps, original_plan: dict, response: str
) -> dict | None:
    """원본 플랜 + AI 수정 응답에서 수정된 최종 플랜을 추출한다."""
    original_json = json.dumps(original_plan, ensure_ascii=False)[:1000]
    try:
        raw = await deps.router.generate(
            system_prompt=_PLAN_MODIFY_PROMPT,
            user_content=f"원본 플랜:\n{original_json}\n\nAI 수정 응답:\n{response}",
            response_schema=dict,
        )
        result = json.loads(raw)
        if result.get("has_changes") and result.get("items"):
            return result
        return None
    except Exception as e:
        logger.warning("수정 플랜 추출 실패: %s", e)
        return None

