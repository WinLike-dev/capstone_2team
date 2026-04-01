"""Tests for custom exception classes and structured error handlers (TDD - RED phase)."""
import pytest
from httpx import ASGITransport, AsyncClient
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_app_error_returns_structured_json():
    """AppError subclass raises -> correct status code + structured JSON."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/app-error")
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "BAD_REQUEST"
    assert "message" in data["error"]


@pytest.mark.anyio
async def test_not_found_error_returns_404():
    """NotFoundError -> 404 + NOT_FOUND code in structured JSON."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/not-found-error")
    assert response.status_code == 404
    data = response.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "NOT_FOUND"
    assert "message" in data["error"]


@pytest.mark.anyio
async def test_validation_error_returns_422():
    """ValidationError -> 422 + VALIDATION_ERROR code in structured JSON."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/validation-error")
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "message" in data["error"]


@pytest.mark.anyio
async def test_external_service_error_returns_502():
    """ExternalServiceError(service='WAS') -> 502 + EXTERNAL_SERVICE_ERROR with service prefix in message."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/external-service-error")
    assert response.status_code == 502
    data = response.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "EXTERNAL_SERVICE_ERROR"
    assert "WAS" in data["error"]["message"]


@pytest.mark.anyio
async def test_http_exception_returns_structured_json():
    """FastAPI HTTPException -> same structured JSON format (not FastAPI default)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/http-exception")
    assert response.status_code == 404
    data = response.json()
    assert data["status"] == "error"
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    # Must NOT be FastAPI's default {"detail": "..."} format
    assert "detail" not in data


def test_unhandled_exception_returns_500_internal_error():
    """Unhandled exception -> 500 + INTERNAL_ERROR without leaking stack trace.

    Uses TestClient with raise_server_exceptions=False so Starlette's
    ServerErrorMiddleware passes the exception to our custom global handler.
    """
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/test/unhandled-exception")
    assert response.status_code == 500
    data = response.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "INTERNAL_ERROR"
    # Must not contain stack trace / internal details
    response_text = str(data)
    assert "Traceback" not in response_text
    assert "traceback" not in response_text


def test_error_response_structure_is_consistent():
    """All error responses follow the same JSON structure: status, error.code, error.message.

    Uses TestClient with raise_server_exceptions=False to test unhandled exceptions too.
    """
    client = TestClient(app, raise_server_exceptions=False)
    test_routes = [
        ("/test/app-error", 400),
        ("/test/not-found-error", 404),
        ("/test/validation-error", 422),
        ("/test/external-service-error", 502),
        ("/test/http-exception", 404),
        ("/test/unhandled-exception", 500),
    ]
    for path, expected_status in test_routes:
        response = client.get(path)
        assert response.status_code == expected_status, f"Path {path}: expected {expected_status}, got {response.status_code}"
        data = response.json()
        assert data["status"] == "error", f"Path {path}: missing status=error"
        assert "error" in data, f"Path {path}: missing error field"
        assert "code" in data["error"], f"Path {path}: missing error.code"
        assert "message" in data["error"], f"Path {path}: missing error.message"
