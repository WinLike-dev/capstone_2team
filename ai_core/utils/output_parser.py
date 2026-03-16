import logging
from typing import Any

logger = logging.getLogger(__name__)

# 인텐트 번호 → action_type, ui_components 매핑
INTENT_RESPONSE_MAP: dict[int, dict[str, Any]] = {
    1: {
        "action_type": "advice",
        "ui_components": {"theme": None, "widget": None, "highlight_color": None},
    },
    2: {
        "action_type": "ui_update",
        "ui_components": {"theme": None, "widget": "plan_editor", "highlight_color": None},
    },
    3: {
        "action_type": "ui_update",
        "ui_components": {"theme": None, "widget": "profile_editor", "highlight_color": None},
    },
    4: {
        "action_type": "ui_update",
        "ui_components": {"theme": None, "widget": "diet_planner", "highlight_color": None},
    },
}

FALLBACK_RESPONSE: dict[str, Any] = {
    "action_type": "advice",
    "text_response": (
        "죄송합니다. 일시적인 오류가 발생했습니다. "
        "잠시 후 다시 시도해 주세요. "
        "긴급한 건강 문제가 있다면 전문의 상담을 받으시기 바랍니다."
    ),
    "ui_components": {"theme": None, "widget": None, "highlight_color": None},
}


def parse_intent(raw_intent: str) -> int:
    """
    인텐트 분류기 LLM 출력에서 유효한 인텐트 번호(1~4)를 추출합니다.
    파싱 실패 시 기본값 1(단순 질문)을 반환합니다.
    """
    stripped = raw_intent.strip()
    for ch in stripped:
        if ch in ("1", "2", "3", "4"):
            return int(ch)
    logger.warning("인텐트 파싱 실패, 기본값 1로 폴백. raw=%r", stripped)
    return 1


def wrap_plain_text_response(text: str, intent: int) -> dict[str, Any]:
    """
    메인 AI의 평문 답변을 GenerateResponse 형태의 딕셔너리로 래핑합니다.

    Args:
        text: 메인 AI가 생성한 평문 답변
        intent: 인텐트 번호(1~4)

    Returns:
        GenerateResponse 구조의 딕셔너리
    """
    mapping = INTENT_RESPONSE_MAP.get(intent, INTENT_RESPONSE_MAP[1])
    return {
        "action_type": mapping["action_type"],
        "text_response": text.strip(),
        "ui_components": mapping["ui_components"],
    }
