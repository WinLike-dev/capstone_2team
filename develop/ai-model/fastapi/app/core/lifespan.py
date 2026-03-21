import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Phase 2에서 Pinecone, httpx, 임베딩 모델 초기화 추가 예정
    # 현재는 placeholder 로그만
    logger.info("Starting up — client initialization placeholder")
    yield
    # Shutdown: Phase 2에서 cleanup 추가 예정
    logger.info("Shutting down — cleanup placeholder")
