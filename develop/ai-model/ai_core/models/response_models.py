from pydantic import BaseModel, Field
from typing import Optional, Literal


class UIComponents(BaseModel):
    """AI가 Frontend에 전달하는 UI 제어 명령."""
    theme: Optional[str] = Field(
        None,
        description="UI 테마 (예: 'calm', 'dark', 'rainy_mood', 'energetic')"
    )
    widget: Optional[str] = Field(
        None,
        description="마운트할 위젯 타입 (예: 'meditation_video', 'breathing_exercise', null)"
    )
    highlight_color: Optional[str] = Field(
        None,
        description="강조 색상 hex 코드 (예: '#4A90E2')"
    )


class GenerateResponse(BaseModel):
    """POST /api/v1/generate 응답 바디.
    
    Frontend는 이 JSON을 파싱하여:
    - action_type == 'advice'   → text_response 텍스트를 채팅 말풍선으로 표시
    - action_type == 'ui_update' → ui_components 값으로 화면 상태 동적 제어
    - action_type == 'referral'  → 전문가 상담 안내 팝업 표시
    """
    action_type: Literal["advice", "ui_update", "referral"] = Field(
        ...,
        description="AI 응답 액션 유형"
    )
    text_response: str = Field(
        ...,
        description="사용자에게 표시할 텍스트 답변"
    )
    ui_components: UIComponents = Field(
        default_factory=UIComponents,
        description="Frontend UI 제어 명령 (선택적)"
    )


class ErrorResponse(BaseModel):
    """에러 응답 바디."""
    error: str = Field(..., description="에러 메시지")
    detail: Optional[str] = Field(None, description="상세 에러 정보")
