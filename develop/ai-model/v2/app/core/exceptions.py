"""Custom exception classes for structured error handling."""


class AppError(Exception):
    def __init__(self, status_code: int, error_code: str, message: str) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "요청한 리소스를 찾을 수 없습니다.") -> None:
        super().__init__(status_code=404, error_code="NOT_FOUND", message=message)


class ValidationError(AppError):
    def __init__(self, message: str = "요청 데이터가 유효하지 않습니다.") -> None:
        super().__init__(status_code=422, error_code="VALIDATION_ERROR", message=message)


class ExternalServiceError(AppError):
    def __init__(self, service: str, message: str, *, status_code: int | None = None) -> None:
        self.service = service
        self.external_status_code = status_code
        super().__init__(
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            message=f"{service}: {message}",
        )

    def is_http_status(self, *codes: int) -> bool:
        return self.external_status_code in set(codes)


class GraphExecutionError(AppError):
    def __init__(self, message: str = "그래프 실행 중 오류가 발생했습니다.") -> None:
        super().__init__(status_code=500, error_code="GRAPH_EXECUTION_ERROR", message=message)
