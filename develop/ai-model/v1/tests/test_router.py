"""Unit tests for RouterClient.

Uses MagicMock to isolate from real Gemini API calls.
All tests are async using anyio.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.clients.router import RouterClient, RouterOutput
from app.prompts.router import ROUTER_SYSTEM_PROMPT


def _make_client(mock_response_text: str) -> tuple[RouterClient, MagicMock]:
    """Create a RouterClient whose underlying genai.Client is fully mocked.

    Returns (client, mock_generate) where mock_generate is the coroutine mock
    for aio.models.generate_content so callers can inspect call_args.
    """
    mock_response = MagicMock()
    mock_response.text = mock_response_text

    mock_generate = AsyncMock(return_value=mock_response)

    mock_aio_models = MagicMock()
    mock_aio_models.generate_content = mock_generate

    mock_aio = MagicMock()
    mock_aio.models = mock_aio_models

    mock_genai_client = MagicMock()
    mock_genai_client.aio = mock_aio

    with patch("app.clients.router.genai.Client", return_value=mock_genai_client):
        client = RouterClient(api_key="test-key", model_name="gemini-test-model")

    return client, mock_generate


@pytest.mark.anyio
async def test_classify_returns_correct_router_output():
    """Test 1: classify() returns the correct RouterOutput for a normal response."""
    response_json = json.dumps({"mode": 4, "reason": "식단 작성 관련 요청"})
    client, _ = _make_client(response_json)

    result = await client.classify("오늘 뭐 먹지?")

    assert isinstance(result, RouterOutput)
    assert result.mode == 4
    assert result.reason == "식단 작성 관련 요청"


@pytest.mark.anyio
async def test_classify_passes_system_prompt_to_gemini():
    """Test 2: classify() calls generate_content with ROUTER_SYSTEM_PROMPT."""
    response_json = json.dumps({"mode": 1, "reason": "일상 대화"})
    client, mock_generate = _make_client(response_json)

    await client.classify("안녕!")

    assert mock_generate.called
    call_kwargs = mock_generate.call_args.kwargs
    config = call_kwargs.get("config")
    assert config is not None
    assert config.system_instruction == ROUTER_SYSTEM_PROMPT


@pytest.mark.anyio
async def test_classify_falls_back_to_mode_1_on_invalid_json():
    """Test 3: When Gemini returns invalid JSON, classify() returns mode=1."""
    client, _ = _make_client("invalid json {{{")

    result = await client.classify("어떤 메시지")

    assert isinstance(result, RouterOutput)
    assert result.mode == 1


@pytest.mark.anyio
async def test_classify_falls_back_to_mode_1_on_empty_response():
    """Test 4: When Gemini returns empty string, classify() returns mode=1."""
    client, _ = _make_client("")

    result = await client.classify("빈 응답 테스트")

    assert isinstance(result, RouterOutput)
    assert result.mode == 1


@pytest.mark.anyio
async def test_classify_mode_is_within_valid_range():
    """Test 5: For a normal response, mode must be between 1 and 6 inclusive."""
    response_json = json.dumps({"mode": 2, "reason": "운동 플랜 작성 요청"})
    client, _ = _make_client(response_json)

    result = await client.classify("다음 주 운동 계획 세워줘")

    assert 1 <= result.mode <= 6
