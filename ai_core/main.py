import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routers import generate, health

# ─────────────────────────────────────────────────────────────────────────────
# 로깅 설정
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 앱 Lifespan (시작/종료 훅)
# ─────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(
        "AI Core 서버 시작. env=%s, model=%s, port=%d",
        settings.app_env,
        settings.gemini_model,
        settings.app_port,
    )
    yield
    logger.info("AI Core 서버 종료.")


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI 앱 초기화
# ─────────────────────────────────────────────────────────────────────────────
settings = get_settings()

app = FastAPI(
    title="AI Core - Healthcare AI Microservice",
    description=(
        "LangChain + Gemini Flash 기반 헬스케어 AI 마이크로서비스. "
        "Backend 서버에서 사용자 컨텍스트를 전달받아 구조화된 JSON 응답을 생성합니다."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 설정 (Backend 및 개발 환경 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(health.router)
app.include_router(generate.router)


# ─────────────────────────────────────────────────────────────────────────────
# 직접 실행 (python main.py)
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=(settings.app_env == "development"),
    )
