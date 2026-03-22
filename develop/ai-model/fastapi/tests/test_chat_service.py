"""chat_service.handle_ai_chat 파이프라인 유닛 테스트 (TDD).

검증 항목:
  1. Router AI classify와 Vector DB context search가 asyncio.gather로 병렬 실행됨
  2. mode 1 요청 시 db_modified_flag="none"인 AiChatResponse 반환
  3. mode 2 요청 시 db_modified_flag="exercise"인 AiChatResponse 반환
  4. mode 6 요청 시 db_modified_flag="profile"인 AiChatResponse 반환
  5. user_instruction이 비어있으면 프롬프트에 사용자 지시사항 섹션 미포함
  6. BackgroundTasks.add_task가 run_background_summary로 호출됨
  7. Router AI 실패 시 mode=1 fallback으로 정상 응답
  8. _get_worker_response_schema()가 8개 모드 각각에 올바른 스키마 반환
  9. _build_ai_chat_data()가 모드별로 AiChatData를 올바르게 구성
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest
from fastapi import BackgroundTasks

from app.schemas.chat import AiChatData, AiChatRequest, AiChatResponse
from app.schemas.common import UserProfile


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def anyio_backend():
    return "asyncio"


SIMPLE_ANSWER_JSON = json.dumps({"answer": "안녕하세요! 무엇을 도와드릴까요?"})
EXERCISE_PLAN_JSON = json.dumps(
    {"items": [{"date": "2026-03-22", "type": "유산소", "detail": "러닝", "count": "30분"}]}
)
MEAL_PLAN_JSON = json.dumps(
    {"items": [{"date": "2026-03-22", "food": "닭가슴살 샐러드", "time": "12:00"}]}
)
USER_DB_UPDATE_JSON = json.dumps({"updated_fields": {"age": 30}})
MEAL_LOG_JSON = json.dumps(
    {"calories": 500, "carbs": 60, "protein": 35, "fat": 15, "message": "균형 잡힌 식사입니다."}
)
RECOMMENDATION_JSON = json.dumps(
    {
        "recommended_exercises": [{"name": "러닝", "calories": 300}],
        "recommended_meals": [{"name": "닭가슴살 샐러드", "calories": 250}],
    }
)

EMBED_VECTOR = [0.1] * 384
PINECONE_RESULTS = [
    {"id": "1", "score": 0.9, "summary": "어제 운동을 했음", "timestamp": "2026-01-01"},
]


def _make_body(**kwargs):
    """기본값으로 AiChatRequest를 생성한다."""
    defaults = dict(
        user_id="user_test",
        user_profile=UserProfile(gender="male", age=28, bmi=23.5, goal="체중 감량"),
        user_instruction="",
        user_message="안녕하세요",
    )
    defaults.update(kwargs)
    return AiChatRequest(**defaults)


def _make_request(router_mock, gemini_mock, pinecone_mock, embed_mock, was_mock=None):
    """app.state에 mock 클라이언트를 가진 FastAPI Request mock을 반환한다."""
    if was_mock is None:
        was_mock = AsyncMock()
    request = MagicMock()
    request.app.state.router_client = router_mock
    request.app.state.gemini_client = gemini_mock
    request.app.state.pinecone_client = pinecone_mock
    request.app.state.embed_client = embed_mock
    request.app.state.was_client = was_mock
    return request


@pytest.fixture
def router_mock():
    """기본 mode=1 응답을 반환하는 RouterClient mock."""
    from app.clients.router import RouterOutput
    m = AsyncMock()
    m.classify = AsyncMock(return_value=RouterOutput(mode=1, reason="단순대화"))
    return m


@pytest.fixture
def gemini_mock():
    m = AsyncMock()
    m.generate = AsyncMock(return_value=SIMPLE_ANSWER_JSON)
    return m


@pytest.fixture
def embed_mock():
    m = AsyncMock()
    m.embed = AsyncMock(return_value=EMBED_VECTOR)
    return m


@pytest.fixture
def pinecone_mock():
    m = AsyncMock()
    m.search = AsyncMock(return_value=PINECONE_RESULTS)
    return m


@pytest.fixture
def background_tasks():
    return MagicMock(spec=BackgroundTasks)


# ---------------------------------------------------------------------------
# Test 1: asyncio.gather로 병렬 실행 검증
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_parallel_router_and_context_fetch(
    router_mock, gemini_mock, embed_mock, pinecone_mock, background_tasks
):
    """Router AI classify와 Vector DB context search가 asyncio.gather로 병렬 실행된다."""
    from app.services.chat_service import handle_ai_chat

    body = _make_body()
    request = _make_request(router_mock, gemini_mock, pinecone_mock, embed_mock)

    gather_called_with_coroutines = []

    original_gather = asyncio.gather

    async def mock_gather(*coros, **kwargs):
        gather_called_with_coroutines.extend(coros)
        return await original_gather(*coros, **kwargs)

    with patch("app.services.chat_service.asyncio.gather", side_effect=mock_gather):
        await handle_ai_chat(body, request, background_tasks)

    assert len(gather_called_with_coroutines) == 2, (
        f"asyncio.gather는 정확히 2개의 코루틴으로 호출되어야 한다. 실제: {len(gather_called_with_coroutines)}"
    )
    # router classify가 호출되었는지 확인
    router_mock.classify.assert_called_once_with(body.user_message)
    # embed가 호출되었는지 확인 (context fetch 일부)
    embed_mock.embed.assert_called_once()


# ---------------------------------------------------------------------------
# Test 2: mode 1 → db_modified_flag="none"
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_mode1_db_flag_none(
    router_mock, gemini_mock, embed_mock, pinecone_mock, background_tasks
):
    """mode 1 요청 시 db_modified_flag='none'인 AiChatResponse를 반환한다."""
    from app.clients.router import RouterOutput
    from app.services.chat_service import handle_ai_chat

    router_mock.classify = AsyncMock(return_value=RouterOutput(mode=1, reason="단순대화"))
    gemini_mock.generate = AsyncMock(return_value=SIMPLE_ANSWER_JSON)
    body = _make_body(user_message="오늘 날씨 어때?")
    request = _make_request(router_mock, gemini_mock, pinecone_mock, embed_mock)

    result = await handle_ai_chat(body, request, background_tasks)

    assert isinstance(result, AiChatResponse)
    assert result.mode == 1
    assert result.db_modified_flag == "none"
    assert result.status == "success"
    assert result.data.message == "안녕하세요! 무엇을 도와드릴까요?"


# ---------------------------------------------------------------------------
# Test 3: mode 2 → db_modified_flag="exercise"
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_mode2_db_flag_exercise(
    embed_mock, pinecone_mock, background_tasks
):
    """mode 2 요청 시 db_modified_flag='exercise'이고 detail에 운동 계획이 담긴다."""
    from app.clients.router import RouterOutput
    from app.services.chat_service import handle_ai_chat

    router_mock2 = AsyncMock()
    router_mock2.classify = AsyncMock(return_value=RouterOutput(mode=2, reason="플랜 작성"))
    gemini_mock2 = AsyncMock()
    gemini_mock2.generate = AsyncMock(return_value=EXERCISE_PLAN_JSON)
    body = _make_body(user_message="운동 계획 만들어줘")
    request = _make_request(router_mock2, gemini_mock2, pinecone_mock, embed_mock)

    result = await handle_ai_chat(body, request, background_tasks)

    assert result.mode == 2
    assert result.db_modified_flag == "exercise"
    assert result.data.detail is not None


# ---------------------------------------------------------------------------
# Test 4: mode 6 → db_modified_flag="profile"
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_mode6_db_flag_profile(
    embed_mock, pinecone_mock, background_tasks
):
    """mode 6 요청 시 db_modified_flag='profile'이고 detail에 updated_fields가 담긴다."""
    from app.clients.router import RouterOutput
    from app.services.chat_service import handle_ai_chat

    router_mock6 = AsyncMock()
    router_mock6.classify = AsyncMock(return_value=RouterOutput(mode=6, reason="DB 수정"))
    gemini_mock6 = AsyncMock()
    gemini_mock6.generate = AsyncMock(return_value=USER_DB_UPDATE_JSON)
    body = _make_body(user_message="나이 30으로 업데이트해줘")
    request = _make_request(router_mock6, gemini_mock6, pinecone_mock, embed_mock)

    result = await handle_ai_chat(body, request, background_tasks)

    assert result.mode == 6
    assert result.db_modified_flag == "profile"
    assert result.data.detail is not None


# ---------------------------------------------------------------------------
# Test 5: user_instruction 비어있으면 프롬프트에 사용자 지시사항 섹션 미포함
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_no_user_instruction_omits_section(
    router_mock, gemini_mock, embed_mock, pinecone_mock, background_tasks
):
    """user_instruction이 빈 문자열이면 시스템 프롬프트에 '사용자 지시사항' 섹션이 없다."""
    from app.services.chat_service import handle_ai_chat
    import app.prompts.worker as worker_module

    body = _make_body(user_instruction="", user_message="운동 팁 알려줘")
    request = _make_request(router_mock, gemini_mock, pinecone_mock, embed_mock)

    captured: dict = {}
    original_build = worker_module.build_worker_system_prompt

    def capture_build(mode, user_profile, context_text, user_instruction=""):
        result = original_build(mode, user_profile, context_text, user_instruction)
        captured["prompt"] = result
        return result

    with patch("app.services.chat_service.build_worker_system_prompt", side_effect=capture_build):
        await handle_ai_chat(body, request, background_tasks)

    # 사용자 지시사항 섹션 헤더("사용자 지시사항: " — 콜론+공백)가 없어야 한다
    # (공통 규칙 본문에도 '사용자 지시사항'이라는 단어가 등장하므로 섹션 헤더 패턴으로 확인)
    assert "사용자 지시사항: " not in captured.get("prompt", ""), (
        "user_instruction이 비어있으면 '사용자 지시사항: ...' 섹션 헤더가 포함되지 않아야 한다"
    )


# ---------------------------------------------------------------------------
# Test 6: BackgroundTasks.add_task가 run_background_summary로 호출됨
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_background_task_registered(
    router_mock, gemini_mock, embed_mock, pinecone_mock, background_tasks
):
    """background_tasks.add_task(run_background_summary, ...) 호출이 확인된다."""
    from app.services.chat_service import handle_ai_chat
    from app.services.background_summary import run_background_summary

    body = _make_body(user_id="bg_user", user_message="건강 팁 알려줘")
    request = _make_request(router_mock, gemini_mock, pinecone_mock, embed_mock)

    await handle_ai_chat(body, request, background_tasks)

    background_tasks.add_task.assert_called_once()
    call_args = background_tasks.add_task.call_args
    assert call_args.args[0] is run_background_summary


# ---------------------------------------------------------------------------
# Test 7: Router AI 실패 시 mode=1 fallback
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_router_failure_fallback_mode1(
    gemini_mock, embed_mock, pinecone_mock, background_tasks
):
    """Router AI classify 실패 시 mode=1 fallback으로 정상 AiChatResponse를 반환한다."""
    from app.services.chat_service import handle_ai_chat

    router_fail = AsyncMock()
    router_fail.classify = AsyncMock(side_effect=Exception("Router AI 연결 실패"))
    body = _make_body(user_message="도와줘")
    request = _make_request(router_fail, gemini_mock, pinecone_mock, embed_mock)

    result = await handle_ai_chat(body, request, background_tasks)

    assert isinstance(result, AiChatResponse)
    assert result.mode == 1
    assert result.db_modified_flag == "none"
    assert result.status == "success"


# ---------------------------------------------------------------------------
# Test 8: _get_worker_response_schema() 모드별 스키마 반환 검증
# ---------------------------------------------------------------------------


def test_get_worker_response_schema_all_modes():
    """_get_worker_response_schema()가 8개 모드 각각에 올바른 스키마 클래스를 반환한다."""
    from app.services.chat_service import _get_worker_response_schema
    from app.schemas.gemini_outputs import (
        SimpleAnswerOutput,
        ExercisePlanOutput,
        MealPlanOutput,
        UserDbUpdateOutput,
        MealLogOutput,
        RecommendationOutput,
    )

    assert _get_worker_response_schema(1) is SimpleAnswerOutput
    assert _get_worker_response_schema(2) is ExercisePlanOutput
    assert _get_worker_response_schema(3) is ExercisePlanOutput
    assert _get_worker_response_schema(4) is MealPlanOutput
    assert _get_worker_response_schema(5) is MealPlanOutput
    assert _get_worker_response_schema(6) is UserDbUpdateOutput
    assert _get_worker_response_schema(7) is MealLogOutput
    assert _get_worker_response_schema(8) is RecommendationOutput


def test_get_worker_response_schema_unknown_mode_fallback():
    """알 수 없는 모드는 SimpleAnswerOutput으로 fallback한다."""
    from app.services.chat_service import _get_worker_response_schema
    from app.schemas.gemini_outputs import SimpleAnswerOutput

    assert _get_worker_response_schema(99) is SimpleAnswerOutput


# ---------------------------------------------------------------------------
# Test 9: _build_ai_chat_data() 모드별 AiChatData 구성 검증
# ---------------------------------------------------------------------------


def test_build_ai_chat_data_mode1():
    """모드 1: message에 answer 값, detail은 None."""
    from app.services.chat_service import _build_ai_chat_data

    parsed = {"answer": "안녕하세요!"}
    result = _build_ai_chat_data(1, parsed)

    assert isinstance(result, AiChatData)
    assert result.message == "안녕하세요!"
    assert result.detail is None


def test_build_ai_chat_data_mode2():
    """모드 2: detail에 운동 계획 items 배열이 담긴다."""
    from app.services.chat_service import _build_ai_chat_data

    items = [{"date": "2026-03-22", "type": "유산소", "detail": "러닝", "count": "30분"}]
    parsed = {"items": items}
    result = _build_ai_chat_data(2, parsed)

    assert isinstance(result, AiChatData)
    assert result.detail == items


def test_build_ai_chat_data_mode6():
    """모드 6: detail에 updated_fields 딕셔너리가 담긴다."""
    from app.services.chat_service import _build_ai_chat_data

    parsed = {"updated_fields": {"age": 30}}
    result = _build_ai_chat_data(6, parsed)

    assert isinstance(result, AiChatData)
    assert result.message == "프로필이 업데이트되었습니다."
    assert result.detail == {"age": 30}


def test_build_ai_chat_data_mode7():
    """모드 7: message에 분석 메시지, detail에 영양소 데이터가 담긴다."""
    from app.services.chat_service import _build_ai_chat_data

    parsed = {"calories": 500, "carbs": 60, "protein": 35, "fat": 15, "message": "균형 잡힌 식사"}
    result = _build_ai_chat_data(7, parsed)

    assert isinstance(result, AiChatData)
    assert result.message == "균형 잡힌 식사"
    assert result.detail["calories"] == 500
    assert result.detail["protein"] == 35


def test_build_ai_chat_data_mode8():
    """모드 8: detail에 추천 운동과 식단 배열이 담긴다."""
    from app.services.chat_service import _build_ai_chat_data

    parsed = {
        "recommended_exercises": [{"name": "러닝", "calories": 300}],
        "recommended_meals": [{"name": "닭가슴살 샐러드", "calories": 250}],
    }
    result = _build_ai_chat_data(8, parsed)

    assert isinstance(result, AiChatData)
    assert result.message == "추천 운동과 식단입니다."
    assert result.detail == parsed
