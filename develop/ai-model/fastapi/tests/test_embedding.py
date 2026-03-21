"""Unit tests for EmbeddingClient."""
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from app.clients.embedding import EMBEDDING_DIM, EmbeddingClient


@pytest.mark.anyio
async def test_embed_returns_384_dim_list():
    """embed() returns a list of 384 floats for Korean text."""
    mock_model = MagicMock()
    mock_model.encode.return_value = np.zeros(384, dtype=np.float32)

    client = EmbeddingClient(model=mock_model)

    with patch(
        "app.clients.embedding.run_in_threadpool",
        new=AsyncMock(return_value=np.zeros(384, dtype=np.float32)),
    ):
        result = await client.embed("안녕하세요")

    assert isinstance(result, list), "embed() must return a list"
    assert len(result) == 384, f"Expected 384 dims, got {len(result)}"
    assert all(isinstance(v, float) for v in result), "All elements must be float"


@pytest.mark.anyio
async def test_embed_uses_run_in_threadpool():
    """embed() must delegate encoding to run_in_threadpool to avoid blocking the event loop."""
    mock_model = MagicMock()

    client = EmbeddingClient(model=mock_model)

    with patch(
        "app.clients.embedding.run_in_threadpool",
        new=AsyncMock(return_value=np.zeros(384, dtype=np.float32)),
    ) as mock_threadpool:
        await client.embed("hello")

    mock_threadpool.assert_called_once()
    args = mock_threadpool.call_args
    # First positional arg should be the model's encode method
    assert args[0][0] == mock_model.encode


@pytest.mark.anyio
async def test_embed_empty_string_returns_384_dim():
    """embed() with empty string still returns a 384-dim vector."""
    mock_model = MagicMock()

    client = EmbeddingClient(model=mock_model)

    with patch(
        "app.clients.embedding.run_in_threadpool",
        new=AsyncMock(return_value=np.zeros(384, dtype=np.float32)),
    ):
        result = await client.embed("")

    assert len(result) == 384, f"Expected 384 dims for empty string, got {len(result)}"


def test_embedding_dim_constant():
    """EMBEDDING_DIM constant must equal 384."""
    assert EMBEDDING_DIM == 384
