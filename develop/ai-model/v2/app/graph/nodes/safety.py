"""안전 경고 노드 — Layer 3 안전 경고 상세 구현.

1. 즉시 차단 + 로그 기록
2. 에스컬레이션 여부 판단 (intensity >= 0.8)
3. 안전 가이드 응답 반환
"""
from __future__ import annotations

import logging
from datetime import datetime

from app.graph.deps import NodeDeps
from app.schemas.state import GraphState

logger = logging.getLogger(__name__)

_SAFETY_RESPONSE = (
    "지금 많이 힘드신 것 같아요. 혼자 감당하기 어려운 상황이라면 "
    "전문가의 도움을 받으시길 권합니다.\n\n"
    "📞 자살예방상담전화: 1393 (24시간)\n"
    "📞 정신건강위기상담전화: 1577-0199\n\n"
    "언제든 이야기 나눠주세요. 제가 여기 있을게요."
)

_ESCALATION_INTENSITY_THRESHOLD = 0.8


def make_safety_node(deps: NodeDeps):
    async def safety_node(state: GraphState) -> dict:
        emotion = state.get("emotion") or {}
        intensity = emotion.get("intensity", 0.0)
        user_id = state["user_id"]
        message = state["user_message"]

        # 즉시 차단 + 로그
        logger.warning(
            "SAFETY_BLOCK | user_id=%s | message=%r | emotion_intensity=%.2f | timestamp=%s",
            user_id,
            message[:100],
            intensity,
            datetime.utcnow().isoformat(),
        )

        # 에스컬레이션 (향후 외부 알림 연동 가능)
        if intensity >= _ESCALATION_INTENSITY_THRESHOLD:
            logger.critical(
                "SAFETY_ESCALATION | user_id=%s | intensity=%.2f",
                user_id,
                intensity,
            )

        return {
            "response": _SAFETY_RESPONSE,
            "messages": {"role": "assistant", "content": _SAFETY_RESPONSE},
        }

    return safety_node
