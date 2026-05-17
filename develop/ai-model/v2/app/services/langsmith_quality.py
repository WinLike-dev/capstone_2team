"""Quality evaluation and optional LangSmith export for AI traces."""
from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.config import Settings
from app.core.trace_store import TraceStore

logger = logging.getLogger(__name__)

QUALITY_VERSION = "quality-v1"
PASS_THRESHOLD = 0.75
REVIEW_THRESHOLD = 0.55


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _clamp_score(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)


def _hash_id(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _response_text(trace: dict[str, Any]) -> str:
    response = trace.get("response")
    if isinstance(response, dict):
        value = response.get("response")
        if value is not None:
            return str(value)
    if response is None:
        return ""
    return str(response)


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _trace_uuid(trace_id: str) -> UUID:
    return UUID(hex=trace_id.replace("-", ""))


def _issue(
    issues: list[dict[str, Any]],
    *,
    severity: str,
    code: str,
    message: str,
    penalty: float,
) -> None:
    issues.append(
        {
            "severity": severity,
            "code": code,
            "message": message,
            "penalty": penalty,
        }
    )


def evaluate_trace_quality(trace: dict[str, Any]) -> dict[str, Any]:
    """Create a compact, deterministic quality report for a completed trace."""
    state_summary = trace.get("state_summary") or {}
    response_payload = trace.get("response") or {}
    response_text = _response_text(trace).strip()
    response_length = len(response_text)
    status = str(trace.get("status") or "")
    action_intent = state_summary.get("action_intent")
    intent = state_summary.get("intent")
    search_quality = state_summary.get("search_quality")
    search_results_count = int(state_summary.get("search_results_count") or 0)
    proposed_plan_count = int(state_summary.get("proposed_plan_count") or 0)
    pending_writes_count = int(state_summary.get("pending_writes_count") or 0)
    needs_clarification = bool(state_summary.get("needs_clarification"))
    draft_components = state_summary.get("draft_components") or {}

    issues: list[dict[str, Any]] = []

    if status not in {"response_sent", "completed"}:
        _issue(
            issues,
            severity="critical",
            code="trace_not_completed",
            message=f"Trace completed with status '{status}'.",
            penalty=0.45,
        )
    if not response_text:
        _issue(
            issues,
            severity="critical",
            code="empty_response",
            message="Response text is empty.",
            penalty=0.60,
        )
    elif response_length < 20 and action_intent not in {"approval", "record"}:
        _issue(
            issues,
            severity="warning",
            code="very_short_response",
            message="Response may be too short for the detected task.",
            penalty=0.12,
        )

    lowered = response_text.lower()
    fallback_markers = ("오류", "다시 시도", "error", "failed", "fallback")
    if any(marker in lowered for marker in fallback_markers):
        _issue(
            issues,
            severity="warning",
            code="fallback_or_error_language",
            message="Response contains fallback or error-like wording.",
            penalty=0.18,
        )
    if action_intent == "fallback":
        _issue(
            issues,
            severity="warning",
            code="fallback_intent_selected",
            message="Intent routing selected fallback clarification.",
            penalty=0.22,
        )

    if search_quality == "degraded":
        _issue(
            issues,
            severity="warning",
            code="degraded_search",
            message="Search quality was degraded during generation.",
            penalty=0.18,
        )
    if action_intent == "info" and search_results_count == 0 and search_quality != "ok":
        _issue(
            issues,
            severity="warning",
            code="info_without_retrieval",
            message="Information request did not retain usable retrieval evidence.",
            penalty=0.15,
        )

    if action_intent in {"create", "modify"} and proposed_plan_count == 0 and not needs_clarification:
        _issue(
            issues,
            severity="critical",
            code="missing_plan_proposal",
            message="Plan request finished without a proposed plan or clarification state.",
            penalty=0.35,
        )

    if action_intent == "approval" and pending_writes_count > 0:
        _issue(
            issues,
            severity="warning",
            code="approval_pending_write",
            message="Approval response left writes pending.",
            penalty=0.20,
        )

    if action_intent == "safety" and not draft_components.get("safety_notes"):
        _issue(
            issues,
            severity="warning",
            code="safety_notes_missing",
            message="Safety intent did not expose structured safety notes.",
            penalty=0.20,
        )

    issue_penalty = sum(float(item["penalty"]) for item in issues)
    response_completeness = _clamp_score(
        1.0
        - sum(
            item["penalty"]
            for item in issues
            if item["code"] in {"trace_not_completed", "empty_response", "very_short_response"}
        )
    )
    intent_alignment = _clamp_score(
        1.0
        - sum(
            item["penalty"]
            for item in issues
            if item["code"] in {"missing_plan_proposal", "approval_pending_write"}
        )
    )
    grounding = _clamp_score(0.72 if search_quality == "degraded" else 0.95 if search_results_count else 0.82)
    safety = _clamp_score(0.72 if any(item["code"] == "safety_notes_missing" for item in issues) else 0.95)
    actionability = _clamp_score(
        0.95
        if proposed_plan_count or action_intent in {"record", "approval", "safety"}
        else 0.86
        if draft_components.get("suggested_action")
        else 0.72
    )

    overall = _clamp_score(
        0.30 * response_completeness
        + 0.25 * intent_alignment
        + 0.15 * grounding
        + 0.15 * safety
        + 0.15 * actionability
        - max(0.0, issue_penalty - 0.25) * 0.20
    )
    if any(item["severity"] == "critical" for item in issues):
        overall = min(overall, 0.54)
    grade = (
        "pass"
        if overall >= PASS_THRESHOLD
        else "review"
        if overall >= REVIEW_THRESHOLD
        else "fail"
    )

    return {
        "version": QUALITY_VERSION,
        "evaluated_at": _utcnow_iso(),
        "score": overall,
        "grade": grade,
        "dimensions": {
            "response_completeness": response_completeness,
            "intent_alignment": intent_alignment,
            "grounding": grounding,
            "safety": safety,
            "actionability": actionability,
        },
        "signals": {
            "intent": intent,
            "action_intent": action_intent,
            "domain": state_summary.get("domain"),
            "response_length": response_length,
            "search_quality": search_quality,
            "search_results_count": search_results_count,
            "proposed_plan_count": proposed_plan_count,
            "pending_writes_count": pending_writes_count,
            "plan_sync_applied": (
                response_payload.get("plan_sync_applied")
                if isinstance(response_payload, dict)
                else None
            ),
            "needs_clarification": needs_clarification,
        },
        "issue_count": len(issues),
        "issues": issues,
    }


def record_quality_for_trace(trace_store: TraceStore, trace_id: str) -> dict[str, Any] | None:
    trace = trace_store.get_trace(trace_id)
    if not trace:
        return None
    quality = evaluate_trace_quality(trace)
    trace_store.record_quality(trace_id, quality)
    return quality


def _node_event_summary(trace: dict[str, Any]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for event in trace.get("events") or []:
        detail = event.get("detail") or {}
        compact_detail = {
            key: value
            for key, value in detail.items()
            if key
            in {
                "reason",
                "raw_intent",
                "coerced_intent",
                "confidence",
                "fallback_reason",
                "resolved_reference",
                "resolved_domain",
                "ambiguous",
                "targets",
            }
        }
        if "signals" in detail:
            signals = detail.get("signals") or {}
            compact_detail["signals"] = {
                key: signals.get(key)
                for key in (
                    "inferred_domain",
                    "resolved_reference",
                    "resolved_domain",
                    "context_ambiguous",
                    "safety_match",
                    "care_match",
                    "health_context_match",
                    "offtopic_match",
                    "question_followup_match",
                    "plan_request_match",
                    "info_request_match",
                    "modify_request_match",
                    "profile_record_match",
                    "memory_query_match",
                    "has_question_mark",
                )
                if key in signals
            }
        summary.append(
            {
                "stage": event.get("stage"),
                "status": event.get("status"),
                "title": event.get("title"),
                "detail": compact_detail,
                "duration_ms": event.get("duration_ms"),
            }
        )
    return summary


def _fallback_diagnosis(trace: dict[str, Any]) -> dict[str, Any] | None:
    state_summary = trace.get("state_summary") or {}
    if state_summary.get("action_intent") != "fallback" and not any(
        event.get("stage") == "fallback" for event in trace.get("events") or []
    ):
        return None

    diagnosis = {
        "action_intent": state_summary.get("action_intent"),
        "domain": state_summary.get("domain"),
        "reason": "unknown",
        "intent_signals": {},
    }
    for event in trace.get("events") or []:
        if event.get("stage") == "intent" and event.get("title") in {
            "Intent fallback selected",
            "LLM intent decision",
        }:
            detail = event.get("detail") or {}
            diagnosis["reason"] = detail.get("reason") or detail.get("fallback_reason") or diagnosis["reason"]
            diagnosis["intent_signals"] = detail.get("signals") or diagnosis["intent_signals"]
    return diagnosis


@dataclass(frozen=True)
class LangSmithQualityExporter:
    enabled: bool
    api_key: str | None
    api_url: str
    project_name: str
    send_full_text: bool = False

    @classmethod
    def from_settings(cls, settings: Settings) -> "LangSmithQualityExporter":
        api_key = settings.LANGSMITH_API_KEY or settings.LANGCHAIN_API_KEY
        api_url = settings.LANGSMITH_ENDPOINT or settings.LANGCHAIN_ENDPOINT
        project_name = settings.LANGSMITH_PROJECT or settings.LANGCHAIN_PROJECT
        return cls(
            enabled=settings.LANGSMITH_QUALITY_ENABLED,
            api_key=api_key,
            api_url=api_url,
            project_name=project_name,
            send_full_text=settings.LANGSMITH_SEND_FULL_TEXT,
        )

    @property
    def configured(self) -> bool:
        return bool(self.enabled and self.api_key)

    async def export_trace(self, trace: dict[str, Any]) -> dict[str, Any]:
        if not self.configured:
            return {
                "enabled": self.enabled,
                "sent": False,
                "reason": "disabled_or_missing_api_key",
            }
        return await asyncio.to_thread(self._export_trace_sync, trace)

    def _export_trace_sync(self, trace: dict[str, Any]) -> dict[str, Any]:
        from langsmith import Client

        quality = trace.get("quality") or evaluate_trace_quality(trace)
        trace_id = str(trace.get("trace_id") or "")
        run_id = _trace_uuid(trace_id)
        client = Client(api_key=self.api_key, api_url=self.api_url)

        client.create_run(
            name=f"ai-hub.{trace.get('kind') or 'request'}",
            inputs=self._build_inputs(trace),
            run_type="chain",
            id=run_id,
            project_name=self.project_name,
            outputs=self._build_outputs(trace, quality),
            start_time=_parse_dt(trace.get("started_at")),
            end_time=_parse_dt(trace.get("completed_at")),
            extra={
                "metadata": {
                    "local_trace_id": trace_id,
                    "kind": trace.get("kind"),
                    "status": trace.get("status"),
                    "quality_grade": quality.get("grade"),
                    "quality_version": quality.get("version"),
                },
            },
            tags=["ai-hub-v2", "quality-eval", str(trace.get("kind") or "request")],
        )

        self._create_feedback(client, run_id, quality)
        return {
            "enabled": True,
            "sent": True,
            "project": self.project_name,
            "run_id": str(run_id),
            "sent_at": _utcnow_iso(),
        }

    def _build_inputs(self, trace: dict[str, Any]) -> dict[str, Any]:
        message = str(trace.get("message") or "")
        request_payload = trace.get("request_payload") or {}
        inputs = {
            "kind": trace.get("kind"),
            "local_trace_id": trace.get("trace_id"),
            "user_id_hash": _hash_id(trace.get("user_id")),
            "session_id_hash": _hash_id(trace.get("session_id")),
            "message_length": len(message),
            "metadata": trace.get("metadata") or {},
        }
        if self.send_full_text:
            inputs["message"] = message
            inputs["request_payload"] = request_payload
        return inputs

    def _build_outputs(self, trace: dict[str, Any], quality: dict[str, Any]) -> dict[str, Any]:
        response_text = _response_text(trace)
        outputs = {
            "status": trace.get("status"),
            "state_summary": trace.get("state_summary") or {},
            "node_events": _node_event_summary(trace),
            "fallback_diagnosis": _fallback_diagnosis(trace),
            "response_length": len(response_text),
            "quality": quality,
        }
        if self.send_full_text:
            outputs["response"] = response_text
        return outputs

    def _create_feedback(self, client: Any, run_id: UUID, quality: dict[str, Any]) -> None:
        source_info = {
            "source": "ai-hub-v2-heuristic",
            "quality_version": quality.get("version"),
        }
        client.create_feedback(
            run_id=run_id,
            trace_id=run_id,
            key="overall_quality",
            score=quality.get("score"),
            value=quality.get("grade"),
            comment=_quality_comment(quality),
            source_info=source_info,
        )
        for key, score in (quality.get("dimensions") or {}).items():
            client.create_feedback(
                run_id=run_id,
                trace_id=run_id,
                key=f"quality.{key}",
                score=score,
                source_info=source_info,
            )


def _quality_comment(quality: dict[str, Any]) -> str:
    issues = quality.get("issues") or []
    if not issues:
        return "No heuristic quality issues detected."
    return "; ".join(f"{item.get('code')}: {item.get('message')}" for item in issues[:4])


async def export_quality_trace(
    *,
    exporter: LangSmithQualityExporter | None,
    trace_store: TraceStore,
    trace_id: str,
) -> None:
    if not exporter or not exporter.configured:
        return

    trace = trace_store.get_trace(trace_id)
    if not trace:
        return
    if not trace.get("quality"):
        quality = evaluate_trace_quality(trace)
        trace_store.record_quality(trace_id, quality)
        trace = trace_store.get_trace(trace_id) or trace

    try:
        result = await exporter.export_trace(trace)
        trace_store.update_metadata(trace_id, langsmith_export=result)
        if result.get("sent"):
            trace_store.record_event(
                trace_id,
                stage="quality_export",
                status="ok",
                title="LangSmith quality export completed",
                detail={
                    "project": result.get("project"),
                    "run_id": result.get("run_id"),
                },
            )
    except Exception as exc:
        logger.warning("LangSmith quality export failed: %s", exc)
        trace_store.update_metadata(
            trace_id,
            langsmith_export={
                "enabled": True,
                "sent": False,
                "error": str(exc),
                "failed_at": _utcnow_iso(),
            },
        )
        trace_store.record_alert(
            trace_id,
            severity="warning",
            message="LangSmith quality export failed",
            detail={"error": str(exc)},
        )
