from __future__ import annotations

import logging

from fastapi import Header, HTTPException

from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def require_internal_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    expected_api_key = settings.INTERNAL_API_KEY

    if not expected_api_key:
        logger.warning("INTERNAL_API_KEY is not configured. Skipping FastAPI internal auth.")
        return

    if x_api_key != expected_api_key:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key")
