"""
Unit tests for PineconeClient.
All Pinecone I/O is mocked — no real network calls.
"""
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.clients.pinecone import PineconeClient


def _make_mock_index() -> MagicMock:
    """Return a MagicMock that mimics pinecone IndexAsyncio."""
    index = MagicMock()
    index.upsert = AsyncMock(return_value=None)
    return index


def _make_query_response(matches: list[dict]) -> MagicMock:
    """Build a mock QueryResponse with a .matches list."""
    response = MagicMock()
    mock_matches = []
    for m in matches:
        mm = MagicMock()
        mm.id = m["id"]
        mm.score = m["score"]
        mm.metadata = m.get("metadata", {})
        mock_matches.append(mm)
    response.matches = mock_matches
    return response


# ---------------------------------------------------------------------------
# Test 1: upsert() calls index.upsert with namespace=user_id and returns UUID
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_upsert_calls_index_with_correct_namespace():
    index = _make_mock_index()
    client = PineconeClient(index)

    result_id = await client.upsert(
        user_id="user_A",
        vector=[0.1, 0.2, 0.3],
        summary="오늘 닭가슴살 200g 섭취",
    )

    # index.upsert must have been called exactly once
    index.upsert.assert_called_once()
    call_kwargs = index.upsert.call_args

    # namespace parameter must equal user_id
    assert call_kwargs.kwargs.get("namespace") == "user_A"

    # vectors list must contain exactly one item
    vectors = call_kwargs.kwargs.get("vectors", [])
    assert len(vectors) == 1

    # returned id must be a non-empty string (UUID4)
    assert isinstance(result_id, str)
    assert len(result_id) == 36  # UUID4 canonical form


# ---------------------------------------------------------------------------
# Test 2: upsert() stores correct metadata (user_id, summary, timestamp)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_upsert_stores_correct_metadata():
    index = _make_mock_index()
    client = PineconeClient(index)

    await client.upsert(
        user_id="user_A",
        vector=[0.1, 0.2],
        summary="런닝 30분",
    )

    vectors = index.upsert.call_args.kwargs["vectors"]
    metadata = vectors[0]["metadata"]

    assert metadata["user_id"] == "user_A"
    assert metadata["summary"] == "런닝 30분"
    assert "timestamp" in metadata
    assert isinstance(metadata["timestamp"], str)


# ---------------------------------------------------------------------------
# Test 3: search() calls index.query with namespace=user_id, top_k
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_search_calls_index_with_correct_namespace():
    index = _make_mock_index()
    index.query = AsyncMock(return_value=_make_query_response([
        {"id": "vec-1", "score": 0.95, "metadata": {"summary": "테스트", "timestamp": "2024-01-01T00:00:00"}},
    ]))
    client = PineconeClient(index)

    await client.search(user_id="user_B", vector=[0.5, 0.6], top_k=3)

    index.query.assert_called_once()
    call_kwargs = index.query.call_args.kwargs

    assert call_kwargs.get("namespace") == "user_B"
    assert call_kwargs.get("top_k") == 3
    assert call_kwargs.get("include_metadata") is True


# ---------------------------------------------------------------------------
# Test 4: search() returns [{id, score, summary, timestamp}] shaped list
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_search_returns_correct_shape():
    index = _make_mock_index()
    index.query = AsyncMock(return_value=_make_query_response([
        {"id": "vec-1", "score": 0.95, "metadata": {"summary": "닭가슴살", "timestamp": "2024-01-01T10:00:00"}},
        {"id": "vec-2", "score": 0.80, "metadata": {"summary": "런닝", "timestamp": "2024-01-02T08:00:00"}},
    ]))
    client = PineconeClient(index)

    results = await client.search(user_id="user_A", vector=[0.1, 0.2])

    assert isinstance(results, list)
    assert len(results) == 2

    first = results[0]
    assert first["id"] == "vec-1"
    assert first["score"] == pytest.approx(0.95)
    assert first["summary"] == "닭가슴살"
    assert first["timestamp"] == "2024-01-01T10:00:00"


# ---------------------------------------------------------------------------
# Test 5: namespace isolation — different user_ids never share namespace
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_namespace_isolation_between_users():
    index = _make_mock_index()
    client = PineconeClient(index)

    await client.upsert(user_id="user_A", vector=[0.1], summary="A의 기록")
    await client.upsert(user_id="user_B", vector=[0.2], summary="B의 기록")

    calls = index.upsert.call_args_list
    namespace_a = calls[0].kwargs["namespace"]
    namespace_b = calls[1].kwargs["namespace"]

    assert namespace_a == "user_A"
    assert namespace_b == "user_B"
    assert namespace_a != namespace_b
