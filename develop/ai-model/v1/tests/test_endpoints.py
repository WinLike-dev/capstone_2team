"""POST /process-meal, POST /recommend 통합 테스트.

서비스 레이어를 mock하여 라우터와 글로벌 예외 핸들러를 검증한다.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.common import SuccessResponse

VALID_MEAL_PAYLOAD = {
    "user_id": "user_123",
    "user_profile": {
        "gender": "female",
        "age": 28,
        "bmi": 21.5,
        "goal": "체중 감량",
        "medical_history": [],
        "allergies": ["우유"],
    },
    "user_instruction": "칼로리를 낮춰줘",
    "user_message": "점심에 비빔밥을 먹었어",
}

MOCK_SUCCESS_RESPONSE = SuccessResponse(data={"calories": 350.0, "message": "균형 잡힌 식사"})

VALID_RECOMMEND_PAYLOAD = {
    "user_id": "user_456",
    "user_profile": {
        "gender": "male",
        "age": 35,
        "bmi": 24.0,
        "goal": "근력 증가",
        "activity_level": "high",
    },
    "user_instruction": "운동과 식단 추천해줘",
}

MOCK_RECOMMEND_RESPONSE = SuccessResponse(
    data={
        "recommended_exercise": {"name": "조깅", "burn_calories": 300.0},
        "recommended_meal": {"name": "샐러드", "calories": 400.0},
    }
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_process_meal_calls_service():
    """POST /process-meal: 서비스 레이어를 mock, 200 + success 응답을 확인한다."""
    with patch(
        "app.routers.meal.handle_process_meal",
        new_callable=AsyncMock,
        return_value=MOCK_SUCCESS_RESPONSE,
    ) as mock_service:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/process-meal", json=VALID_MEAL_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "calories" in body["data"]
    assert "message" in body["data"]
    mock_service.assert_called_once()


@pytest.mark.anyio
async def test_process_meal_422_invalid_body():
    """POST /process-meal: 필수 필드 누락 시 422 반환 (글로벌 핸들러 미간섭)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/process-meal",
            json={
                # user_id 누락
                "user_profile": {},
                "user_instruction": "test",
                "user_message": "test",
            },
        )

    assert response.status_code == 422
    # 글로벌 핸들러의 INTERNAL_ERROR가 아닌 FastAPI 기본 422 응답
    body = response.json()
    assert "detail" in body


@pytest.mark.anyio
async def test_global_handler_500():
    """서비스에서 예상치 못한 Exception raise 시 500 + INTERNAL_ERROR를 반환한다."""
    with patch(
        "app.routers.meal.handle_process_meal",
        new_callable=AsyncMock,
        side_effect=Exception("예기치 않은 오류"),
    ):
        # raise_server_exceptions=False: ASGI transport가 서버 예외를 테스트로 전파하지 않고
        # FastAPI의 exception_handler가 반환한 JSONResponse를 그대로 받는다.
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/process-meal", json=VALID_MEAL_PAYLOAD)

    assert response.status_code == 500
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert "내부 서버 오류" in body["error"]["message"]


# ---------------------------------------------------------------------------
# /recommend 통합 테스트
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_recommend_calls_service():
    """POST /recommend: 서비스 레이어를 mock, 200 + success 응답을 확인한다."""
    with patch(
        "app.routers.recommend.handle_recommend",
        new_callable=AsyncMock,
        return_value=MOCK_RECOMMEND_RESPONSE,
    ) as mock_service:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/recommend", json=VALID_RECOMMEND_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "recommended_exercise" in body["data"]
    assert "recommended_meal" in body["data"]
    exercise = body["data"]["recommended_exercise"]
    meal = body["data"]["recommended_meal"]
    assert exercise["name"] == "조깅"
    assert exercise["burn_calories"] == 300.0
    assert meal["name"] == "샐러드"
    assert meal["calories"] == 400.0
    mock_service.assert_called_once()


@pytest.mark.anyio
async def test_recommend_422_invalid_body():
    """POST /recommend: user_id 누락 시 422 반환."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/recommend",
            json={
                # user_id 누락
                "user_profile": {},
                "user_instruction": "추천해줘",
            },
        )

    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
