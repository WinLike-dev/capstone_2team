"""
헬스 메이트 - FastAPI 애플리케이션 진입점

실행 방법:
  uvicorn main:app --reload --host 0.0.0.0 --port 8000

환경변수:
  GOOGLE_API_KEY : Google AI Studio API 키 (.env 파일 또는 환경변수로 주입)
"""
from dotenv import load_dotenv

load_dotenv()  # .env 파일에서 GOOGLE_API_KEY 로드

from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="헬스 메이트 AI API",
    description="LangGraph 기반 맞춤형 운동/식단 플랜 생성 서비스",
    version="0.1.0",
)

app.include_router(router)
