import logging
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

from config import get_settings
from chains.prompt_templates import build_intent_classifier_prompt, build_main_prompt
from utils.output_parser import parse_intent, wrap_plain_text_response, FALLBACK_RESPONSE
from models.request_models import GenerateRequest

logger = logging.getLogger(__name__)


def _build_llm() -> ChatGoogleGenerativeAI:
    """공유 Gemini LLM 인스턴스를 생성합니다."""
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        temperature=settings.gemini_temperature,
        google_api_key=settings.google_api_key,
    )


def _format_chat_history(request: GenerateRequest) -> list:
    """GenerateRequest의 chat_history를 LangChain 메시지 객체 리스트로 변환합니다."""
    messages = []
    for msg in request.chat_history:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            messages.append(AIMessage(content=msg.content))
    return messages


def _build_user_context_vars(request: GenerateRequest) -> dict[str, str]:
    """UserContext를 프롬프트 템플릿 변수 딕셔너리로 변환합니다."""
    ctx = request.user_context
    return {
        "age": str(ctx.age) if ctx.age is not None else "정보 없음",
        "gender": ctx.gender or "정보 없음",
        "height": str(ctx.height) if ctx.height is not None else "정보 없음",
        "weight": str(ctx.weight) if ctx.weight is not None else "정보 없음",
        "mbti": ctx.mbti or "정보 없음",
    }



async def _classify_intent(llm: ChatGoogleGenerativeAI, message: str) -> int:
    """
    [1단계] 인텐트 분류기
    사용자 발화를 분석하여 1~4 중 하나의 인텐트 번호를 반환합니다.
    """
    classifier_prompt = build_intent_classifier_prompt()
    chain = classifier_prompt | llm
    result = await chain.ainvoke({"current_message": message})
    raw_intent = result.content
    logger.info("인텐트 분류 결과: raw=%r", raw_intent)
    return parse_intent(raw_intent)


async def _generate_main_response(
    llm: ChatGoogleGenerativeAI,
    intent: int,
    request: GenerateRequest,
    user_vars: dict[str, str],
) -> str:
    """
    [2단계] 메인 AI 응답 생성기
    분류된 인텐트에 맞는 프롬프트로 Gemini를 호출하고 평문 답변을 반환합니다.
    """
    main_prompt = build_main_prompt(intent)
    chain = main_prompt | llm

    chain_input = {
        **user_vars,
        "chat_history": _format_chat_history(request),
        "current_message": request.current_message,
    }

    ai_message = await chain.ainvoke(chain_input)
    return ai_message.content


async def run_health_chain(request: GenerateRequest) -> dict[str, Any]:
    """
    AI 라우터 2단계 파이프라인을 실행하고 GenerateResponse 형태의 딕셔너리를 반환합니다.

    [흐름]
        사용자 입력
            │
            ▼
        [1단계] 인텐트 분류기 → 발화를 1~4 카테고리로 분류
            │
            ▼
        [2단계] 메인 AI 응답 생성 → 인텐트별 특화 프롬프트 + 사용자 DB 기반 평문 답변
            │
            ▼
        응답 래핑 → GenerateResponse { action_type, text_response, ui_components }

    Args:
        request: GenerateRequest (사용자 ID, 컨텍스트, 대화 이력, 현재 발화)

    Returns:
        GenerateResponse 형태의 딕셔너리
    """
    try:
        llm = _build_llm()
        user_vars = _build_user_context_vars(request)

        # 1단계: 인텐트 분류
        logger.info("1단계 인텐트 분류 시작. user_id=%s", request.user_id)
        intent = await _classify_intent(llm, request.current_message)
        logger.info("인텐트 분류 완료. user_id=%s, intent=%d", request.user_id, intent)

        # 2단계: 메인 AI 응답 생성
        logger.info("2단계 메인 AI 호출 시작. user_id=%s, intent=%d", request.user_id, intent)
        plain_text = await _generate_main_response(llm, intent, request, user_vars)
        logger.info("메인 AI 응답 수신 완료. user_id=%s", request.user_id)

        # 응답 래핑
        return wrap_plain_text_response(plain_text, intent)

    except Exception:
        logger.exception("헬스 체인 실행 중 예외 발생. user_id=%s", request.user_id)
        return FALLBACK_RESPONSE
