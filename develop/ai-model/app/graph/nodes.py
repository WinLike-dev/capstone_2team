"""
헬스 메이트 - LangGraph 노드(Node) 구현

[포함 노드]
  1. super_agent_node     : 의도 파악 (Structured Output)
  2. exercise_expert_node : 운동 전문가 조언 생성
  3. diet_expert_node     : 식단 전문가 조언 생성
  4. plan_draft_node      : 플랜 초안 생성
  5. evaluator_node       : 환각/위험 가이드 자체 검증
  6. reask_node           : 재질문 안내 메시지 생성

[제외 노드 - 추후 구현 예정]
  검색 라우터 / 탐색 횟수 초과 / Web Search / RAG Search / 문서 평가
  → 전문가 노드에서 플랜 초안 생성 노드로 Edge 직접 연결
"""
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

from app.graph.state import HealthMateState

# ── LLM 인스턴스 (노드 역할에 따라 모델 분리) ──────────────────────────────────
# 전문가 노드 + 플랜 초안: 무료 티어 지원 모델 (gemini-2.5-flash)
_llm_expert = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

# 의도 파악 / 평가 / 재질문: 무료 티어 경량 모델 (gemini-2.5-flash-lite)
_llm_router = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.3)


def _extract_text(content) -> str:
    """
    LangChain AIMessage.content 정규화 헬퍼.
    gemini-3 계열은 content를 list[dict] 형태로 반환하므로
    'text' 블록만 추출하여 문자열로 합친다.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return str(content)


# ── Pydantic 스키마 정의 ──────────────────────────────────────────────────────

class IntentOutput(BaseModel):
    """Super Agent의 구조화 출력 스키마."""

    intent: str = Field(
        description="사용자 입력의 주요 도메인. 반드시 '운동' 또는 '식단' 중 하나."
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="의도 판단 확신도. 0.0(불확실) ~ 1.0(매우 확실).",
    )


class EvaluationOutput(BaseModel):
    """평가 노드의 구조화 출력 스키마."""

    is_safe: bool = Field(
        description=(
            "플랜이 안전하고 사실에 기반하면 True(PASS), "
            "환각이나 위험한 내용이 있으면 False(FAIL)."
        )
    )
    reason: str = Field(description="판단 근거 한 문장 요약.")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Super Agent — 의도 파악 및 라우팅 준비
# ─────────────────────────────────────────────────────────────────────────────
def super_agent_node(state: HealthMateState) -> dict:
    """
    사용자 입력을 분석해 도메인 의도(운동/식단)와 확신도를 반환한다.
    with_structured_output으로 Pydantic 모델에 자동 파싱한다.
    """
    structured_llm = _llm_router.with_structured_output(IntentOutput)

    prompt = (
        "당신은 AI 헬스케어 서비스 '헬스 메이트'의 의도 분석 에이전트입니다.\n"
        "사용자의 입력이 '운동'에 관한 것인지 '식단'에 관한 것인지 판단하세요.\n"
        "두 주제가 혼재하거나 불명확한 경우 더 가까운 도메인을 선택하되 "
        "confidence를 낮게 설정하세요.\n\n"
        f"[사용자 입력]\n{state['user_input']}\n\n"
        "intent와 confidence를 반환하세요."
    )

    result: IntentOutput = structured_llm.invoke(prompt)
    return {"intent": result.intent, "confidence": result.confidence}


# ─────────────────────────────────────────────────────────────────────────────
# 2. Exercise Expert — 운동 전문가
# ─────────────────────────────────────────────────────────────────────────────
def exercise_expert_node(state: HealthMateState) -> dict:
    """
    헬스 트레이너 페르소나로 운동 관련 전문 조언을 생성한다.
    현재 버전: 외부 검색 없이 자체 지식 기반으로만 답변.
    """
    prompt = (
        "당신은 국가공인 퍼스널 트레이너(CPT) 자격을 보유한 10년 경력의 헬스 트레이너입니다.\n"
        "과학적 근거에 기반한 안전하고 효과적인 운동 조언을 제공합니다.\n"
        "부상 위험이 있는 과도한 훈련이나 검증되지 않은 방법은 절대 권장하지 않습니다.\n"
        "반드시 운동에 관한 내용만 답변하고, 식단·영양 조언은 절대 포함하지 마세요.\n\n"
        f"[사용자 질문]\n{state['user_input']}\n\n"
        "위 질문에 대해 운동 관련 조언만 전문적이고 구체적으로 제공해주세요."
    )

    response = _llm_expert.invoke(prompt)
    return {"expert_advice": _extract_text(response.content)}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Diet Expert — 식단 전문가
# ─────────────────────────────────────────────────────────────────────────────
def diet_expert_node(state: HealthMateState) -> dict:
    """
    공인 영양사 페르소나로 식단 관련 전문 조언을 생성한다.
    현재 버전: 외부 검색 없이 자체 지식 기반으로만 답변.
    """
    prompt = (
        "당신은 임상 영양학 석사 학위를 보유한 공인 영양사(Registered Dietitian)입니다.\n"
        "균형 잡힌 영양 섭취와 개인 건강 목표에 맞는 식단을 과학적으로 조언합니다.\n"
        "극단적인 다이어트, 검증되지 않은 보충제, 의학적 처방에 해당하는 내용은 권장하지 않습니다.\n"
        "반드시 식단·영양에 관한 내용만 답변하고, 운동 조언은 절대 포함하지 마세요.\n\n"
        f"[사용자 질문]\n{state['user_input']}\n\n"
        "위 질문에 대해 식단 관련 조언만 전문적이고 구체적으로 제공해주세요."
    )

    response = _llm_expert.invoke(prompt)
    return {"expert_advice": _extract_text(response.content)}


# ─────────────────────────────────────────────────────────────────────────────
# 4. Plan Draft Node — 플랜 초안 생성
# ─────────────────────────────────────────────────────────────────────────────
def plan_draft_node(state: HealthMateState) -> dict:
    """
    전문가 조언을 바탕으로 사용자가 실행할 수 있는 플랜 초안을 작성한다.
    (검색 노드 미구현으로 expert_advice만 활용)
    """
    domain = state.get("intent", "운동/식단")
    exclude = "식단·영양" if domain == "운동" else "운동"

    prompt = (
        "당신은 AI 헬스케어 서비스 '헬스 메이트'의 플랜 작성 전문가입니다.\n"
        "아래 전문가 조언을 바탕으로 사용자가 바로 실행할 수 있는 "
        "구체적이고 친절한 맞춤형 플랜을 작성하세요.\n\n"
        "[작성 규칙]\n"
        f"- 반드시 '{domain}' 관련 내용만 다룰 것. '{exclude}' 조언은 절대 포함하지 말 것\n"
        "- 단계별 행동 계획을 명확하게 제시할 것\n"
        "- 전문 용어는 쉬운 말로 풀어서 설명할 것\n"
        "- 각 단계에 예상 효과나 주의사항을 간략히 포함할 것\n"
        "- 사용자의 안전을 최우선으로 할 것\n\n"
        f"[사용자 원문 입력]\n{state['user_input']}\n\n"
        f"[전문가 조언]\n{state['expert_advice']}\n\n"
        "위 내용을 종합하여 최종 플랜 초안을 작성해주세요."
    )

    response = _llm_expert.invoke(prompt)
    return {"draft_plan": _extract_text(response.content)}


# ─────────────────────────────────────────────────────────────────────────────
# 5. Evaluator Node — 최종 답변 평가
# ─────────────────────────────────────────────────────────────────────────────
def evaluator_node(state: HealthMateState) -> dict:
    """
    플랜 초안에 환각(Hallucination)이나 위험한 가이드가 없는지 자체 검증한다.
    PASS(is_safe=True): final_plan에 초안을 그대로 저장.
    FAIL(is_safe=False): final_plan=None, 이후 reask_node로 라우팅.
    """
    structured_llm = _llm_router.with_structured_output(EvaluationOutput)

    prompt = (
        "당신은 AI 헬스케어 서비스의 안전성 검토 전문가입니다.\n"
        "아래 플랜 초안을 검토하여 다음 기준으로 PASS/FAIL을 판정하세요.\n\n"
        "[FAIL 판정 기준 — 하나라도 해당하면 False]\n"
        "1. 사실과 다른 정보(환각)가 포함된 경우\n"
        "2. 부상·건강 악화 위험이 있는 극단적 운동 또는 식단 권장\n"
        "3. 의학적 진단·처방에 해당하는 내용 포함\n"
        "4. 검증되지 않은 보충제·약물 복용 권장\n"
        "5. 특정 연령·질환을 고려하지 않은 위험한 조언\n\n"
        f"[검토할 플랜 초안]\n{state['draft_plan']}\n\n"
        "is_safe(True/False)와 판단 reason을 반환하세요."
    )

    result: EvaluationOutput = structured_llm.invoke(prompt)

    # PASS 시 초안을 최종 플랜으로 확정, FAIL 시 None
    final_plan = state["draft_plan"] if result.is_safe else None
    return {"is_safe": result.is_safe, "final_plan": final_plan}


# ─────────────────────────────────────────────────────────────────────────────
# 6. Reask Node — 재질문 요청
# ─────────────────────────────────────────────────────────────────────────────
def reask_node(state: HealthMateState) -> dict:
    """
    확신도 부족(confidence < 0.7) 또는 평가 FAIL(is_safe=False) 시
    사용자에게 재입력을 유도하는 친절한 안내 메시지를 생성한다.
    """
    confidence = state.get("confidence") or 0.0
    is_safe = state.get("is_safe")

    # 재질문 원인에 따라 컨텍스트를 다르게 구성
    if confidence < 0.7:
        reason_context = (
            f"사용자의 입력 '{state['user_input']}'에서 "
            f"운동인지 식단인지 명확히 파악하기 어려웠습니다 (확신도: {confidence:.0%})."
        )
    else:
        reason_context = (
            f"생성된 플랜이 안전성 검토를 통과하지 못했습니다 (is_safe={is_safe}). "
            f"사용자 입력: '{state['user_input']}'"
        )

    prompt = (
        "당신은 AI 헬스케어 서비스 '헬스 메이트'의 친절한 상담 어시스턴트입니다.\n"
        "아래 상황을 고려하여, 사용자가 더 명확한 정보를 제공할 수 있도록 "
        "구체적인 재질문 안내 메시지를 작성하세요.\n\n"
        f"[상황]\n{reason_context}\n\n"
        "[작성 규칙]\n"
        "- 2~3문장으로 간결하게 작성\n"
        "- 사용자가 추가로 제공해야 할 정보를 구체적으로 명시\n"
        "- 친절하고 부드러운 어조 유지\n"
    )

    response = _llm_router.invoke(prompt)
    return {"error_message": response.content, "final_plan": None}
