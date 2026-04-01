from functools import lru_cache

from pydantic_settings import BaseSettings


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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
