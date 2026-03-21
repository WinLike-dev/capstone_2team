from fastapi import FastAPI

from app.core.config import get_settings
from app.core.lifespan import lifespan

app = FastAPI(title="AI Hub", lifespan=lifespan)


@app.get("/health")
async def health_check():
    settings = get_settings()
    return {"status": "ok", "env": settings.APP_ENV}


# Phase 2에서 router include 추가 예정
# app.include_router(meal_router, prefix="/api/v1")
# app.include_router(recommend_router, prefix="/api/v1")
