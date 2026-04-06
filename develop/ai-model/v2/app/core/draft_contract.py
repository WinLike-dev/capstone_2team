"""Helpers for the structured Draft -> Persona contract."""
from __future__ import annotations

from typing import Any

from app.schemas.state import DraftComponents


def _clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _clean_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    cleaned: list[str] = []
    for value in values:
        text = _clean_text(value)
        if text:
            cleaned.append(text)
    return cleaned


def normalize_draft_components(
    payload: dict[str, Any] | None,
    fallback_text: str | None = None,
) -> DraftComponents:
    if not payload:
        text = _clean_text(fallback_text) or "무엇을 도와드릴까요?"
        return {
            "core_message": text,
            "reason_points": [],
            "suggested_action": "",
            "safety_notes": [],
            "approval_question": None,
            "search_grounding_summary": "",
        }

    core_message = _clean_text(payload.get("core_message")) or _clean_text(fallback_text) or "무엇을 도와드릴까요?"
    approval_question = _clean_text(payload.get("approval_question")) or None

    return {
        "core_message": core_message,
        "reason_points": _clean_list(payload.get("reason_points")),
        "suggested_action": _clean_text(payload.get("suggested_action")),
        "safety_notes": _clean_list(payload.get("safety_notes")),
        "approval_question": approval_question,
        "search_grounding_summary": _clean_text(payload.get("search_grounding_summary")),
    }


def render_draft_preview(components: DraftComponents) -> str:
    parts: list[str] = []

    if components["core_message"]:
        parts.append(components["core_message"])

    if components["search_grounding_summary"]:
        parts.append(f"근거 요약: {components['search_grounding_summary']}")

    if components["reason_points"]:
        reasons = "\n".join(f"- {item}" for item in components["reason_points"])
        parts.append(f"이유:\n{reasons}")

    if components["suggested_action"]:
        parts.append(f"제안: {components['suggested_action']}")

    if components["safety_notes"]:
        notes = "\n".join(f"- {item}" for item in components["safety_notes"])
        parts.append(f"주의:\n{notes}")

    if components["approval_question"]:
        parts.append(components["approval_question"])

    return "\n\n".join(part for part in parts if part).strip()
