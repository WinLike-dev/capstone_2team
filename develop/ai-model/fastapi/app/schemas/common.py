from typing import Any, Optional

from pydantic import BaseModel


class UserProfile(BaseModel):
    """통합 UserProfile — 모든 필드 Optional, 엔드포인트별로 공유.

    /process-meal: medical_history, allergies 사용
    /recommend: activity_level 사용
    """

    gender: Optional[str] = None
    age: Optional[int] = None
    bmi: Optional[float] = None
    goal: Optional[str] = None
    medical_history: Optional[list[str]] = None
    allergies: Optional[list[str]] = None
    activity_level: Optional[str] = None


class ErrorDetail(BaseModel):
    code: str
    message: str


class SuccessResponse(BaseModel):
    status: str = "success"
    data: Any


class ErrorResponse(BaseModel):
    status: str = "error"
    error: ErrorDetail
