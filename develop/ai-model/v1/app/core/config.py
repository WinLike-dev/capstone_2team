from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    # Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash"
    # Router
    ROUTER_API_KEY: str
    ROUTER_MODEL_NAME: str = "gemini-2.5-flash-lite"
    # Pinecone
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str
    # WAS
    WAS_BASE_URL: str
    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ENV_FILE, "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
