"""WAS HTTP 클라이언트 — Layer 4 API 엔드포인트 구현.

읽기 API (동기 호출):
  GET /api/user/profile
  GET /api/plan/today
  GET /api/workout-plan/full
  GET /api/diet-plan/full

쓰기 API (비동기 호출):
  PUT  /api/user/profile
  POST /api/plan/create
  PUT  /api/plan/update
  PUT  /api/plan/check
"""
from __future__ import annotations

from typing import Any

import httpx

from app.core.exceptions import ExternalServiceError


class WASClient:
    def __init__(self, base_url: str, client: httpx.AsyncClient) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client

    # ── 읽기 API ─────────────────────────────────────────────────────────────

    async def get_user_profile(self, user_id: str) -> dict[str, Any]:
        return await self._get(f"/api/user/profile/{user_id}")

    async def get_today_plan(self, user_id: str) -> list[dict[str, Any]]:
        return await self._get(f"/api/plan/today/{user_id}")

    async def get_workout_plan_full(self, user_id: str) -> dict[str, Any]:
        return await self._get(f"/api/workout-plan/full/{user_id}")

    async def get_diet_plan_full(self, user_id: str) -> dict[str, Any]:
        return await self._get(f"/api/diet-plan/full/{user_id}")

    # ── 쓰기 API ─────────────────────────────────────────────────────────────

    async def put_user_profile(self, user_id: str, changes: dict[str, Any]) -> None:
        await self._put(f"/api/user/profile/{user_id}", changes)

    async def post_plan_create(self, user_id: str, plan: dict[str, Any]) -> None:
        await self._post(f"/api/plan/create/{user_id}", plan)

    async def put_plan_update(self, user_id: str, plan: dict[str, Any]) -> None:
        await self._put(f"/api/plan/update/{user_id}", plan)

    async def put_plan_check(self, user_id: str, item_id: str) -> None:
        await self._put(f"/api/plan/check/{user_id}", {"item_id": item_id})

    # ── 내부 헬퍼 ─────────────────────────────────────────────────────────────

    async def _get(self, path: str) -> Any:
        try:
            resp = await self._client.get(f"{self._base_url}{path}")
            resp.raise_for_status()
        except httpx.TimeoutException:
            raise ExternalServiceError(service="WAS", message="request timeout")
        except httpx.HTTPStatusError as exc:
            raise ExternalServiceError(service="WAS", message=f"HTTP {exc.response.status_code}")
        return resp.json().get("data", resp.json())

    async def _post(self, path: str, body: dict) -> None:
        try:
            resp = await self._client.post(f"{self._base_url}{path}", json=body)
            resp.raise_for_status()
        except httpx.TimeoutException:
            raise ExternalServiceError(service="WAS", message="request timeout")
        except httpx.HTTPStatusError as exc:
            raise ExternalServiceError(service="WAS", message=f"HTTP {exc.response.status_code}")

    async def _put(self, path: str, body: dict) -> None:
        try:
            resp = await self._client.put(f"{self._base_url}{path}", json=body)
            resp.raise_for_status()
        except httpx.TimeoutException:
            raise ExternalServiceError(service="WAS", message="request timeout")
        except httpx.HTTPStatusError as exc:
            raise ExternalServiceError(service="WAS", message=f"HTTP {exc.response.status_code}")
