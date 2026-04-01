"""POST /ai-chat 라우터 통합 테스트 (TDD).

handle_ai_chat를 AsyncMock으로 패치하여 라우터 계층만 검증한다.
패치 대상: app.services.chat_service.handle_ai_chat

검증 항목:
  Test 1: 유효한 요청 바디 → 200 + AiChatResponse JSON
  Test 2: user_message 누락 → 422 구조화 에러
  Test 3: user_id 누락 → 422 구조화 에러
  Test 4: 응답 JSON에 mode, data.message, db_modified_flag 필드 포함
  Test 5: handle_ai_chat 내부 에러 → 500 structured error
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.chat import AiChatData, AiChatResponse

pytestmark = pytest.mark.anyio


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def anyio_backend():
    return "asyncio"


VALID_BODY = {
    "user_id": "test-user-1",
    "user_profile": {"gender": "male", "age": 25},
    "user_instruction": "",
    "user_message": "안녕하세요",
}

MOCK_RESPONSE = AiChatResponse(
    mode=1,
    data=AiChatData(message="안녕하세요! 무엇을 도와드릴까요?"),
    db_modified_flag="none",
)


# ---------------------------------------------------------------------------
# Test 1: 유효한 요청 바디 → 200 + AiChatResponse JSON
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_ai_chat_valid_request_returns_200():
    """POST /ai-chat: 유효한 요청 바디로 200 + AiChatResponse를 반환한다."""
    with patch(
        "app.routers.chat.handle_ai_chat",
        new_callable=AsyncMock,
        return_value=MOCK_RESPONSE,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/ai-chat", json=VALID_BODY)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["mode"] == 1
    assert "data" in body
    assert "db_modified_flag" in body


# ---------------------------------------------------------------------------
# Test 2: user_message 누락 → 422
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_ai_chat_missing_user_message_returns_422():
    """POST /ai-chat: user_message 필드 누락 시 422 구조화 에러를 반환한다."""
    payload = {
        "user_id": "test-user-1",
        "user_profile": {"gender": "male", "age": 25},
        "user_instruction": "",
        # user_message 누락
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/ai-chat", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert "detail" in body


# ---------------------------------------------------------------------------
# Test 3: user_id 누락 → 422
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_ai_chat_missing_user_id_returns_422():
    """POST /ai-chat: user_id 필드 누락 시 422 구조화 에러를 반환한다."""
    payload = {
        # user_id 누락
        "user_profile": {"gender": "male", "age": 25},
        "user_instruction": "",
        "user_message": "안녕하세요",
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/ai-chat", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert "detail" in body


# ---------------------------------------------------------------------------
# Test 4: 응답 JSON에 mode, data.message, db_modified_flag 필드 포함
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_ai_chat_response_contains_required_fields():
    """POST /ai-chat: 응답 JSON에 mode, data.message, db_modified_flag 필드가 포함된다."""
    with patch(
        "app.routers.chat.handle_ai_chat",
        new_callable=AsyncMock,
        return_value=MOCK_RESPONSE,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/ai-chat", json=VALID_BODY)

    assert response.status_code == 200
    body = response.json()
    assert "mode" in body
    assert "data" in body
    assert "message" in body["data"]
    assert "db_modified_flag" in body
    assert body["data"]["message"] == "안녕하세요! 무엇을 도와드릴까요?"
    assert body["db_modified_flag"] == "none"


# ---------------------------------------------------------------------------
# Test 5: handle_ai_chat 내부 에러 → 500 structured error
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_ai_chat_service_error_returns_500():
    """POST /ai-chat: handle_ai_chat에서 예상치 못한 예외 발생 시 500 + INTERNAL_ERROR를 반환한다."""
    with patch(
        "app.routers.chat.handle_ai_chat",
        new_callable=AsyncMock,
        side_effect=Exception("Unexpected service failure"),
    ):
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/ai-chat", json=VALID_BODY)

    assert response.status_code == 500
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "INTERNAL_ERROR"
