from pydantic import BaseModel, Field
from typing import Optional


# ── 사용자 프로필 (엔드포인트별 변형) ────────────────────────────────────────

class BaseUserProfile(BaseModel):
    """모든 AI 요청에 공통으로 포함되는 사용자 건강 프로필."""
    gender: str = Field(..., description="성별 ('male' 또는 'female')")
    age: int = Field(..., description="나이")
    bmi: float = Field(..., description="BMI 수치 (Front에서 계산하여 전달)")
    goal: str = Field(..., description="건강/운동 목표 (예: '체중 감량', '근육 증가')")


class ChatUserProfile(BaseUserProfile):
    """POST /ai-chat 전용 사용자 프로필."""
    pass


class MealUserProfile(BaseUserProfile):
    """POST /process-meal 전용 사용자 프로필 (기저질환·알러지 포함)."""
    medical_history: list[str] = Field(
        default_factory=list,
        description="기저질환 목록 (예: ['고혈압', '당뇨'])",
    )
    allergies: list[str] = Field(
        default_factory=list,
        description="알러지 목록 (예: ['견과류', '갑각류'])",
    )


class RecommendUserProfile(BaseUserProfile):
    """POST /recommend 전용 사용자 프로필 (활동량 포함)."""
    activity_level: Optional[str] = Field(
        None,
        description="평소 활동량 (예: '활동적', '보통', '비활동적')",
    )


# ── 요청 바디 ────────────────────────────────────────────────────────────────

class AIChatRequest(BaseModel):
    """POST /ai-chat 요청 바디 (모드 1~6 채팅)."""
    user_id: str = Field(..., description="사용자 고유 ID")
    user_profile: ChatUserProfile = Field(..., description="사용자 건강 프로필")
    user_instruction: Optional[str] = Field(
        None,
        description="사용자 개인 지시사항 (DB의 user_instruction 필드)",
    )
    user_message: str = Field(..., description="사용자 채팅 메시지")


class MealRequest(BaseModel):
    """POST /process-meal 요청 바디 (식단 기록 — Router AI 바이패스)."""
    user_id: str = Field(..., description="사용자 고유 ID")
    user_profile: MealUserProfile = Field(..., description="사용자 건강 프로필")
    user_instruction: Optional[str] = Field(
        None,
        description="사용자 개인 지시사항",
    )
    user_message: str = Field(
        ...,
        description="기록할 식사 메시지 (예: '점심에 닭가슴살 샐러드 먹었어')",
    )


class RecommendRequest(BaseModel):
    """POST /recommend 요청 바디 (운동·식단 추천 — AI 전체 바이패스)."""
    user_id: str = Field(..., description="사용자 고유 ID")
    user_profile: RecommendUserProfile = Field(..., description="사용자 건강 프로필")
    user_instruction: Optional[str] = Field(
        None,
        description="개인화된 추천을 위한 사용자 지시사항",
    )
