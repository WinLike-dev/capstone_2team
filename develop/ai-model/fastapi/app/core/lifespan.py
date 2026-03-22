"""FastAPI lifespan: initialize and shut down all clients in the correct order.

Startup order (per CONTEXT.md decision):
  1. EmbeddingClient (CPU-bound model load via run_in_threadpool)
  2. PineconeClient  (async index init, creates index if absent)
  3. GeminiClient    (lightweight constructor, no I/O)
  4. RouterClient    (lightweight constructor, no I/O)
  5. WASClient       (httpx.AsyncClient with 10s timeout)

Shutdown:
  - Close PineconeAsyncio control-plane connection.
  - Close httpx.AsyncClient used by WASClient.

Initialization failures are NOT caught — exceptions propagate and FastAPI
aborts server startup, preventing a partially-initialized state.
"""
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from pinecone import PineconeAsyncio, ServerlessSpec
from sentence_transformers import SentenceTransformer
from starlette.concurrency import run_in_threadpool

from app.clients import EMBEDDING_DIM, EmbeddingClient, GeminiClient, PineconeClient, RouterClient, WASClient
from app.core.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan: startup initialization and shutdown cleanup."""
    settings = get_settings()

    # ------------------------------------------------------------------ #
    # Startup                                                              #
    # ------------------------------------------------------------------ #

    # 1. Embedding model (CPU-bound — offload to thread pool)
    model = await run_in_threadpool(
        SentenceTransformer, "paraphrase-multilingual-MiniLM-L12-v2"
    )
    app.state.embed_client = EmbeddingClient(model)
    logger.info("Embedding model loaded (dim=%d)", EMBEDDING_DIM)

    # 2. Pinecone index
    pc = PineconeAsyncio(api_key=settings.PINECONE_API_KEY)
    app.state._pinecone_control = pc  # kept for shutdown cleanup

    if not await pc.has_index(settings.PINECONE_INDEX_NAME):
        await pc.create_index(
            name=settings.PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

    description = await pc.describe_index(settings.PINECONE_INDEX_NAME)
    index = pc.IndexAsyncio(host=description.host)
    app.state.pinecone_client = PineconeClient(index)
    logger.info("Pinecone initialized (index=%s)", settings.PINECONE_INDEX_NAME)

    # 3. Gemini client
    app.state.gemini_client = GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.GEMINI_MODEL_NAME,
    )
    logger.info("Gemini client initialized (model=%s)", settings.GEMINI_MODEL_NAME)

    # 4. Router client
    app.state.router_client = RouterClient(
        api_key=settings.ROUTER_API_KEY,
        model_name=settings.ROUTER_MODEL_NAME,
    )
    logger.info("Router client initialized (model=%s)", settings.ROUTER_MODEL_NAME)

    # 5. WAS HTTP client (httpx.AsyncClient with 10s timeout)
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
    app.state.was_client = WASClient(base_url=settings.WAS_BASE_URL, client=http_client)
    app.state._was_http_client = http_client  # kept for shutdown cleanup
    logger.info("WAS client initialized (base_url=%s)", settings.WAS_BASE_URL)

    yield

    # ------------------------------------------------------------------ #
    # Shutdown                                                             #
    # ------------------------------------------------------------------ #
    await app.state._pinecone_control.close()
    logger.info("Pinecone connection closed")

    await app.state._was_http_client.aclose()
    logger.info("WAS HTTP client closed")
