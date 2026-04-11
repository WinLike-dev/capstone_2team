"""Persona node for tone polishing and final response generation."""
from __future__ import annotations

import json
import logging
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
            system_prompt = template.format(
                persona_id=resolved_persona_id,
                emotion=emotion_str,
                mbti=mbti,
                intimacy_level=intimacy_level,
            )
        except Exception as exc:
            logger.error("Failed to load persona prompt: %s", exc)
            deps.trace.record_current_alert(
                severity="warning",
                message="Persona prompt load failed; using fallback prompt",
                detail={"error": str(exc), "resolved_persona_id": resolved_persona_id},
            )
            system_prompt = "Rewrite the structured draft naturally without changing facts."

        structured_payload = {
            "core_message": draft_components["core_message"],
            "reason_points": draft_components["reason_points"],
            "suggested_action": draft_components["suggested_action"],
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
            "messages": [
                {"role": "user", "content": state["user_message"]},
                {"role": "assistant", "content": final_response},
            ],
        }

    return persona_node
