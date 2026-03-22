"""대화 요약 프롬프트 및 출력 스키마."""

from pydantic import BaseModel


class SummaryOutput(BaseModel):
    """Gemini 요약 응답 스키마.

    summary 필드는 Optional이 아님 — 반드시 존재해야 한다.
    """

    summary: str


SUMMARY_SYSTEM_PROMPT: str = (
    "당신은 대화 요약 전문가입니다.\n"
    "주어진 질문과 답변을 2-3문장으로 간결하게 요약하세요.\n"
    "한국어로 응답하세요."
)


def build_summary_prompt() -> str:
    """요약 시스템 프롬프트를 반환한다."""
    return SUMMARY_SYSTEM_PROMPT
