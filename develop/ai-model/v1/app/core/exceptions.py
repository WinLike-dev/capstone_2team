"""Custom exception classes for structured error handling."""


class AppError(Exception):
    """Base application exception with structured error response support.

    All subclasses map to a structured JSON error response:
      {"status": "error", "error": {"code": "<error_code>", "message": "<message>"}}
    """

    def __init__(self, status_code: int, error_code: str, message: str) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    """Raised when a requested resource is not found (HTTP 404)."""

    def __init__(self, message: str = "요청한 리소스를 찾을 수 없습니다.") -> None:
        super().__init__(status_code=404, error_code="NOT_FOUND", message=message)


class ValidationError(AppError):
    """Raised when request data fails validation (HTTP 422)."""

    def __init__(self, message: str = "요청 데이터가 유효하지 않습니다.") -> None:
        super().__init__(status_code=422, error_code="VALIDATION_ERROR", message=message)


class ExternalServiceError(AppError):
    """Raised when an external service (e.g. WAS) call fails (HTTP 502).

    The service name is prepended to the message for clarity.
    """

    def __init__(self, service: str, message: str) -> None:
        full_message = f"{service}: {message}"
        super().__init__(status_code=502, error_code="EXTERNAL_SERVICE_ERROR", message=full_message)
