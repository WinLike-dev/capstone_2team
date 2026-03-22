"""Request logging middleware with request_id injection and timing."""
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that injects a UUID4 request_id and logs structured request/response info.

    For every request:
    - Generates a UUID4 request_id and stores it in request.state.request_id
    - Adds X-Request-ID header to the response
    - Logs structured key=value pairs: request_id, method, path, status, duration_ms
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            logger.info(
                "request_id=%s method=%s path=%s status=%s duration_ms=%.1f",
                request_id,
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )
        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "request_id=%s method=%s path=%s status=500 duration_ms=%.1f error=%s",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
                str(exc),
            )
            raise

        response.headers["X-Request-ID"] = request_id
        return response
