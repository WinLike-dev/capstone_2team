from pydantic import BaseModel, Field
from typing import Optional


class ChatMessage(BaseModel):
    """단일 채팅 메시지."""
    role: str = Field(..., description="발화자 역할: 'user' 또는 'assistant'")
    content: str = Field(..., description="메시지 내용")


class UserContext(BaseModel):
    """Backend에서 전달하는 사용자 상태 정보."""
    age: Optional[int] = Field(None, description="사용자 나이")
    gender: Optional[str] = Field(None, description="성별 (male/female/other)")
    height: Optional[float] = Field(None, description="키 (cm)")
    weight: Optional[float] = Field(None, description="체중 (kg)")
    mbti: Optional[str] = Field(None, description="MBTI 유형 (예: 'INFP', 'ENTJ')")



class GenerateRequest(BaseModel):
    """POST /api/v1/generate 요청 바디."""
    user_id: str = Field(..., description="사용자 고유 ID")
    user_context: UserContext = Field(..., description="사용자 상태 정보 (Backend DB 기반)")
    chat_history: list[ChatMessage] = Field(
        default_factory=list,
        description="이전 대화 이력 (오래된 것부터)"
    )
    current_message: str = Field(..., description="사용자 현재 발화")
