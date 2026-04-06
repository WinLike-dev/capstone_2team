"""Track profile update events so sessions can refresh on the next turn."""
from __future__ import annotations

import asyncio


class ProfileSyncTracker:
    """In-memory tracker for per-user profile update versions."""

    def __init__(self) -> None:
        self._versions: dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def mark_profile_updated(self, user_id: str, profile_version: int | None = None) -> int:
        async with self._lock:
            current = self._versions.get(user_id, 0)
            if profile_version is None:
                next_version = current + 1
            else:
                next_version = max(current, profile_version)
            self._versions[user_id] = next_version
            return next_version

    async def get_profile_version(self, user_id: str) -> int:
        async with self._lock:
            return self._versions.get(user_id, 0)
