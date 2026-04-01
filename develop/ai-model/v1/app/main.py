import logging
import traceback

from fastapi import FastAPI, HTTPException, Request as FastAPIRequest
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import (
    AppError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)
from app.core.lifespan import lifespan
from app.core.middleware import RequestLoggingMiddleware
from app.routers.chat import router as chat_router
from app.routers.debug import router as debug_router
from app.routers.meal import router as meal_router
from app.routers.recommend import router as recommend_router

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Hub", lifespan=lifespan)

# Middleware must be added BEFORE routers are included
app.add_middleware(RequestLoggingMiddleware)

app.include_router(meal_router)
app.include_router(recommend_router)
app.include_router(chat_router)
app.include_router(debug_router)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(AppError)
async def app_error_handler(request: FastAPIRequest, exc: AppError) -> JSONResponse:
    """AppError 및 서브클래스를 구조화된 JSON 에러 응답으로 반환한다."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": {
                "code": exc.error_code,
                "message": exc.message,
            },
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: FastAPIRequest, exc: HTTPException) -> JSONResponse:
    """FastAPI HTTPException을 FastAPI 기본 포맷 대신 구조화 JSON으로 반환한다."""
    # Map common HTTP status codes to error_code strings
    status_to_code: dict[int, str] = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
    }
    error_code = status_to_code.get(exc.status_code, "HTTP_ERROR")
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": {
                "code": error_code,
                "message": message,
            },
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: FastAPIRequest, exc: Exception) -> JSONResponse:
    """예상치 못한 예외를 포착하여 500 + INTERNAL_ERROR로 반환한다. 스택 트레이스는 로그에만 기록."""
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


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
async def health_check():
    settings = get_settings()
    return {"status": "ok", "env": settings.APP_ENV}


# ---------------------------------------------------------------------------
# Test-only routes (used by tests/test_error_handler.py)
# These routes are intentionally minimal and should not be removed.
# ---------------------------------------------------------------------------


@app.get("/test/app-error")
async def test_app_error():
    raise AppError(status_code=400, error_code="BAD_REQUEST", message="테스트 BAD_REQUEST 오류")


@app.get("/test/not-found-error")
async def test_not_found_error():
    raise NotFoundError(message="테스트 리소스를 찾을 수 없습니다.")


@app.get("/test/validation-error")
async def test_validation_error():
    raise ValidationError(message="테스트 유효성 검사 오류")


@app.get("/test/external-service-error")
async def test_external_service_error():
    raise ExternalServiceError(service="WAS", message="timeout")


@app.get("/test/http-exception")
async def test_http_exception():
    raise HTTPException(status_code=404, detail="테스트 HTTP 예외")


@app.get("/test/unhandled-exception")
async def test_unhandled_exception():
    raise RuntimeError("테스트 처리되지 않은 예외")


@app.get("/test/request-id")
async def test_request_id(request: FastAPIRequest):
    """Returns the request_id from request.state for testing middleware."""
    return {"request_id": request.state.request_id}
