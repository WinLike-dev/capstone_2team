"""WAS HTTP client — wraps httpx.AsyncClient for exercise/meal list fetching.

Raises ExternalServiceError on HTTP 4xx/5xx or timeout.
"""

import httpx

from app.core.exceptions import ExternalServiceError


class WASClient:
    """Async HTTP client for the WAS (Web Application Server) backend."""

    def __init__(self, base_url: str, client: httpx.AsyncClient) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client

    async def fetch_exercise_list(self, user_id: str) -> list[dict]:
        """GET /api/exercise-list/{user_id} -> list of exercise dicts."""
        url = f"{self._base_url}/api/exercise-list/{user_id}"
        return await self._get_data(url)

    async def fetch_meal_list(self, user_id: str) -> list[dict]:
        """GET /api/meal-list/{user_id} -> list of meal dicts."""
        url = f"{self._base_url}/api/meal-list/{user_id}"
        return await self._get_data(url)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_data(self, url: str) -> list[dict]:
        """Perform GET request and return response.json()['data']."""
        try:
            response = await self._client.get(url)
            response.raise_for_status()
        except httpx.TimeoutException:
            raise ExternalServiceError(service="WAS", message="request timeout")
        except httpx.HTTPStatusError as exc:
            raise ExternalServiceError(
                service="WAS",
                message=f"HTTP {exc.response.status_code}",
            )
        return response.json()["data"]
