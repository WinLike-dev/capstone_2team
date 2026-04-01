import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

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


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_process_meal_valid_request():
    """/process-meal 유효 요청 → 200 + success 응답."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/process-meal", json=VALID_MEAL_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "calories" in body["data"]
    assert "message" in body["data"]
    assert isinstance(body["data"]["calories"], (int, float))
    assert isinstance(body["data"]["message"], str)


@pytest.mark.anyio
async def test_process_meal_missing_field():
    """/process-meal user_id 누락 → 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/process-meal",
            json={
                "user_profile": {},
                "user_instruction": "test",
                "user_message": "test",
            },
        )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_recommend_valid_request():
    """/recommend 유효 요청 → 200 + success 응답."""
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
    assert "name" in exercise and "burn_calories" in exercise
    assert "name" in meal and "calories" in meal


@pytest.mark.anyio
async def test_recommend_missing_field():
    """/recommend user_id 누락 → 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/recommend",
            json={
                "user_profile": {},
                "user_instruction": "추천해줘",
            },
        )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_process_meal_empty_profile():
    """/process-meal user_profile 필드가 최소한만 있어도 성공 (Optional 필드 검증)."""
    payload = {
        "user_id": "u1",
        "user_profile": {},
        "user_instruction": "test",
        "user_message": "아무거나",
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/process-meal", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
