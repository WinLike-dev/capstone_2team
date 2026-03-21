from fastapi import FastAPI

from app.core.config import get_settings
from app.core.lifespan import lifespan
from app.routers.meal import router as meal_router
from app.routers.recommend import router as recommend_router

app = FastAPI(title="AI Hub", lifespan=lifespan)

app.include_router(meal_router)
app.include_router(recommend_router)


@app.get("/health")
async def health_check():
    settings = get_settings()
    return {"status": "ok", "env": settings.APP_ENV}
