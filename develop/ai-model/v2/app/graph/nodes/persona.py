"""Persona node for tone polishing and final response generation."""
from __future__ import annotations

import json
import logging
import re
import time

from pydantic import BaseModel, Field

from app.core.draft_contract import normalize_draft_components, render_draft_preview
from app.core.persona_registry import resolve_persona
from app.graph.deps import NodeDeps
from app.schemas.state import GraphState

logger = logging.getLogger(__name__)


class PersonaResponse(BaseModel):
    response: str = Field(description="Final message shown to the user")


def _selected_persona_id(profile: dict) -> str | None:
    persona_id = profile.get("selected_ai_persona")
    if isinstance(persona_id, str) and persona_id.strip():
        return persona_id.strip()
    return None


def _dedupe_repeated_sentences(text: str) -> str:
    chunks = [
        chunk.strip()
        for chunk in re.split(r"(?<=[.!?])\s+|\n+", text)
        if chunk.strip()
    ]
    if not chunks:
        return text.strip()

    normalized_seen: set[str] = set()
    deduped: list[str] = []
    for chunk in chunks:
        normalized = re.sub(r"\s+", " ", chunk).strip().lower()
        if normalized in normalized_seen:
            continue
        normalized_seen.add(normalized)
        deduped.append(chunk)

    if len(deduped) == 1:
        return deduped[0]
    return "\n".join(deduped)


def _is_plan_flow_intent(intent: str) -> bool:
    return intent in {"계획", "수정", "계획_승인"}


def _persona_guardrails(state: GraphState, draft_components: dict) -> str:
    intent = state.get("intent", "")
    lines = [
        "Global constraints:",
        "- Preserve the draft's main conclusion and factual scope.",
        "- Keep the response concise in the persona's style; do not expand into broader general advice.",
        "- Do not weaken or generalize specific reasoning that is already present in reason_points.",
        "- If approval_question exists, keep that approval flow in the final response.",
    ]
    if state.get("support_mode") == "care":
        lines.append("- Keep the tone warm and validating, but do not change the task outcome or factual content.")

    if intent == "정보":
        lines.extend(
            [
                "- For info answers, the first sentence must directly answer the user's question.",
                "- Keep the answer focused on the asked point instead of widening into a generic wellness lecture.",
            ]
        )

    if intent in {"계획", "수정"}:
        lines.extend(
            [
                "- For plan or modify answers, preserve the plan direction and change axes already present in the draft.",
                "- If the draft refers to frequency, intensity, sets, rest, calories, ingredient changes, or meal composition, do not blur those specifics.",
                "- If plan_preview exists, keep the visible plan structure and major item details in the final response.",
                "- Do not repeat the same plan summary, confirmation sentence, or approval request in multiple phrasings.",
                "- Keep the closing line to a single short next-step or confirmation sentence.",
            ]
        )

    if intent == "怨꾪쉷_?뱀씤":
        lines.extend(
            [
                "- Keep approval answers short and final.",
                "- Do not restate the full plan summary again once the user has already approved it.",
            ]
        )

    if draft_components.get("core_message"):
        lines.append(
            f"- The final response must stay semantically aligned with this core message: {draft_components['core_message']}"
        )

    if _is_plan_flow_intent(str(intent or "")):
        lines.extend(
            [
                "- Never repeat the same confirmation or plan summary in slightly different wording.",
                "- Keep plan-flow answers compact; avoid filler before or after the main point.",
            ]
        )

    if intent == "계획_승인":
        lines.extend(
            [
                "- Approval replies should be one short confirmation, not a fresh explanation.",
                "- Do not re-list the plan contents after approval unless the draft explicitly requires it.",
            ]
        )

    return "\n".join(lines)


def make_persona_node(deps: NodeDeps):
    async def persona_node(state: GraphState) -> dict:
        if state.get("response"):
            return {}

        started_at = time.perf_counter()
        draft_components = normalize_draft_components(
            state.get("draft_components"),
            fallback_text=state.get("draft_response"),
        )
        draft_response = render_draft_preview(draft_components)

        profile = state.get("user_profile") or {}
        mbti = profile.get("mbti", "unknown")
        selected_persona = _selected_persona_id(profile)
        resolved_persona_id, persona_path = resolve_persona(selected_persona)
        intimacy_level = state.get("intimacy_level", 1)

        emotion = state.get("emotion") or {}
        emotion_label = emotion.get("label", "neutral")
        emotion_intensity = float(emotion.get("intensity", 0))
        emotion_str = f"{emotion_label} (intensity {emotion_intensity:.1f})"
        deps.trace.record_current_event(
            stage="persona",
            status="info",
            title="Persona polishing started",
            detail={
                "selected_persona_id": selected_persona,
                "resolved_persona_id": resolved_persona_id,
                "emotion": emotion_label,
            },
        )

        try:
            template = persona_path.read_text(encoding="utf-8")
            persona_prompt = template.format(
                persona_id=resolved_persona_id,
                emotion=emotion_str,
                mbti=mbti,
                intimacy_level=intimacy_level,
            )
            system_prompt = persona_prompt + "\n\n" + _persona_guardrails(state, draft_components)
        except Exception as exc:
            logger.error("Failed to load persona prompt: %s", exc)
            deps.trace.record_current_alert(
                severity="warning",
                message="Persona prompt load failed; using fallback prompt",
                detail={"error": str(exc), "resolved_persona_id": resolved_persona_id},
            )
            system_prompt = (
                "Rewrite the structured draft naturally without changing facts.\n\n"
                + _persona_guardrails(state, draft_components)
            )

        structured_payload = {
            "core_message": draft_components["core_message"],
            "reason_points": draft_components["reason_points"],
            "suggested_action": draft_components["suggested_action"],
            "plan_preview": draft_components["plan_preview"],
            "safety_notes": draft_components["safety_notes"],
            "approval_question": draft_components["approval_question"],
            "search_grounding_summary": draft_components["search_grounding_summary"],
        }
        user_content = "[Structured Draft]\n" + json.dumps(
            structured_payload,
            ensure_ascii=False,
            indent=2,
        )

        try:
            raw = await deps.router.generate(
                system_prompt=system_prompt,
                user_content=user_content,
                response_schema=PersonaResponse,
            )
            result = PersonaResponse.model_validate_json(raw)
            final_response = result.response
        except Exception as exc:
            logger.error("Persona generation failed: %s", exc)
            deps.trace.record_current_alert(
                severity="warning",
                message="Persona generation failed; using draft preview",
                detail={"error": str(exc), "resolved_persona_id": resolved_persona_id},
            )
            final_response = draft_response

        if state.get("intent") in {"怨꾪쉷", "?섏젙", "怨꾪쉷_?뱀씤"}:
            final_response = _dedupe_repeated_sentences(final_response)

        if _is_plan_flow_intent(str(state.get("intent") or "")):
            final_response = _dedupe_repeated_sentences(final_response)

        deps.trace.record_current_event(
            stage="persona",
            status="ok",
            title="Persona polishing completed",
            detail={"resolved_persona_id": resolved_persona_id},
            duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
        )

        return {
            "response": final_response,
            "resolved_persona_id": resolved_persona_id,
        }

    return persona_node
