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
_EXTREME_DIET_SAFETY_PATTERNS = re.compile(
    r"굶는?\s*식단|굶어서|단식.*살|일주일.*[5-9]\s*kg|[5-9]\s*kg.*일주일|"
    r"극단적.*다이어트|초저칼로리"
)
_EXTREME_DIET_RESPONSE = (
    "식사를 거르거나 단기간에 큰 폭으로 감량하는 방식은 안전하지 않아서 도와드릴 수 없어요.\n\n"
    "극단적인 제한은 어지럼, 폭식 반동, 근손실, 컨디션 저하 위험을 키울 수 있습니다. "
    "감량은 식사를 유지하면서 작은 칼로리 조정과 활동량 조절로 가는 편이 안전합니다.\n\n"
    "최근 어지럼, 실신감, 폭식/절식 반복, 월경 이상, 복용약이나 질환이 있으면 전문가 상담을 우선하세요."
)

_ESCALATION_INTENSITY_THRESHOLD = 0.8


def make_safety_node(deps: NodeDeps):
    async def safety_node(state: GraphState) -> dict:
        emotion = state.get("emotion") or {}
        intensity = emotion.get("intensity", 0.0)
        user_id = state["user_id"]
        message = state["user_message"]
        safety_kind = _classify_safety_kind(message)
        response = _response_for_safety_kind(safety_kind)
        profile_note = _profile_safety_context(state.get("user_profile") or {})
        if profile_note:
            response = f"{response}\n\n{profile_note}"

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
        }

    return safety_node


def _classify_safety_kind(message: str) -> str:
    if _MENTAL_HEALTH_SAFETY_PATTERNS.search(message):
        return "mental_health_crisis"
    if _EXTREME_DIET_SAFETY_PATTERNS.search(message):
        return "extreme_diet"
    if _PHYSICAL_SAFETY_PATTERNS.search(message):
        return "physical_emergency"
    return "physical_emergency"


def _response_for_safety_kind(safety_kind: str) -> str:
    if safety_kind == "mental_health_crisis":
        return _MENTAL_HEALTH_RESPONSE
    if safety_kind == "extreme_diet":
        return _EXTREME_DIET_RESPONSE
    return _PHYSICAL_EMERGENCY_RESPONSE


def _profile_safety_context(profile: dict) -> str:
    constraints: list[str] = []
    for key in ("injury_history", "medical_conditions", "conditions", "pain_points", "allergies", "dietary_restrictions"):
        value = profile.get(key)
        if isinstance(value, list):
            constraints.extend(str(item).strip() for item in value if str(item).strip())
        elif value:
            constraints.append(str(value).strip())

    parts: list[str] = []
    if profile.get("age"):
        parts.append(f"나이 {profile['age']}세")
    if profile.get("exercise_level") or profile.get("activity_level"):
        parts.append(f"운동 수준 {profile.get('exercise_level') or profile.get('activity_level')}")
    if constraints:
        parts.append(f"제약({', '.join(constraints)})")
    if not parts:
        return ""
    return "프로필 기준으로도 " + ", ".join(parts) + "이 확인되므로 무리하지 말고 전문가 확인 전에는 강한 운동이나 극단적 식단을 피하세요."
