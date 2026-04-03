"""Fallback 노드 — Layer 3 Fallback 상세 구현.

이전 대화 맥락 존재 시: 맥락 기반 재추론 → 의도 분석 재실행
맥락 없음:             Clarification 요청 → 사용자 입력 대기

무한 루프 방지를 위해 fallback_count >= 2 이면 Clarification으로 강제 전환.
"""
from __future__ import annotations

import logging

from app.graph.deps import NodeDeps
from app.schemas.state import GraphState

logger = logging.getLogger(__name__)

MAX_FALLBACK = 2

_CLARIFICATION_RESPONSE = (
    "죄송해요, 질문을 정확히 이해하지 못했어요. "
    "조금 더 구체적으로 말씀해 주시겠어요? 예를 들어, "
    "운동 계획, 식단 기록, 건강 정보 등 어떤 도움이 필요하신지 알려주세요."
)


def make_fallback_node(deps: NodeDeps):
    async def fallback_node(state: GraphState) -> dict:
        count = state.get("fallback_count", 0)
        messages = state.get("messages", [])
        has_context = len(messages) >= 2 and count < MAX_FALLBACK

        if has_context:
            logger.info("Fallback 재추론 시도: fallback_count=%d", count)
            return {
                "fallback_count": count + 1,
                "needs_clarification": False,
            }
        else:
            logger.info("Fallback Clarification 요청: fallback_count=%d", count)
            return {
                "response": _CLARIFICATION_RESPONSE,
                "fallback_count": count + 1,
                "needs_clarification": True,
                "messages": {"role": "assistant", "content": _CLARIFICATION_RESPONSE},
            }

    return fallback_node
