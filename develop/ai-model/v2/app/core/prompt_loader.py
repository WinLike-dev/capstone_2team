"""Load text prompts from the app prompt directory."""
from __future__ import annotations

from pathlib import Path

PROMPTS_ROOT = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(relative_path: str) -> str:
    """Load a prompt file relative to app/prompts."""
    prompt_path = PROMPTS_ROOT / relative_path
    return prompt_path.read_text(encoding="utf-8").strip()


def compose_prompts(*relative_paths: str) -> str:
    """Join multiple prompt files with blank lines."""
    return "\n\n".join(load_prompt(path) for path in relative_paths if path).strip()
