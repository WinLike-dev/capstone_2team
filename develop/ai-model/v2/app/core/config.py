from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Gemini Flash (응답 생성)
    GEMINI_API_KEY: str
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash"
    # Gemini Flash-Lite (의도 분석 · 검색 평가)
    ROUTER_API_KEY: str
    ROUTER_MODEL_NAME: str = "gemini-2.5-flash-lite"
    # Pinecone
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str
    # WAS
    WAS_BASE_URL: str
    WAS_TIMEOUT: float = 10.0
    # Summary
    SUMMARY_TURN_INTERVAL: int = 10  # 턴 카운터 임계값
    MAX_MESSAGES: int = 20            # State에 보관할 최대 메시지 수
    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
