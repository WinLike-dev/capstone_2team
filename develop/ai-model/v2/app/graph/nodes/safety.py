"""Safety response node for urgent-risk conversations."""
from __future__ import annotations

import logging
import re
from datetime import datetime

from app.graph.deps import NodeDeps
from app.schemas.state import GraphState

logger = logging.getLogger(__name__)

_MENTAL_HEALTH_SAFETY_PATTERNS = re.compile(
    r"자해|자살|죽고\s*싶|극단적\s*선택|충동|해치고\s*싶|살고\s*싶지"
)
_PHYSICAL_SAFETY_PATTERNS = re.compile(
    r"가슴.*조여|숨이?\s*차|호흡.*힘들|어지럽|쓰러질\s*것\s*같|실신|기절|"
    r"과다\s*복용|심한\s*통증|출혈|피가\s*멈추지"
)

_MENTAL_HEALTH_RESPONSE = (
    "지금은 운동이나 식단보다 즉시 사람과 연결되는 것이 먼저입니다.\n\n"
    "가까운 사람이나 보호자에게 지금 상태를 바로 알리고, "
    "자살예방상담전화 109 또는 정신건강상담전화 1577-0199에 즉시 연락하세요.\n"
    "당장 위험이 크면 119 또는 가까운 응급실로 바로 도움을 요청하세요.\n\n"
    "혼자 있지 말고, 위험한 물건이나 약물이 손에 닿지 않게 멀리하세요."
)

_PHYSICAL_EMERGENCY_RESPONSE = (
    "이건 운동 조언보다 즉시 응급 대응이 우선일 수 있는 증상입니다.\n\n"
    "지금 바로 운동을 멈추고 앉거나 누워 안정을 취하세요. "
    "증상이 계속되거나 심해지면 119에 연락하거나 가까운 응급실로 가야 합니다.\n"
    "혼자 이동하지 말고 가능하면 주변 사람에게 도움을 요청하세요.\n\n"
    "가슴 통증, 숨참, 심한 어지럼, 의식 저하, 과다 복용 의심이 있으면 "
    "운동을 다시 하지 말고 바로 진료를 받으세요."
)

_ESCALATION_INTENSITY_THRESHOLD = 0.8


def make_safety_node(deps: NodeDeps):
    async def safety_node(state: GraphState) -> dict:
        emotion = state.get("emotion") or {}
        intensity = emotion.get("intensity", 0.0)
        user_id = state["user_id"]
        message = state["user_message"]
        safety_kind = _classify_safety_kind(message)
        response = (
            _MENTAL_HEALTH_RESPONSE
            if safety_kind == "mental_health_crisis"
            else _PHYSICAL_EMERGENCY_RESPONSE
        )

        logger.warning(
            "SAFETY_BLOCK | user_id=%s | kind=%s | message=%r | emotion_intensity=%.2f | timestamp=%s",
            user_id,
            safety_kind,
            message[:100],
            intensity,
            datetime.utcnow().isoformat(),
        )

        if intensity >= _ESCALATION_INTENSITY_THRESHOLD:
            logger.critical(
                "SAFETY_ESCALATION | user_id=%s | kind=%s | intensity=%.2f",
                user_id,
                safety_kind,
                intensity,
            )

        return {
            "response": response,
            "messages": [
                {"role": "user", "content": state["user_message"]},
                {"role": "assistant", "content": response},
            ],
        }

    return safety_node


def _classify_safety_kind(message: str) -> str:
    if _MENTAL_HEALTH_SAFETY_PATTERNS.search(message):
        return "mental_health_crisis"
    if _PHYSICAL_SAFETY_PATTERNS.search(message):
        return "physical_emergency"
    return "physical_emergency"
