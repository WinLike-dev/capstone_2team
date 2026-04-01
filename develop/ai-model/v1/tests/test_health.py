import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_health_returns_200():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_settings_missing_env_raises(monkeypatch):
    """필수 환경변수 누락 시 ValidationError 발생 확인"""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("PINECONE_API_KEY", raising=False)
    monkeypatch.delenv("PINECONE_INDEX_NAME", raising=False)
    monkeypatch.delenv("WAS_BASE_URL", raising=False)
    # lru_cache 초기화
    from app.core.config import get_settings
    get_settings.cache_clear()
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        from app.core.config import Settings
        Settings(_env_file=None)  # .env 파일도 무시
