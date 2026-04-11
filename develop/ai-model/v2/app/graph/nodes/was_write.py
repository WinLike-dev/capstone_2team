"""Background WAS write helpers executed after the response is returned."""
from __future__ import annotations

import json
import logging
from typing import Any, TypedDict

from app.core.exceptions import ExternalServiceError
from app.graph.deps import NodeDeps
from app.schemas.llm_responses import PlanExtractResponse, PlanModifyResponse
from app.schemas.state import PendingWrite
from app.schemas.was import to_plan_create, to_plan_update

logger = logging.getLogger(__name__)

_PLAN_EXTRACT_PROMPT = """\
아래 AI 응답에서 운동/식단 계획 데이터를 JSON으로 추출하세요.
응답에 구체적인 계획이 없으면 has_plan: false를 반환하세요.

JSON 형식:
{
  "has_plan": true/false,
  "plan_type": "workout" | "diet",
  "items": [
    {
      "name": "항목명",
      "detail": "상세 내용",
      "day": "YYYY-MM-DD 날짜",
      "ex_list": [{"exercise_name": "운동명", "sets": 3}]
    }
  ]
}
"""

_PLAN_MODIFY_PROMPT = """\
아래 원본 계획과 AI 수정 응답을 비교하여, 수정이 반영된 최종 계획을 JSON으로 반환하세요.
변경된 부분만이 아니라 수정 후 전체 계획을 반환해야 합니다.
실질적인 수정이 없으면 has_changes: false를 반환하세요.

JSON 형식:
{
  "has_changes": true/false,
  "plan_type": "workout" | "diet",
  "items": [
    {
      "name": "항목명",
      "detail": "상세 내용",
      "day": "YYYY-MM-DD 날짜",
      "ex_list": [{"exercise_name": "운동명", "sets": 3}]
    }
  ]
}
"""


class WriteExecutionResult(TypedDict):
    pending: list[PendingWrite]
    write_succeeded: bool


async def execute_was_writes(
    deps: NodeDeps,
    user_id: str,
    intent: str,
    response: str,
    record_type: str | None,
    profile_changes: dict[str, Any] | None,
    today_plan: list[dict] | None,
    search_results: list[dict] | None,
    modify_target: str | None,
    modify_plan_context: dict | None,
    proposed_plan: list[dict] | None,
    proposed_plan_type: str | None,
    proposed_plan_action: str | None,
) -> WriteExecutionResult:
    """Execute WAS writes and return pending retries plus approval success state."""

    pending: list[PendingWrite] = []
    write_succeeded = False

    if intent == "기록" and profile_changes:
        if record_type == "plan_check":
            item_id = profile_changes.get("item_id")
            if item_id:
                write: PendingWrite = {"write_type": "plan_check", "payload": profile_changes}
                try:
                    await deps.was.put_plan_check(user_id, item_id)
                    logger.info("plan_check WAS write succeeded: %s", item_id)
                except ExternalServiceError as exc:
                    logger.warning("plan_check WAS write failed: %s", exc)
                    pending.append(write)
        elif record_type == "profile":
            write = {"write_type": "profile", "payload": profile_changes}
            try:
                await deps.was.put_user_profile(user_id, profile_changes)
                logger.info("profile WAS write succeeded")
            except ExternalServiceError as exc:
                logger.warning("profile WAS write failed: %s", exc)
                pending.append(write)

    if intent == "계획_승인" and proposed_plan:
        resolved_plan_type = proposed_plan_type or modify_target or "workout"
        write_type = "plan_update" if proposed_plan_action == "update" else "plan_create"
        raw_payload = {
            "plan_type": resolved_plan_type,
            "items": proposed_plan,
        }

        try:
            if write_type == "plan_update":
                plan_payload = to_plan_update(
                    {
                        "has_changes": True,
                        **raw_payload,
                    }
                )
            else:
                plan_payload = to_plan_create(
                    {
                        "has_plan": True,
                        **raw_payload,
                    }
                )
        except Exception as exc:
            logger.exception("계획_승인 WAS payload 변환 실패: %s", exc)
            return {"pending": pending, "write_succeeded": False}

        if not plan_payload:
            logger.warning("계획_승인 WAS write skipped: plan payload generation returned empty")
            return {"pending": pending, "write_succeeded": False}

        write = {"write_type": write_type, "payload": plan_payload}
        try:
            if write_type == "plan_update":
                await deps.was.put_plan_update(user_id, plan_payload)
            else:
                await deps.was.post_plan_create(user_id, plan_payload)
            logger.info("계획_승인 WAS write succeeded (%s)", write_type)
            write_succeeded = True
        except ExternalServiceError as exc:
            logger.warning("계획_승인 WAS write failed: %s", exc)
            pending.append(write)

    return {"pending": pending, "write_succeeded": write_succeeded}


async def _extract_plan_from_response(deps: NodeDeps, response: str) -> dict | None:
    """Extract a structured plan from a free-form AI response."""

    try:
        raw = await deps.router.generate(
            system_prompt=_PLAN_EXTRACT_PROMPT,
            user_content=f"AI 응답:\n{response}",
            response_schema=PlanExtractResponse,
        )
        result = PlanExtractResponse.model_validate_json(raw)
        if result.has_plan and result.items:
            return result.model_dump()
        return None
    except Exception as exc:
        logger.warning("Plan extraction failed: %s", exc)
        return None


async def _extract_modified_plan(
    deps: NodeDeps, original_plan: dict, response: str
) -> dict | None:
    """Extract a fully modified plan from the original plan plus AI response."""

    original_json = json.dumps(original_plan, ensure_ascii=False)[:1000]
    try:
        raw = await deps.router.generate(
            system_prompt=_PLAN_MODIFY_PROMPT,
            user_content=f"원본 계획:\n{original_json}\n\nAI 수정 응답:\n{response}",
            response_schema=PlanModifyResponse,
        )
        result = PlanModifyResponse.model_validate_json(raw)
        if result.has_changes and result.items:
            return result.model_dump()
        return None
    except Exception as exc:
        logger.warning("Modified plan extraction failed: %s", exc)
        return None
