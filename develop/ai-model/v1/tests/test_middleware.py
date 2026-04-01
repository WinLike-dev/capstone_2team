"""Tests for RequestLoggingMiddleware - request_id and timing (TDD - RED phase)."""
import re

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

UUID4_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_response_has_x_request_id_header():
    """Every response includes X-Request-ID header with a valid UUID4 value."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    request_id = response.headers["x-request-id"]
    assert UUID4_PATTERN.match(request_id), f"Not a valid UUID4: {request_id}"


@pytest.mark.anyio
async def test_request_id_is_unique_per_request():
    """Each request gets a distinct request_id (no reuse)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.get("/health")
        r2 = await client.get("/health")
    assert r1.headers["x-request-id"] != r2.headers["x-request-id"]


@pytest.mark.anyio
async def test_request_state_has_request_id():
    """request.state.request_id is set and accessible inside route handlers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/request-id")
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert UUID4_PATTERN.match(data["request_id"]), f"Not a valid UUID4: {data['request_id']}"


@pytest.mark.anyio
async def test_request_state_id_matches_header():
    """The request_id in response body and X-Request-ID header are the same."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/request-id")
    data = response.json()
    header_id = response.headers["x-request-id"]
    body_id = data["request_id"]
    assert header_id == body_id, f"Header ID {header_id!r} != body ID {body_id!r}"


@pytest.mark.anyio
async def test_log_contains_structured_fields(caplog):
    """Log entry for a completed request includes request_id, method, path, status, duration_ms."""
    import logging

    transport = ASGITransport(app=app)
    with caplog.at_level(logging.INFO, logger="app.core.middleware"):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.get("/health")

    # Find the request completion log entry
    log_messages = [r.getMessage() for r in caplog.records if "request_id" in r.getMessage()]
    assert len(log_messages) >= 1, f"No structured log found. All records: {[r.getMessage() for r in caplog.records]}"

    log_line = log_messages[0]
    assert "request_id=" in log_line, f"Missing request_id= in: {log_line}"
    assert "method=" in log_line, f"Missing method= in: {log_line}"
    assert "path=" in log_line, f"Missing path= in: {log_line}"
    assert "status=" in log_line, f"Missing status= in: {log_line}"
    assert "duration_ms=" in log_line, f"Missing duration_ms= in: {log_line}"


@pytest.mark.anyio
async def test_error_response_also_gets_x_request_id():
    """Error responses (AppError, HTTPException) also include X-Request-ID header."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/not-found-error")
    assert response.status_code == 404
    assert "x-request-id" in response.headers
    assert UUID4_PATTERN.match(response.headers["x-request-id"])
