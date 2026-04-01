"""Unit tests for run_background_summary() pipeline."""

import json
import logging

import pytest
from unittest.mock import AsyncMock

from app.services.background_summary import run_background_summary


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_clients() -> dict:
    """All three client mocks with default happy-path return values."""
    gemini = AsyncMock()
    gemini.generate.return_value = json.dumps({"summary": "테스트 요약"})

    embed = AsyncMock()
    embed.embed.return_value = [0.1] * 384

    pinecone = AsyncMock()
    pinecone.upsert.return_value = "test-id"

    return {"gemini": gemini, "embed": embed, "pinecone": pinecone}


# ---------------------------------------------------------------------------
# Test 1: Gemini generate()가 올바른 인자로 호출된다
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_summary_gemini_call(mock_clients: dict) -> None:
    """run_background_summary가 gemini_client.generate()를
    build_summary_prompt() 결과 + user_message/ai_response 조합 content로 호출한다."""
    from app.prompts.summary import build_summary_prompt

    await run_background_summary(
        user_id="user-1",
        user_message="오늘 점심 뭐 먹었어?",
        ai_response="닭가슴살 샐러드를 드셨군요.",
        gemini_client=mock_clients["gemini"],
        embed_client=mock_clients["embed"],
        pinecone_client=mock_clients["pinecone"],
    )

    expected_system_prompt = build_summary_prompt()
    expected_content = "질문: 오늘 점심 뭐 먹었어?\n답변: 닭가슴살 샐러드를 드셨군요."

    mock_clients["gemini"].generate.assert_called_once()
    call_kwargs = mock_clients["gemini"].generate.call_args.kwargs
    assert call_kwargs["system_prompt"] == expected_system_prompt
    assert call_kwargs["user_content"] == expected_content


# ---------------------------------------------------------------------------
# Test 2: embed_client.embed()가 Gemini 요약 결과로 호출된다
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_summary_embed_call(mock_clients: dict) -> None:
    """Gemini 요약 결과(summary 텍스트)를 embed_client.embed()에 전달한다."""
    await run_background_summary(
        user_id="user-1",
        user_message="오늘 운동했어?",
        ai_response="네, 30분 조깅을 하셨군요.",
        gemini_client=mock_clients["gemini"],
        embed_client=mock_clients["embed"],
        pinecone_client=mock_clients["pinecone"],
    )

    mock_clients["embed"].embed.assert_called_once_with("테스트 요약")


# ---------------------------------------------------------------------------
# Test 3: pinecone_client.upsert()가 올바른 인자로 호출된다
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_summary_pinecone_upsert(mock_clients: dict) -> None:
    """embed 결과 벡터를 pinecone_client.upsert(user_id, vector, summary)로 저장한다."""
    await run_background_summary(
        user_id="user-42",
        user_message="칼로리가 얼마야?",
        ai_response="약 500kcal입니다.",
        gemini_client=mock_clients["gemini"],
        embed_client=mock_clients["embed"],
        pinecone_client=mock_clients["pinecone"],
    )

    expected_vector = [0.1] * 384
    mock_clients["pinecone"].upsert.assert_called_once_with(
        user_id="user-42",
        vector=expected_vector,
        summary="테스트 요약",
    )


# ---------------------------------------------------------------------------
# Test 4: 에러 발생 시 예외가 전파되지 않는다
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_summary_error_silent(mock_clients: dict) -> None:
    """gemini_client.generate()가 Exception을 raise해도 예외가 전파되지 않는다."""
    mock_clients["gemini"].generate.side_effect = Exception("API 오류")

    # 예외가 전파되지 않으면 통과
    await run_background_summary(
        user_id="user-1",
        user_message="테스트",
        ai_response="응답",
        gemini_client=mock_clients["gemini"],
        embed_client=mock_clients["embed"],
        pinecone_client=mock_clients["pinecone"],
    )


# ---------------------------------------------------------------------------
# Test 5: 에러 발생 시 logger.exception()이 호출된다
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_summary_error_logging(
    mock_clients: dict, caplog: pytest.LogCaptureFixture
) -> None:
    """실패 시 logger.exception()이 호출되어 ERROR 레벨 로그가 남는다."""
    mock_clients["gemini"].generate.side_effect = RuntimeError("네트워크 오류")

    with caplog.at_level(logging.ERROR, logger="app.services.background_summary"):
        await run_background_summary(
            user_id="user-1",
            user_message="테스트",
            ai_response="응답",
            gemini_client=mock_clients["gemini"],
            embed_client=mock_clients["embed"],
            pinecone_client=mock_clients["pinecone"],
        )

    assert len(caplog.records) >= 1
    assert caplog.records[0].levelno == logging.ERROR
