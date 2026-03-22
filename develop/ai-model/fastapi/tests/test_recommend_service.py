"""Unit tests for recommend() service pipeline."""

import json
import pytest
from fastapi import BackgroundTasks, HTTPException
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.common import UserProfile
from app.schemas.recommend import RecommendRequest, RecommendationData


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

GEMINI_SUCCESS_RESPONSE = json.dumps(
    {
        "recommended_exercise": {"name": "조깅", "burn_calories": 300.0},
        "recommended_meal": {"name": "샐러드", "calories": 400.0},
    }
)


def _make_body() -> RecommendRequest:
    return RecommendRequest(
        user_id="user-1",
        user_profile=UserProfile(gender="남성", age=30, bmi=22.0, goal="체중 감량"),
        user_instruction="오늘 점심 뭐 먹으면 좋을까요?",
    )


def _make_request(gemini=None, embed=None, pinecone=None):
    """Fake FastAPI Request with app.state client instances."""
    gemini_client = gemini or AsyncMock()
    embed_client = embed or AsyncMock()
    pinecone_client = pinecone or AsyncMock()

    state = MagicMock()
    state.gemini_client = gemini_client
    state.embed_client = embed_client
    state.pinecone_client = pinecone_client

    request = MagicMock()
    request.app.state = state
    return request


# ---------------------------------------------------------------------------
# Test 1: body 필드(user_id, user_instruction)가 올바르게 사용됨
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_recommend_passes_fields() -> None:
    """recommend()가 body.user_id와 body.user_instruction을 파이프라인에 전달한다."""
    body = _make_body()

    gemini = AsyncMock()
    gemini.generate.return_value = GEMINI_SUCCESS_RESPONSE

    embed = AsyncMock()
    embed.embed.return_value = [0.1] * 384

    pinecone = AsyncMock()
    pinecone.search.return_value = []

    request = _make_request(gemini=gemini, embed=embed, pinecone=pinecone)
    background_tasks = BackgroundTasks()

    from app.services.recommend_service import recommend

    result = await recommend(body, request, background_tasks)

    # embed은 user_instruction을 받아야 함
    embed.embed.assert_called_once_with(body.user_instruction)
    # pinecone.search는 user_id로 검색해야 함
    pinecone.search.assert_called_once()
    call_kwargs = pinecone.search.call_args
    assert call_kwargs.kwargs.get("user_id") == body.user_id or call_args_has_user_id(
        call_kwargs, body.user_id
    )


def call_args_has_user_id(call_kwargs, user_id: str) -> bool:
    """positional or keyword user_id check."""
    args = call_kwargs.args if call_kwargs.args else ()
    return len(args) >= 1 and args[0] == user_id


# ---------------------------------------------------------------------------
# Test 2: embed -> pinecone.search 순서로 호출
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_recommend_pinecone_search() -> None:
    """embed.embed(user_instruction) -> pinecone.search(user_id, vector, top_k=3) 순서."""
    body = _make_body()

    gemini = AsyncMock()
    gemini.generate.return_value = GEMINI_SUCCESS_RESPONSE

    embed = AsyncMock()
    embed.embed.return_value = [0.5] * 384

    pinecone = AsyncMock()
    pinecone.search.return_value = []

    request = _make_request(gemini=gemini, embed=embed, pinecone=pinecone)
    background_tasks = BackgroundTasks()

    from app.services.recommend_service import recommend

    await recommend(body, request, background_tasks)

    embed.embed.assert_called_once_with(body.user_instruction)
    pinecone.search.assert_called_once_with(
        user_id=body.user_id, vector=[0.5] * 384, top_k=3
    )


# ---------------------------------------------------------------------------
# Test 3: Pinecone 실패 시 graceful degradation — 정상 응답 반환
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_recommend_pinecone_failure() -> None:
    """pinecone.search가 Exception을 raise해도 recommend()는 정상 응답을 반환한다."""
    body = _make_body()

    gemini = AsyncMock()
    gemini.generate.return_value = GEMINI_SUCCESS_RESPONSE

    embed = AsyncMock()
    embed.embed.return_value = [0.1] * 384

    pinecone = AsyncMock()
    pinecone.search.side_effect = Exception("Pinecone 연결 오류")

    request = _make_request(gemini=gemini, embed=embed, pinecone=pinecone)
    background_tasks = BackgroundTasks()

    from app.services.recommend_service import recommend

    result = await recommend(body, request, background_tasks)
    assert result.status == "success"


# ---------------------------------------------------------------------------
# Test 4: 검색 결과가 있으면 "이전 맥락:\n1. ..." 형식으로 프롬프트 주입
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_recommend_context_injection() -> None:
    """Pinecone 검색 결과가 있으면 '이전 맥락:\\n1. ...' 형식의 context_text를 생성한다."""
    body = _make_body()

    gemini = AsyncMock()
    gemini.generate.return_value = GEMINI_SUCCESS_RESPONSE

    embed = AsyncMock()
    embed.embed.return_value = [0.1] * 384

    pinecone = AsyncMock()
    pinecone.search.return_value = [
        {"summary": "이전에 조깅을 추천받았습니다."},
        {"summary": "저탄수화물 식단을 시작했습니다."},
    ]

    request = _make_request(gemini=gemini, embed=embed, pinecone=pinecone)
    background_tasks = BackgroundTasks()

    from app.services.recommend_service import recommend
    from app.prompts.recommend import build_recommend_system_prompt

    with patch(
        "app.services.recommend_service.build_recommend_system_prompt",
        wraps=build_recommend_system_prompt,
    ) as mock_build:
        await recommend(body, request, background_tasks)

        call_kwargs = mock_build.call_args
        context_text = call_kwargs.kwargs.get("context_text") or call_kwargs.args[1]
        assert "이전 맥락:" in context_text
        assert "1." in context_text
        assert "이전에 조깅을 추천받았습니다." in context_text


# ---------------------------------------------------------------------------
# Test 5: 검색 결과 빈 리스트일 때 "이전 맥락: 없음" 전달
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_recommend_no_context() -> None:
    """Pinecone 검색 결과가 빈 리스트일 때 '이전 맥락: 없음'을 프롬프트에 전달한다."""
    body = _make_body()

    gemini = AsyncMock()
    gemini.generate.return_value = GEMINI_SUCCESS_RESPONSE

    embed = AsyncMock()
    embed.embed.return_value = [0.1] * 384

    pinecone = AsyncMock()
    pinecone.search.return_value = []

    request = _make_request(gemini=gemini, embed=embed, pinecone=pinecone)
    background_tasks = BackgroundTasks()

    from app.services.recommend_service import recommend
    from app.prompts.recommend import build_recommend_system_prompt

    with patch(
        "app.services.recommend_service.build_recommend_system_prompt",
        wraps=build_recommend_system_prompt,
    ) as mock_build:
        await recommend(body, request, background_tasks)

        call_kwargs = mock_build.call_args
        context_text = call_kwargs.kwargs.get("context_text") or call_kwargs.args[1]
        assert context_text == "이전 맥락: 없음"


# ---------------------------------------------------------------------------
# Test 6: gemini.generate(system_prompt, user_instruction, RecommendationData) 호출
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_recommend_gemini_call() -> None:
    """gemini.generate가 system_prompt, user_instruction, RecommendationData로 호출된다."""
    body = _make_body()

    gemini = AsyncMock()
    gemini.generate.return_value = GEMINI_SUCCESS_RESPONSE

    embed = AsyncMock()
    embed.embed.return_value = [0.1] * 384

    pinecone = AsyncMock()
    pinecone.search.return_value = []

    request = _make_request(gemini=gemini, embed=embed, pinecone=pinecone)
    background_tasks = BackgroundTasks()

    from app.services.recommend_service import recommend

    await recommend(body, request, background_tasks)

    gemini.generate.assert_called_once()
    call_kwargs = gemini.generate.call_args.kwargs
    assert call_kwargs["user_content"] == body.user_instruction
    assert call_kwargs["response_schema"] is RecommendationData


# ---------------------------------------------------------------------------
# Test 7: 반환값이 SuccessResponse(data={...}) 형식
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_recommend_response_format() -> None:
    """반환값이 SuccessResponse(status='success', data=RecommendationData dict)이다."""
    body = _make_body()

    gemini = AsyncMock()
    gemini.generate.return_value = GEMINI_SUCCESS_RESPONSE

    embed = AsyncMock()
    embed.embed.return_value = [0.1] * 384

    pinecone = AsyncMock()
    pinecone.search.return_value = []

    request = _make_request(gemini=gemini, embed=embed, pinecone=pinecone)
    background_tasks = BackgroundTasks()

    from app.services.recommend_service import recommend

    result = await recommend(body, request, background_tasks)

    assert result.status == "success"
    data = result.data
    assert "recommended_exercise" in data
    assert data["recommended_exercise"]["name"] == "조깅"
    assert data["recommended_exercise"]["burn_calories"] == 300.0
    assert "recommended_meal" in data
    assert data["recommended_meal"]["name"] == "샐러드"
    assert data["recommended_meal"]["calories"] == 400.0


# ---------------------------------------------------------------------------
# Test 8: Gemini 실패 시 HTTPException(500, GEMINI_ERROR)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_recommend_gemini_failure() -> None:
    """gemini.generate가 ClientError를 raise하면 HTTPException(500, GEMINI_ERROR)이 발생한다."""
    from google.genai import errors as genai_errors

    body = _make_body()

    gemini = AsyncMock()
    gemini.generate.side_effect = genai_errors.ClientError("Gemini API Error", {"code": 500})

    embed = AsyncMock()
    embed.embed.return_value = [0.1] * 384

    pinecone = AsyncMock()
    pinecone.search.return_value = []

    request = _make_request(gemini=gemini, embed=embed, pinecone=pinecone)
    background_tasks = BackgroundTasks()

    from app.services.recommend_service import recommend

    with pytest.raises(HTTPException) as exc_info:
        await recommend(body, request, background_tasks)

    assert exc_info.value.status_code == 500
    assert "GEMINI_ERROR" in str(exc_info.value.detail)


# ---------------------------------------------------------------------------
# Test 9: BackgroundTasks에 run_background_summary 등록 확인
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_recommend_background_task() -> None:
    """응답 반환 전 background_tasks.add_task(run_background_summary, ...) 가 호출된다."""
    body = _make_body()

    gemini = AsyncMock()
    gemini.generate.return_value = GEMINI_SUCCESS_RESPONSE

    embed = AsyncMock()
    embed.embed.return_value = [0.1] * 384

    pinecone = AsyncMock()
    pinecone.search.return_value = []

    request = _make_request(gemini=gemini, embed=embed, pinecone=pinecone)
    background_tasks = MagicMock(spec=BackgroundTasks)

    from app.services.recommend_service import recommend
    from app.services.background_summary import run_background_summary

    await recommend(body, request, background_tasks)

    background_tasks.add_task.assert_called_once()
    call_args = background_tasks.add_task.call_args

    # 첫 번째 인자가 run_background_summary여야 함
    assert call_args.args[0] is run_background_summary
    # user_message 키워드 인자에 body.user_instruction이 전달돼야 함
    assert call_args.kwargs.get("user_message") == body.user_instruction
    # user_id도 전달돼야 함
    assert call_args.kwargs.get("user_id") == body.user_id
