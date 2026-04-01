"""meal_service.process_meal 파이프라인 유닛 테스트 (TDD)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import BackgroundTasks
from fastapi.testclient import TestClient
from google.genai import errors as genai_errors

from app.schemas.common import SuccessResponse
from app.schemas.meal import ProcessMealRequest, MealAnalysisData
from app.schemas.common import UserProfile


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def anyio_backend():
    return "asyncio"


def _make_request(gemini_mock, embed_mock, pinecone_mock):
    """app.state에 mock 클라이언트를 가진 FastAPI Request mock을 반환한다."""
    request = MagicMock()
    request.app.state.gemini_client = gemini_mock
    request.app.state.embed_client = embed_mock
    request.app.state.pinecone_client = pinecone_mock
    return request


def _make_body(**kwargs):
    defaults = dict(
        user_id="user_42",
        user_profile=UserProfile(gender="male", age=30, bmi=22.0, goal="체중 유지"),
        user_instruction="칼로리 알려줘",
        user_message="저녁에 삼겹살을 먹었어",
    )
    defaults.update(kwargs)
    return ProcessMealRequest(**defaults)


GEMINI_RESPONSE = json.dumps({"calories": 350.0, "message": "균형 잡힌 식사입니다."})
EMBED_VECTOR = [0.1] * 384
PINECONE_RESULTS = [
    {"id": "1", "score": 0.9, "summary": "어제 치킨을 먹었음", "timestamp": "2026-01-01"},
]


@pytest.fixture
def gemini_mock():
    m = AsyncMock()
    m.generate = AsyncMock(return_value=GEMINI_RESPONSE)
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
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_process_meal_passes_fields(gemini_mock, embed_mock, pinecone_mock, background_tasks):
    """body의 user_id, user_message가 올바르게 파이프라인에 사용된다."""
    from app.services.meal_service import process_meal

    body = _make_body(user_id="u_xyz", user_message="점심에 비빔밥")
    request = _make_request(gemini_mock, embed_mock, pinecone_mock)

    result = await process_meal(body, request, background_tasks)

    # user_message가 embed.embed()에 전달되었는지 확인
    embed_mock.embed.assert_called_once_with("점심에 비빔밥")
    # user_id가 pinecone.search()에 전달되었는지 확인
    pinecone_mock.search.assert_called_once_with("u_xyz", EMBED_VECTOR, top_k=3)


@pytest.mark.anyio
async def test_process_meal_pinecone_search(gemini_mock, embed_mock, pinecone_mock, background_tasks):
    """embed.embed(user_message) -> pinecone.search(user_id, vector, top_k=3) 순서로 호출된다."""
    from app.services.meal_service import process_meal

    body = _make_body()
    request = _make_request(gemini_mock, embed_mock, pinecone_mock)

    call_order = []
    original_embed = embed_mock.embed
    original_search = pinecone_mock.search

    async def embed_wrapper(text):
        call_order.append("embed")
        return await original_embed(text)

    async def search_wrapper(user_id, vector, top_k=3):
        call_order.append("search")
        return await original_search(user_id, vector, top_k=top_k)

    embed_mock.embed = embed_wrapper
    pinecone_mock.search = search_wrapper

    await process_meal(body, request, background_tasks)

    assert call_order[0] == "embed", "embed()이 search()보다 먼저 호출되어야 한다"
    assert call_order[1] == "search", "search()이 embed() 다음에 호출되어야 한다"


@pytest.mark.anyio
async def test_process_meal_pinecone_failure(gemini_mock, embed_mock, background_tasks):
    """pinecone.search가 Exception을 raise해도 process_meal은 정상 응답을 반환한다 (graceful degradation)."""
    from app.services.meal_service import process_meal

    pinecone_fail = AsyncMock()
    pinecone_fail.search = AsyncMock(side_effect=Exception("Pinecone 연결 실패"))

    body = _make_body()
    request = _make_request(gemini_mock, embed_mock, pinecone_fail)

    result = await process_meal(body, request, background_tasks)

    assert result.status == "success"
    assert "calories" in result.data
    assert "message" in result.data


@pytest.mark.anyio
async def test_process_meal_context_injection(gemini_mock, embed_mock, pinecone_mock, background_tasks):
    """검색 결과가 있으면 '이전 맥락:\\n1. ...' 형식으로 build_meal_system_prompt에 전달된다."""
    from app.services.meal_service import process_meal
    from app.prompts import meal as meal_prompts

    body = _make_body()
    request = _make_request(gemini_mock, embed_mock, pinecone_mock)

    captured_context = {}

    original_build = meal_prompts.build_meal_system_prompt

    def capture_build(user_profile, context_text="이전 맥락: 없음"):
        captured_context["context_text"] = context_text
        return original_build(user_profile, context_text)

    with patch("app.services.meal_service.build_meal_system_prompt", side_effect=capture_build):
        await process_meal(body, request, background_tasks)

    context_text = captured_context["context_text"]
    assert context_text.startswith("이전 맥락:"), f"Expected '이전 맥락:' prefix, got: {context_text!r}"
    assert "어제 치킨을 먹었음" in context_text


@pytest.mark.anyio
async def test_process_meal_no_context(gemini_mock, embed_mock, background_tasks):
    """Pinecone 검색 결과가 빈 리스트일 때 '이전 맥락: 없음'이 전달된다."""
    from app.services.meal_service import process_meal

    pinecone_empty = AsyncMock()
    pinecone_empty.search = AsyncMock(return_value=[])

    body = _make_body()
    request = _make_request(gemini_mock, embed_mock, pinecone_empty)

    captured_context = {}
    from app.prompts import meal as meal_prompts
    original_build = meal_prompts.build_meal_system_prompt

    def capture_build(user_profile, context_text="이전 맥락: 없음"):
        captured_context["context_text"] = context_text
        return original_build(user_profile, context_text)

    with patch("app.services.meal_service.build_meal_system_prompt", side_effect=capture_build):
        await process_meal(body, request, background_tasks)

    assert captured_context["context_text"] == "이전 맥락: 없음"


@pytest.mark.anyio
async def test_process_meal_gemini_call(gemini_mock, embed_mock, pinecone_mock, background_tasks):
    """gemini.generate(system_prompt, user_message, MealAnalysisData) 호출을 확인한다."""
    from app.services.meal_service import process_meal

    body = _make_body(user_message="저녁에 치킨")
    request = _make_request(gemini_mock, embed_mock, pinecone_mock)

    await process_meal(body, request, background_tasks)

    gemini_mock.generate.assert_called_once()
    call_args = gemini_mock.generate.call_args
    # system_prompt, user_message, MealAnalysisData
    assert call_args.kwargs.get("user_content") == "저녁에 치킨" or call_args.args[1] == "저녁에 치킨"
    # response_schema는 MealAnalysisData여야 한다
    schema_arg = call_args.kwargs.get("response_schema") or call_args.args[2]
    assert schema_arg is MealAnalysisData


@pytest.mark.anyio
async def test_process_meal_response_format(gemini_mock, embed_mock, pinecone_mock, background_tasks):
    """반환값이 SuccessResponse(data={calories: float, message: str}) 형식이다."""
    from app.services.meal_service import process_meal

    body = _make_body()
    request = _make_request(gemini_mock, embed_mock, pinecone_mock)

    result = await process_meal(body, request, background_tasks)

    assert isinstance(result, SuccessResponse)
    assert result.status == "success"
    assert isinstance(result.data, dict)
    assert isinstance(result.data["calories"], float)
    assert isinstance(result.data["message"], str)


@pytest.mark.anyio
async def test_process_meal_gemini_failure(embed_mock, pinecone_mock, background_tasks):
    """gemini.generate가 ClientError를 raise하면 HTTPException(500, GEMINI_ERROR)를 반환한다."""
    from fastapi import HTTPException
    from app.services.meal_service import process_meal

    # ClientError 생성 (code=400 — 재시도 불가 에러)
    gemini_fail = AsyncMock()
    client_error = genai_errors.ClientError(400, {"error": {"message": "Bad request"}})
    gemini_fail.generate = AsyncMock(side_effect=client_error)

    body = _make_body()
    request = _make_request(gemini_fail, embed_mock, pinecone_mock)

    with pytest.raises(HTTPException) as exc_info:
        await process_meal(body, request, background_tasks)

    assert exc_info.value.status_code == 500
    detail = exc_info.value.detail
    assert detail["error"]["code"] == "GEMINI_ERROR"


@pytest.mark.anyio
async def test_background_task_registered(gemini_mock, embed_mock, pinecone_mock, background_tasks):
    """background_tasks.add_task(run_background_summary, ...) 호출이 확인된다."""
    from app.services.meal_service import process_meal
    from app.services.background_summary import run_background_summary

    body = _make_body(user_id="bg_user", user_message="배가 고프다")
    request = _make_request(gemini_mock, embed_mock, pinecone_mock)

    await process_meal(body, request, background_tasks)

    background_tasks.add_task.assert_called_once()
    call_args = background_tasks.add_task.call_args
    # 첫 번째 인자는 run_background_summary 함수여야 한다
    assert call_args.args[0] is run_background_summary
