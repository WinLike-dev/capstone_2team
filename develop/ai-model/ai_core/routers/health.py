from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health Check"])


class HealthCheckResponse(BaseModel):
    status: str
    service: str


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="AI 서버 헬스체크",
    description="서버가 정상 동작 중인지 확인합니다. Load Balancer / Backend 모니터링에서 활용합니다.",
)
async def health_check() -> HealthCheckResponse:
    """GET /health - AI 마이크로서비스 상태 확인."""
    return HealthCheckResponse(status="ok", service="ai-core")
