"""Unit tests for GeminiClient and Mode 7/8 prompt builders."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from google.genai import errors as genai_errors

from app.clients.gemini import GeminiClient
from app.prompts.meal import build_meal_system_prompt
from app.prompts.recommend import build_recommend_system_prompt
from app.schemas.common import UserProfile
from app.schemas.meal import MealAnalysisData
from app.schemas.recommend import RecommendationData


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client_with_mock(mock_generate_content: AsyncMock) -> GeminiClient:
    """GeminiClient를 생성하고 내부 _client를 모킹된 객체로 교체한다."""
    client = GeminiClient.__new__(GeminiClient)
    client._model_name = "gemini-2.0-flash"

    mock_sdk_client = MagicMock()
    mock_sdk_client.aio.models.generate_content = mock_generate_content
    client._client = mock_sdk_client

    return client


# ---------------------------------------------------------------------------
# Test 1: generate()가 generate_content를 올바른 파라미터로 호출한다
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_generate_calls_api_with_correct_params() -> None:
    mock_response = MagicMock(text='{"calories": 500, "message": "good"}')
    mock_gen = AsyncMock(return_value=mock_response)
    client = _make_client_with_mock(mock_gen)

    await client.generate(
        system_prompt="시스템 프롬프트",
        user_content="사용자 입력",
        response_schema=MealAnalysisData,
    )

    mock_gen.assert_called_once()
    call_kwargs = mock_gen.call_args.kwargs
    assert call_kwargs["model"] == "gemini-2.0-flash"
    assert call_kwargs["contents"] == "사용자 입력"
    config = call_kwargs["config"]
    assert config.system_instruction == "시스템 프롬프트"
    assert config.response_mime_type == "application/json"
    assert config.response_schema is MealAnalysisData


# ---------------------------------------------------------------------------
# Test 2: generate()가 response.text를 반환한다
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_generate_returns_response_text() -> None:
    expected_text = '{"calories": 750, "message": "적당한 식사입니다."}'
    mock_gen = AsyncMock(return_value=MagicMock(text=expected_text))
    client = _make_client_with_mock(mock_gen)

    result = await client.generate(
        system_prompt="프롬프트",
        user_content="닭가슴살 200g",
        response_schema=MealAnalysisData,
    )

    assert result == expected_text


# ---------------------------------------------------------------------------
# Test 3: ResourceExhausted(429) 에러 발생 시 tenacity가 재시도한다
# ---------------------------------------------------------------------------


def _make_429_error() -> genai_errors.ClientError:
    """429 ClientError 인스턴스를 생성한다."""
    err = genai_errors.ClientError.__new__(genai_errors.ClientError)
    err.code = 429
    err.message = "Resource exhausted"
    err.status = "RESOURCE_EXHAUSTED"
    err.details = {"error": {"code": 429, "message": "quota exceeded"}}
    err.response = None
    Exception.__init__(err, "429 RESOURCE_EXHAUSTED. quota exceeded")
    return err


@pytest.mark.anyio
async def test_generate_retries_on_resource_exhausted() -> None:
    """첫 번째 호출에서 429 에러, 두 번째에서 성공하는 경우 재시도 후 성공한다."""
    success_response = MagicMock(text='{"calories": 300, "message": "가벼운 식사"}')
    mock_gen = AsyncMock(
        side_effect=[_make_429_error(), success_response]
    )
    client = _make_client_with_mock(mock_gen)

    # tenacity wait을 0으로 오버라이드하여 테스트 속도 확보
    from tenacity import wait_none
    client.generate.retry.wait = wait_none()

    result = await client.generate(
        system_prompt="프롬프트",
        user_content="입력",
        response_schema=MealAnalysisData,
    )

    assert mock_gen.call_count == 2
    assert result == '{"calories": 300, "message": "가벼운 식사"}'


# ---------------------------------------------------------------------------
# Test 4: build_meal_system_prompt()가 UserProfile 필드를 프롬프트에 주입한다
# ---------------------------------------------------------------------------


def test_build_meal_system_prompt_injects_user_profile() -> None:
    profile = UserProfile(
        gender="male",
        age=25,
        bmi=22.5,
        goal="체중 감량",
        medical_history=["당뇨"],
        allergies=["견과류"],
    )

    prompt = build_meal_system_prompt(profile)

    assert "male" in prompt
    assert "25" in prompt
    assert "22.5" in prompt
    assert "체중 감량" in prompt
    assert "당뇨" in prompt
    assert "견과류" in prompt
    assert "한국어" in prompt


# ---------------------------------------------------------------------------
# Test 5: build_recommend_system_prompt()가 UserProfile 필드를 프롬프트에 주입한다
# ---------------------------------------------------------------------------


def test_build_recommend_system_prompt_injects_user_profile() -> None:
    profile = UserProfile(
        gender="female",
        age=30,
        bmi=20.0,
        goal="근력 향상",
        activity_level="활동적",
    )

    prompt = build_recommend_system_prompt(profile)

    assert "female" in prompt
    assert "30" in prompt
    assert "20.0" in prompt
    assert "근력 향상" in prompt
    assert "활동적" in prompt
    assert "한국어" in prompt


# ---------------------------------------------------------------------------
# Test 6: UserProfile 필드가 None일 때 "정보 없음"으로 대체된다
# ---------------------------------------------------------------------------


def test_build_meal_system_prompt_none_fields_replaced() -> None:
    profile = UserProfile()  # 모든 필드 None

    prompt = build_meal_system_prompt(profile)

    assert "정보 없음" in prompt


def test_build_recommend_system_prompt_none_fields_replaced() -> None:
    profile = UserProfile()  # 모든 필드 None

    prompt = build_recommend_system_prompt(profile)

    assert "정보 없음" in prompt
