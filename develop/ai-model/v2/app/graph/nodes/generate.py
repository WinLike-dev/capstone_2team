"""응답 생성 노드 — Layer 3 응답 생성 + 자기 평가 상세 구현.

Flash + Persona DB로 응답 생성:
  - State.emotion → 톤 조절
  - State.profile_changes → 변경 확인 문구
  - State.today_plan → 기록 검증
  - modify_plan_context → 수정 반영
  - State.search_quality → degraded 안내
  - 출처 태그 → 기억·정보 구분

자기 평가 (안전경고 · 공감_케어만 실행):
  - 통과: 최종 출력
  - 실패: max=2 재생성 → 초과 시 부분 패치
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.graph.deps import NodeDeps
from app.schemas.state import GraphState

logger = logging.getLogger(__name__)

MAX_SELF_EVAL = 2

_SELF_EVAL_INTENTS = {"안전경고", "공감_케어"}

_GENERATION_SYSTEM_PROMPT = """
당신은 친절하고 전문적인 헬스 AI 코치입니다.
사용자의 운동·식단·건강 목표를 돕는 개인 AI입니다.

응답 원칙:
- 감정(emotion) 기반 톤 조절: 슬픔/불안 → 따뜻하고 공감적, 기쁨 → 밝고 격려적
- 검색 결과가 있으면 출처를 [기억] 또는 [정보]로 표시
- search_quality가 degraded이면 "정확한 정보를 찾기 어려워 일반적인 내용으로 답변"을 언급
- profile_changes가 있으면 변경 사항을 확인하는 문구 포함
- 수정 플랜이 있으면 구체적인 변경 내용을 반영
- 응답은 한국어로, 자연스럽고 친근하게
"""

_SELF_EVAL_PROMPT = """
아래 응답을 평가하세요:
1. 톤이 감정 상태에 적합한가?
2. 할루시네이션(없는 정보 지어내기)이 없는가?
3. 안전 제약사항을 위반하지 않는가?

JSON: {"pass": true/false, "reason": "이유 (실패 시)"}
"""


def make_generate_node(deps: NodeDeps):
    async def generate_node(state: GraphState) -> dict:
        # 이미 응답이 세팅된 경우 (record 에러, safety 등)
        if state.get("response"):
            response = state["response"]
            return {
                "messages": [
                    {"role": "user", "content": state["user_message"]},
                    {"role": "assistant", "content": response},
                ]
            }

        context = _build_generation_context(state)
        intent = state.get("intent", "")
        eval_count = state.get("self_eval_count", 0)
        failure_reason = state.get("self_eval_failure_reason")

        system_prompt = _build_system_prompt(state, failure_reason)

        try:
            response = await deps.gemini.generate_text(
                system_prompt=system_prompt,
                user_content=context,
            )
        except Exception as e:
            logger.error("응답 생성 실패: %s", e)
            response = "죄송해요, 잠시 오류가 발생했어요. 다시 말씀해 주시겠어요?"

        # ── 자기 평가 (안전경고 · 공감_케어만) ─────────────────────────────
        if intent in _SELF_EVAL_INTENTS:
            passed, reason = await _self_evaluate(deps, state, response)
            if not passed:
                if eval_count < MAX_SELF_EVAL:
                    logger.info("자기 평가 실패, 재생성: count=%d, reason=%s", eval_count, reason)
                    return {
                        "self_eval_count": eval_count + 1,
                        "self_eval_failure_reason": reason,
                    }
                else:
                    # 부분 패치
                    logger.warning("자기 평가 최대 재시도 초과, 부분 패치 적용")
                    response = _partial_patch(response, reason)

        return {
            "response": response,
            "self_eval_count": 0,
            "self_eval_failure_reason": None,
            "messages": [
                {"role": "user", "content": state["user_message"]},
                {"role": "assistant", "content": response},
            ],
        }

    return generate_node


def _build_generation_context(state: GraphState) -> str:
    parts: list[str] = []

    # 이전 대화 맥락
    messages = state.get("messages", [])
    if messages:
        history = "\n".join(
            f"{m['role']}: {m['content']}" for m in messages[-6:]
        )
        parts.append(f"[대화 맥락]\n{history}")

    # 현재 메시지
    parts.append(f"\n[현재 질문]\n{state['user_message']}")

    # 검색 결과
    results = state.get("search_results") or []
    if results:
        snippets = "\n".join(
            f"[{r['source']}] {r['text'][:300]}" for r in results[:5]
        )
        parts.append(f"\n[참고 정보]\n{snippets}")

    # 수정 플랜 컨텍스트
    modify_ctx = state.get("modify_plan_context")
    if modify_ctx:
        parts.append(f"\n[현재 전체 플랜]\n{json.dumps(modify_ctx, ensure_ascii=False)[:500]}")

    # 프로필 변경사항
    changes = state.get("profile_changes")
    if changes:
        parts.append(f"\n[프로필 변경 사항]\n{json.dumps(changes, ensure_ascii=False)}")

    return "\n".join(parts)


def _build_system_prompt(state: GraphState, failure_reason: str | None) -> str:
    prompt = _GENERATION_SYSTEM_PROMPT
    emotion = state.get("emotion") or {}
    label = emotion.get("label", "중립")
    intensity = emotion.get("intensity", 0.0)
    prompt += f"\n\n현재 사용자 감정: {label} (강도 {intensity:.1f})"

    if state.get("search_quality") == "degraded":
        prompt += "\n\n주의: 검색 결과가 충분하지 않으므로 일반적인 내용으로 답변하고 이를 안내하세요."

    if failure_reason:
        prompt += f"\n\n이전 응답 실패 이유: {failure_reason}\n이를 개선하여 다시 작성하세요."

    return prompt


async def _self_evaluate(deps: NodeDeps, state: GraphState, response: str) -> tuple[bool, str]:
    emotion = state.get("emotion") or {}
    user_content = (
        f"감정 상태: {emotion.get('label', '중립')} (강도 {emotion.get('intensity', 0):.1f})\n"
        f"사용자 메시지: {state['user_message']}\n"
        f"생성된 응답:\n{response}"
    )
    try:
        raw = await deps.router.generate(
            system_prompt=_SELF_EVAL_PROMPT,
            user_content=user_content,
            response_schema=dict,
        )
        result = json.loads(raw)
        passed = bool(result.get("pass", True))
        reason = result.get("reason", "")
        return passed, reason
    except Exception as e:
        logger.warning("자기 평가 API 실패, 통과 처리: %s", e)
        return True, ""


def _partial_patch(response: str, reason: str) -> str:
    """최대 재시도 초과 시 간단한 안전 문구 추가."""
    safe_suffix = "\n\n(더 정확한 도움이 필요하시면 전문가 상담을 권장드립니다.)"
    if safe_suffix not in response:
        return response + safe_suffix
    return response
