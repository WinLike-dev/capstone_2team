from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """애플리케이션 설정. 환경변수 또는 .env 파일에서 자동 로딩."""

    # Google Gemini API Key
    google_api_key: str

    # 앱 환경
    app_env: str = "development"
    app_port: int = 8000

    # CORS 허용 오리진 (쉼표로 구분된 문자열 → 리스트로 변환)
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # Gemini 모델 설정
    gemini_model: str = "gemini-flash-lite-latest"
    gemini_temperature: float = 0.3  # 헬스케어: 낮은 temperature로 일관된 응답 유도

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """설정 싱글톤 반환 (캐시)."""
    return Settings()
