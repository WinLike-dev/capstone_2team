"""
AI Core API 통합 테스트
- Gemini API는 Mock 처리하여 API 키 없이도 실행 가능
- AI 라우터(2단계 파이프라인) 기준으로 테스트
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

from main import app

# ─────────────────────────────────────────────────────────────────────────────
# 공통 픽스처
# ─────────────────────────────────────────────────────────────────────────────
BASE_REQUEST = {
    "user_id": "test-user-001",
    "user_context": {
        "age": 28,
        "gender": "male",
        "height": 175.0,
        "weight": 70.0,
        "mbti": "INFP",
    },
    "chat_history": [],
    "current_message": "오늘 운동 루틴 추천해줘",
}

MOCK_MAIN_RESPONSE = (
    "오늘은 맑은 날씨이니 가볍게 30분 조깅을 추천드려요. "
    "INFP 성향에 맞게 혼자 음악을 들으며 달리는 것이 좋을 것 같습니다!"
)


# ─────────────────────────────────────────────────────────────────────────────
# 헬스체크
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_health_check():
    """GET /health → 200 OK"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ai-core"


# ─────────────────────────────────────────────────────────────────────────────
# /api/v1/generate - _classify_intent, _generate_main_response 레벨 패치
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_generate_success_simple_question():
    """인텐트 1(단순 질문) → action_type: advice"""
    with (
        patch("chains.health_chain._classify_intent", new=AsyncMock(return_value=1)),
        patch("chains.health_chain._generate_main_response", new=AsyncMock(return_value=MOCK_MAIN_RESPONSE)),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/generate", json=BASE_REQUEST)

    assert response.status_code == 200
    data = response.json()
    assert data["action_type"] == "advice"
    assert MOCK_MAIN_RESPONSE in data["text_response"]
    assert "ui_components" in data


@pytest.mark.asyncio
async def test_generate_intent_plan_edit():
    """인텐트 2(계획 수정) → action_type: ui_update, widget: plan_editor"""
    request = {**BASE_REQUEST, "current_message": "운동 계획 좀 바꿔줘"}
    with (
        patch("chains.health_chain._classify_intent", new=AsyncMock(return_value=2)),
        patch("chains.health_chain._generate_main_response", new=AsyncMock(return_value="주 3회 근력 운동 루틴을 추천해 드릴게요.")),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/generate", json=request)

    assert response.status_code == 200
    data = response.json()
    assert data["action_type"] == "ui_update"
    assert data["ui_components"]["widget"] == "plan_editor"


@pytest.mark.asyncio
async def test_generate_intent_db_update():
    """인텐트 3(DB 수정) → action_type: ui_update, widget: profile_editor"""
    request = {**BASE_REQUEST, "current_message": "체중이 3kg 늘었어"}
    with (
        patch("chains.health_chain._classify_intent", new=AsyncMock(return_value=3)),
        patch("chains.health_chain._generate_main_response", new=AsyncMock(return_value="체중 변화를 기록해 드릴게요.")),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/generate", json=request)

    assert response.status_code == 200
    data = response.json()
    assert data["action_type"] == "ui_update"
    assert data["ui_components"]["widget"] == "profile_editor"


@pytest.mark.asyncio
async def test_generate_intent_diet():
    """인텐트 4(식단 구성) → action_type: ui_update, widget: diet_planner"""
    request = {**BASE_REQUEST, "current_message": "오늘 먹을 식단 짜줘"}
    with (
        patch("chains.health_chain._classify_intent", new=AsyncMock(return_value=4)),
        patch("chains.health_chain._generate_main_response", new=AsyncMock(return_value="오늘의 추천 식단입니다: 아침-오트밀, 점심-닭가슴살")),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/generate", json=request)

    assert response.status_code == 200
    data = response.json()
    assert data["action_type"] == "ui_update"
    assert data["ui_components"]["widget"] == "diet_planner"


@pytest.mark.asyncio
async def test_generate_with_chat_history():
    """대화 이력이 있는 경우도 정상 처리"""
    request = {
        **BASE_REQUEST,
        "chat_history": [
            {"role": "user", "content": "어제 운동했어"},
            {"role": "assistant", "content": "잘 하셨네요!"},
        ],
    }
    with (
        patch("chains.health_chain._classify_intent", new=AsyncMock(return_value=1)),
        patch("chains.health_chain._generate_main_response", new=AsyncMock(return_value=MOCK_MAIN_RESPONSE)),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/generate", json=request)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_generate_missing_required_field():
    """current_message 누락 → 422 Unprocessable Entity"""
    invalid_request = {k: v for k, v in BASE_REQUEST.items() if k != "current_message"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/generate", json=invalid_request)

    assert response.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# output_parser 단위 테스트
# ─────────────────────────────────────────────────────────────────────────────
def test_parse_intent_valid():
    from utils.output_parser import parse_intent
    assert parse_intent("1") == 1
    assert parse_intent("2") == 2
    assert parse_intent("3") == 3
    assert parse_intent("4") == 4


def test_parse_intent_fallback():
    from utils.output_parser import parse_intent
    assert parse_intent("알 수 없음") == 1
    assert parse_intent("") == 1


def test_wrap_plain_text_response_intent1():
    from utils.output_parser import wrap_plain_text_response
    result = wrap_plain_text_response("테스트 答변", 1)
    assert result["action_type"] == "advice"
    assert result["text_response"] == "테스트 答변"
    assert result["ui_components"]["widget"] is None


def test_wrap_plain_text_response_intent4():
    from utils.output_parser import wrap_plain_text_response
    result = wrap_plain_text_response("식단 추천 내용", 4)
    assert result["action_type"] == "ui_update"
    assert result["ui_components"]["widget"] == "diet_planner"
