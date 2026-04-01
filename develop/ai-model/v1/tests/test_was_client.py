"""Tests for WASClient — uses httpx MockTransport, no real HTTP calls."""

import httpx
import pytest

from app.clients.was import WASClient
from app.core.exceptions import ExternalServiceError

pytestmark = pytest.mark.anyio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_transport(status_code: int, body: dict | None = None):
    """Return a MockTransport that responds with a fixed status/body."""
    import json

    def handler(request: httpx.Request) -> httpx.Response:
        content = json.dumps(body or {}).encode()
        return httpx.Response(status_code=status_code, content=content)

    return httpx.MockTransport(handler)


def _make_client(transport) -> WASClient:
    http_client = httpx.AsyncClient(transport=transport)
    return WASClient(base_url="http://was-mock", client=http_client)


# ---------------------------------------------------------------------------
# fetch_exercise_list
# ---------------------------------------------------------------------------

async def test_fetch_exercise_list_returns_list_on_200():
    """200 OK with data list -> returns that list."""
    payload = {"status": "success", "data": [{"id": 1, "name": "pushup"}]}
    client = _make_client(_make_transport(200, payload))

    result = await client.fetch_exercise_list("user_abc")

    assert result == [{"id": 1, "name": "pushup"}]


async def test_fetch_exercise_list_empty_list():
    """200 OK with empty data list -> returns empty list."""
    payload = {"status": "success", "data": []}
    client = _make_client(_make_transport(200, payload))

    result = await client.fetch_exercise_list("user_abc")

    assert result == []


# ---------------------------------------------------------------------------
# fetch_meal_list
# ---------------------------------------------------------------------------

async def test_fetch_meal_list_returns_list_on_200():
    """200 OK with data list -> returns that list."""
    payload = {"status": "success", "data": [{"id": 10, "name": "salad"}]}
    client = _make_client(_make_transport(200, payload))

    result = await client.fetch_meal_list("user_xyz")

    assert result == [{"id": 10, "name": "salad"}]


# ---------------------------------------------------------------------------
# Error handling — HTTP status errors
# ---------------------------------------------------------------------------

async def test_http_500_raises_external_service_error():
    """WAS returns 500 -> ExternalServiceError raised with WAS and 500 in message."""
    client = _make_client(_make_transport(500, {"error": "internal error"}))

    with pytest.raises(ExternalServiceError) as exc_info:
        await client.fetch_exercise_list("user_abc")

    assert exc_info.value.error_code == "EXTERNAL_SERVICE_ERROR"
    assert "WAS" in exc_info.value.message
    assert "500" in exc_info.value.message


async def test_http_404_raises_external_service_error():
    """WAS returns 404 -> ExternalServiceError raised with WAS and 404 in message."""
    client = _make_client(_make_transport(404, {"error": "not found"}))

    with pytest.raises(ExternalServiceError) as exc_info:
        await client.fetch_exercise_list("user_abc")

    assert exc_info.value.error_code == "EXTERNAL_SERVICE_ERROR"
    assert "WAS" in exc_info.value.message
    assert "404" in exc_info.value.message


async def test_meal_list_http_500_raises_external_service_error():
    """fetch_meal_list: WAS returns 500 -> ExternalServiceError raised."""
    client = _make_client(_make_transport(500, {}))

    with pytest.raises(ExternalServiceError) as exc_info:
        await client.fetch_meal_list("user_xyz")

    assert exc_info.value.error_code == "EXTERNAL_SERVICE_ERROR"
    assert "WAS" in exc_info.value.message


# ---------------------------------------------------------------------------
# Error handling — timeout
# ---------------------------------------------------------------------------

async def test_timeout_raises_external_service_error():
    """Timeout -> ExternalServiceError with 'timeout' in message."""

    def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    transport = httpx.MockTransport(timeout_handler)
    client = _make_client(transport)

    with pytest.raises(ExternalServiceError) as exc_info:
        await client.fetch_exercise_list("user_abc")

    assert exc_info.value.error_code == "EXTERNAL_SERVICE_ERROR"
    assert "timeout" in exc_info.value.message.lower()
