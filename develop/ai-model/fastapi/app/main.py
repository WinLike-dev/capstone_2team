import logging
import traceback

from fastapi import FastAPI, Request as FastAPIRequest
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.lifespan import lifespan
from app.routers.meal import router as meal_router
from app.routers.recommend import router as recommend_router

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Hub", lifespan=lifespan)

app.include_router(meal_router)
app.include_router(recommend_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: FastAPIRequest, exc: Exception) -> JSONResponse:
    """예상치 못한 예외를 포착하여 500 + INTERNAL_ERROR로 반환한다."""
    logger.error(
        "Unhandled exception: %s\n%s",
        str(exc),
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "내부 서버 오류가 발생했습니다.",
            },
        },
    )


@app.get("/health")
async def health_check():
    settings = get_settings()
    return {"status": "ok", "env": settings.APP_ENV}
