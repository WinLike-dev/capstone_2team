"""Unit tests for app/core/lifespan.py.

All external libraries are mocked — no real network calls or model loads.
sentence_transformers is not installed in the CI environment, so it is
injected into sys.modules before the lifespan module is imported.

Covers:
  1. startup sets app.state.embed_client
  2. startup sets app.state.pinecone_client
  3. startup sets app.state.gemini_client
  4. startup sets app.state.router_client
  5. shutdown calls pc.close()
  6. Pinecone init failure propagates (server startup aborted)
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fastapi import FastAPI

from app.core.lifespan import lifespan


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pinecone_mock(*, raise_on_describe: bool = False) -> MagicMock:
    """Return a mock PineconeAsyncio with sensible defaults."""
    pc = MagicMock()
    pc.has_index = AsyncMock(return_value=True)  # index already exists
    pc.close = AsyncMock()

    if raise_on_describe:
        pc.describe_index = AsyncMock(side_effect=RuntimeError("Pinecone unreachable"))
    else:
        description = MagicMock()
        description.host = "test-host.pinecone.io"
        pc.describe_index = AsyncMock(return_value=description)
        pc.IndexAsyncio = MagicMock(return_value=MagicMock())

    return pc


def _common_patches(pc_mock: MagicMock) -> list:
    """Return patch context managers shared across most tests."""
    settings_mock = MagicMock(
        PINECONE_API_KEY="pk",
        PINECONE_INDEX_NAME="test-index",
        GEMINI_API_KEY="gk",
        GEMINI_MODEL_NAME="gemini-2.0-flash",
        ROUTER_API_KEY="rk",
        ROUTER_MODEL_NAME="gemini-2.0-flash-lite",
    )
    return [
        patch("app.core.lifespan.run_in_threadpool", new=AsyncMock(return_value=MagicMock())),
        patch("app.core.lifespan.SentenceTransformer", MagicMock()),
        patch("app.core.lifespan.PineconeAsyncio", return_value=pc_mock),
        patch("app.core.lifespan.EmbeddingClient", MagicMock(return_value=MagicMock())),
        patch("app.core.lifespan.PineconeClient", MagicMock(return_value=MagicMock())),
        patch("app.core.lifespan.GeminiClient", MagicMock(return_value=MagicMock())),
        patch("app.core.lifespan.RouterClient", MagicMock(return_value=MagicMock())),
        patch("app.core.lifespan.get_settings", return_value=settings_mock),
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_startup_sets_embed_client():
    """Lifespan startup must assign app.state.embed_client."""
    pc_mock = _make_pinecone_mock()
    app = FastAPI()

    patches = _common_patches(pc_mock)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7]:
        async with lifespan(app):
            assert hasattr(app.state, "embed_client"), "app.state.embed_client not set"


@pytest.mark.anyio
async def test_startup_sets_pinecone_client():
    """Lifespan startup must assign app.state.pinecone_client."""
    pc_mock = _make_pinecone_mock()
    app = FastAPI()

    patches = _common_patches(pc_mock)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7]:
        async with lifespan(app):
            assert hasattr(app.state, "pinecone_client"), "app.state.pinecone_client not set"


@pytest.mark.anyio
async def test_startup_sets_gemini_client():
    """Lifespan startup must assign app.state.gemini_client."""
    pc_mock = _make_pinecone_mock()
    app = FastAPI()

    patches = _common_patches(pc_mock)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7]:
        async with lifespan(app):
            assert hasattr(app.state, "gemini_client"), "app.state.gemini_client not set"


@pytest.mark.anyio
async def test_startup_sets_router_client():
    """Lifespan startup must assign app.state.router_client."""
    pc_mock = _make_pinecone_mock()
    app = FastAPI()

    patches = _common_patches(pc_mock)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7]:
        async with lifespan(app):
            assert hasattr(app.state, "router_client"), "app.state.router_client not set"


@pytest.mark.anyio
async def test_shutdown_calls_pinecone_close():
    """Lifespan shutdown must call close() on the PineconeAsyncio instance."""
    pc_mock = _make_pinecone_mock()
    app = FastAPI()

    patches = _common_patches(pc_mock)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7]:
        async with lifespan(app):
            pass  # trigger shutdown

    pc_mock.close.assert_called_once()


@pytest.mark.anyio
async def test_pinecone_failure_propagates():
    """When Pinecone init raises, the exception must propagate (server startup aborted)."""
    pc_mock = _make_pinecone_mock(raise_on_describe=True)
    app = FastAPI()

    settings_mock = MagicMock(
        PINECONE_API_KEY="pk",
        PINECONE_INDEX_NAME="test-index",
        GEMINI_API_KEY="gk",
        GEMINI_MODEL_NAME="gemini-2.0-flash",
        ROUTER_API_KEY="rk",
        ROUTER_MODEL_NAME="gemini-2.0-flash-lite",
    )

    with pytest.raises(RuntimeError, match="Pinecone unreachable"):
        with (
            patch("app.core.lifespan.run_in_threadpool", new=AsyncMock(return_value=MagicMock())),
            patch("app.core.lifespan.SentenceTransformer", MagicMock()),
            patch("app.core.lifespan.PineconeAsyncio", return_value=pc_mock),
            patch("app.core.lifespan.EmbeddingClient", MagicMock(return_value=MagicMock())),
            patch("app.core.lifespan.PineconeClient", MagicMock(return_value=MagicMock())),
            patch("app.core.lifespan.GeminiClient", MagicMock(return_value=MagicMock())),
            patch("app.core.lifespan.RouterClient", MagicMock(return_value=MagicMock())),
            patch("app.core.lifespan.get_settings", return_value=settings_mock),
        ):
            async with lifespan(app):
                pass
