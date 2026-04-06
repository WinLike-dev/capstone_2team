"""Helpers for resolving AI personas from a shared registry."""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

PERSONAS_DIR = Path(__file__).resolve().parent.parent / "prompts" / "personas"
REGISTRY_PATH = PERSONAS_DIR / "registry.json"

_FALLBACK_REGISTRY = {
    "default_persona": "default",
    "personas": {
        "default": {
            "label": "Default Coach",
            "prompt_file": "default.md",
            "active": True,
            "fallback": "default",
        }
    },
}


def _normalize_persona_id(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


@lru_cache(maxsize=1)
def load_persona_registry() -> dict:
    """Load the persona registry once per process."""
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("registry.json must contain a JSON object")
        return data
    except Exception as exc:
        logger.error("Failed to load persona registry: %s", exc)
        return _FALLBACK_REGISTRY


def _personas_map(registry: dict) -> dict[str, dict]:
    personas = registry.get("personas")
    if isinstance(personas, dict):
        return {str(key): value for key, value in personas.items() if isinstance(value, dict)}
    return {}


def _default_persona_id(registry: dict) -> str:
    default_id = _normalize_persona_id(registry.get("default_persona"))
    if default_id:
        return default_id
    personas = _personas_map(registry)
    if "default" in personas:
        return "default"
    for persona_id in personas:
        return persona_id
    return "default"


def _is_active(entry: dict | None) -> bool:
    return isinstance(entry, dict) and bool(entry.get("active", True))


def _fallback_persona_id(personas: dict[str, dict], entry: dict | None, default_id: str) -> str:
    fallback_id = _normalize_persona_id((entry or {}).get("fallback"))
    if fallback_id and _is_active(personas.get(fallback_id)):
        return fallback_id
    if _is_active(personas.get(default_id)):
        return default_id
    for persona_id, candidate in personas.items():
        if _is_active(candidate):
            return persona_id
    return "default"


def resolve_persona(persona_id: object) -> tuple[str, Path]:
    """Resolve a user-selected persona to a valid prompt file."""
    registry = load_persona_registry()
    personas = _personas_map(registry)
    default_id = _default_persona_id(registry)

    requested_id = _normalize_persona_id(persona_id)
    requested_entry = personas.get(requested_id) if requested_id else None

    if requested_id and _is_active(requested_entry):
        resolved_id = requested_id
        resolved_entry = requested_entry
    else:
        resolved_id = _fallback_persona_id(personas, requested_entry, default_id)
        resolved_entry = personas.get(resolved_id)

    prompt_name = _normalize_persona_id((resolved_entry or {}).get("prompt_file")) or f"{resolved_id}.md"
    prompt_path = PERSONAS_DIR / prompt_name
    if prompt_path.exists():
        return resolved_id, prompt_path

    logger.warning("Persona prompt file missing for '%s': %s", resolved_id, prompt_path)
    fallback_id = _fallback_persona_id(personas, resolved_entry, default_id)
    fallback_entry = personas.get(fallback_id)
    fallback_name = _normalize_persona_id((fallback_entry or {}).get("prompt_file")) or "default.md"
    fallback_path = PERSONAS_DIR / fallback_name
    if fallback_path.exists():
        return fallback_id, fallback_path

    return "default", PERSONAS_DIR / "default.md"


def list_active_personas() -> list[dict[str, str | bool]]:
    """Return active personas for UI/debug surfaces."""
    registry = load_persona_registry()
    personas = _personas_map(registry)
    default_id = _default_persona_id(registry)

    entries: list[dict[str, str | bool]] = []
    for persona_id, entry in personas.items():
        if not _is_active(entry):
            continue
        entries.append(
            {
                "id": persona_id,
                "label": str(entry.get("label", persona_id)),
                "prompt_file": str(entry.get("prompt_file", f"{persona_id}.md")),
                "is_default": persona_id == default_id,
            }
        )

    entries.sort(key=lambda item: (not bool(item["is_default"]), str(item["label"]).lower()))
    return entries
