"""FastAPI lifespan — 클라이언트 초기화 및 LangGraph 빌드."""
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from pinecone import PineconeAsyncio, ServerlessSpec

from app.clients.embedding import EMBEDDING_DIM, EmbeddingClient
from app.clients.gemini import GeminiClient
from app.clients.pinecone import PineconeClient
from app.clients.was import WASClient
from app.core.config import get_settings
from app.graph.builder import build_graph
from app.graph.deps import NodeDeps

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    # 1. EmbeddingClient
    embed_client = EmbeddingClient(api_key=settings.GEMINI_API_KEY)
    logger.info("EmbeddingClient initialized (dim=%d)", EMBEDDING_DIM)

    # 2. Pinecone
    pc = PineconeAsyncio(api_key=settings.PINECONE_API_KEY)
    app.state._pinecone_control = pc

    if not await pc.has_index(settings.PINECONE_INDEX_NAME):
        await pc.create_index(
            name=settings.PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

    description = await pc.describe_index(settings.PINECONE_INDEX_NAME)
    index = pc.IndexAsyncio(host=description.host)
    pinecone_client = PineconeClient(index)
    logger.info("Pinecone initialized (index=%s)", settings.PINECONE_INDEX_NAME)

    # 3. Gemini Flash (응답 생성)
    gemini_client = GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.GEMINI_MODEL_NAME,
    )
    logger.info("GeminiClient initialized (model=%s)", settings.GEMINI_MODEL_NAME)

    # 4. Gemini Flash-Lite (의도 분석 · 평가)
    router_client = GeminiClient(
        api_key=settings.ROUTER_API_KEY,
        model_name=settings.ROUTER_MODEL_NAME,
    )
    logger.info("RouterClient initialized (model=%s)", settings.ROUTER_MODEL_NAME)

    # 5. WASClient
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(settings.WAS_TIMEOUT))
    was_client = WASClient(base_url=settings.WAS_BASE_URL, client=http_client)
    app.state._was_http_client = http_client
    logger.info("WASClient initialized (base_url=%s)", settings.WAS_BASE_URL)

    # 6. LangGraph 빌드
    deps = NodeDeps(
        gemini=gemini_client,
        router=router_client,
        was=was_client,
        pinecone=pinecone_client,
        embed=embed_client,
    )
    app.state.graph = build_graph(deps)
    app.state.deps = deps
    logger.info("LangGraph compiled and ready")

    yield

    # Shutdown
    await app.state._pinecone_control.close()
    await app.state._was_http_client.aclose()
    logger.info("Shutdown complete")
