"""Chat Pipeline 오케스트레이터 서비스.

POST /ai-chat 요청을 받아:
  1. app.state에서 클라이언트 인스턴스 획득
  2. Router AI 의도분류 + Vector DB 맥락검색 병렬 실행 (asyncio.gather)
  3. db_modified_flag 모드별 결정
  4. Worker AI 시스템 프롬프트 빌드
  5. WAS 조건부 호출 (mode 3, 5)
  6. Gemini 워커 AI 호출
  7. AiChatResponse 반환
  8. Background Summary 비동기 등록
"""

import asyncio
import json
import logging

from fastapi import BackgroundTasks, HTTPException, Request
from google.genai import errors as genai_errors

from app.prompts.worker import build_worker_system_prompt
from app.schemas.chat import (
    AiChatData,
    AiChatRequest,
    AiChatResponse,
    get_db_modified_flag,
)
from app.schemas.gemini_outputs import (
    ExercisePlanOutput,
    MealLogOutput,
    MealPlanOutput,
    RecommendationOutput,
    SimpleAnswerOutput,
    UserDbUpdateOutput,
)
from app.services.background_summary import run_background_summary

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 모드 이름 맵 (로그용)
# ---------------------------------------------------------------------------

_MODE_NAME: dict[int, str] = {
    1: "단순대화",
    2: "운동플랜 작성",
    3: "운동플랜 수정",
    4: "식단플랜 작성",
    5: "식단플랜 수정",
    6: "DB 수정 (프로필)",
    7: "식단 기록 분석",
    8: "운동/식단 추천",
}


def _mode_label(mode: int) -> str:
    return f"mode={mode}({_MODE_NAME.get(mode, '알수없음')})"


# ---------------------------------------------------------------------------
# 모드별 Gemini 응답 스키마 맵
# ---------------------------------------------------------------------------

_MODE_SCHEMA_MAP: dict[int, type] = {
    1: SimpleAnswerOutput,
    2: ExercisePlanOutput,
    3: ExercisePlanOutput,
    4: MealPlanOutput,
    5: MealPlanOutput,
    6: UserDbUpdateOutput,
    7: MealLogOutput,
    8: RecommendationOutput,
}


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------


async def _fetch_context(
    pinecone_client,
    embed_client,
    user_id: str,
    query: str,
) -> str:
    """Pinecone에서 사용자 맥락을 검색하여 포매팅된 문자열을 반환한다.

    검색 실패 또는 결과 없음 시 '이전 맥락: 없음'을 반환한다.

    Args:
        pinecone_client: Pinecone 클라이언트 인스턴스.
        embed_client: 임베딩 클라이언트 인스턴스.
        user_id: 사용자 식별자 (Pinecone namespace).
        query: 검색에 사용할 쿼리 텍스트.

    Returns:
        포매팅된 맥락 텍스트 문자열.
    """
    try:
        vector: list[float] = await embed_client.embed(query)
        results: list[dict] = await pinecone_client.search(user_id, vector, top_k=3)

        if not results:
            return "이전 맥락: 없음"

        lines = [f"{i + 1}. {r['summary']}" for i, r in enumerate(results)]
        return "이전 맥락:\n" + "\n".join(lines)

    except Exception:
        logger.warning(
            "Pinecone 맥락 검색 실패 — 맥락 없이 진행 (user_id=%s)", user_id
        )
        return "이전 맥락: 없음"


def _get_worker_response_schema(mode: int) -> type:
    """모드별 Gemini 응답 스키마를 반환한다.

    Args:
        mode: 라우터 AI가 분류한 모드 번호 (1-8).

    Returns:
        Pydantic BaseModel 서브클래스.
    """
    return _MODE_SCHEMA_MAP.get(mode, SimpleAnswerOutput)


def _build_ai_chat_data(mode: int, parsed: dict) -> AiChatData:
    """모드별 Gemini 응답 파싱 결과를 AiChatData로 구성한다.

    Args:
        mode: 라우터 AI가 분류한 모드 번호 (1-8).
        parsed: Gemini JSON 응답을 dict로 파싱한 값.

    Returns:
        AiChatData 인스턴스.
    """
    if mode == 1:
        return AiChatData(
            message=parsed.get("answer", ""),
            detail=None,
        )

    if mode == 2:
        return AiChatData(
            message="운동 계획이 생성되었습니다.",
            detail=parsed.get("items"),
        )

    if mode == 3:
        return AiChatData(
            message="운동 계획이 수정되었습니다.",
            detail=parsed.get("items"),
        )

    if mode == 4:
        return AiChatData(
            message="식단 계획이 생성되었습니다.",
            detail=parsed.get("items"),
        )

    if mode == 5:
        return AiChatData(
            message="식단 계획이 수정되었습니다.",
            detail=parsed.get("items"),
        )

    if mode == 6:
        return AiChatData(
            message="프로필이 업데이트되었습니다.",
            detail=parsed.get("updated_fields"),
        )

    if mode == 7:
        return AiChatData(
            message=parsed.get("message", ""),
            detail={
                "calories": parsed.get("calories"),
                "carbs": parsed.get("carbs"),
                "protein": parsed.get("protein"),
                "fat": parsed.get("fat"),
            },
        )

    if mode == 8:
        return AiChatData(
            message="추천 운동과 식단입니다.",
            detail=parsed,
        )

    # 알 수 없는 모드 — fallback
    return AiChatData(
        message=parsed.get("answer", str(parsed)),
        detail=None,
    )


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------


async def handle_ai_chat(
    body: AiChatRequest,
    request: Request,
    background_tasks: BackgroundTasks,
) -> AiChatResponse:
    """Chat pipeline 전체 흐름을 실행하고 AiChatResponse를 반환한다.

    파이프라인:
        1. app.state에서 클라이언트 인스턴스 획득
        2. Router AI + Vector DB 맥락검색 병렬 실행 (asyncio.gather)
        3. db_modified_flag 모드별 결정 (CHAT-11)
        4. Worker AI 시스템 프롬프트 빌드 (CHAT-12)
        5. WAS 조건부 호출 (mode 3: fetch_exercise_list, mode 5: fetch_meal_list)
        6. Gemini 워커 AI 호출
        7. AiChatResponse 반환
        8. Background Summary 비동기 등록 (CHAT-13)

    Args:
        body: POST /ai-chat 요청 바디.
        request: FastAPI Request 객체 (app.state 접근에 사용).
        background_tasks: FastAPI BackgroundTasks 인스턴스.

    Returns:
        AiChatResponse with mode, data, db_modified_flag.

    Raises:
        HTTPException(500): Gemini API 호출이 ClientError로 실패한 경우.
    """
    logger.info("[ai-chat] 요청 수신 user_id=%s message='%s'", body.user_id, body.user_message[:80])

    # 1. 클라이언트 획득
    router = request.app.state.router_client
    gemini = request.app.state.gemini_client
    pinecone = request.app.state.pinecone_client
    embed = request.app.state.embed_client
    was = request.app.state.was_client

    # 2. Router AI + Vector DB 병렬 실행 (CHAT-02)
    logger.info("[ai-chat] Router AI 분류 + Pinecone 맥락 검색 시작")
    try:
        router_output, context_text = await asyncio.gather(
            router.classify(body.user_message),
            _fetch_context(pinecone, embed, body.user_id, body.user_message),
        )
    except Exception:
        logger.warning("[ai-chat] Router AI 분류 실패 — mode=1(단순대화) fallback 적용")
        from app.clients.router import RouterOutput
        router_output = RouterOutput(mode=1, reason="분류 실패 - 기본 모드")
        context_text = "이전 맥락: 없음"

    mode: int = router_output.mode
    logger.info("[ai-chat] Router AI 분류 완료 → %s, reason='%s'", _mode_label(mode), router_output.reason)
    logger.info("[ai-chat] Pinecone 맥락 검색 완료 → %s", context_text[:100])

    # 3. db_modified_flag 결정 (CHAT-11)
    db_flag = get_db_modified_flag(mode)
    logger.info("[ai-chat] db_modified_flag=%s", db_flag)

    # 4. Worker 시스템 프롬프트 빌드 (CHAT-12)
    system_prompt = build_worker_system_prompt(
        mode=mode,
        user_profile=body.user_profile,
        context_text=context_text,
        user_instruction=body.user_instruction,
    )
    logger.info("[ai-chat] Worker 시스템 프롬프트 빌드 완료 (%d자)", len(system_prompt))

    # 5. WAS 조건부 호출 (Phase 6에서 모드별 핸들러로 이전)
    user_content = body.user_message
    if mode == 3:
        logger.info("[ai-chat] WAS fetch_exercise_list 호출 (user_id=%s)", body.user_id)
        try:
            exercise_list = await was.fetch_exercise_list(body.user_id)
            logger.info("[ai-chat] WAS 운동 계획 수신 완료 (%d건)", len(exercise_list))
            user_content = (
                f"{body.user_message}\n\n현재 운동 계획:\n{json.dumps(exercise_list, ensure_ascii=False)}"
            )
        except Exception:
            logger.warning("[ai-chat] WAS fetch_exercise_list 실패 (user_id=%s) — 기존 데이터 없이 진행", body.user_id)
    elif mode == 5:
        logger.info("[ai-chat] WAS fetch_meal_list 호출 (user_id=%s)", body.user_id)
        try:
            meal_list = await was.fetch_meal_list(body.user_id)
            logger.info("[ai-chat] WAS 식단 계획 수신 완료 (%d건)", len(meal_list))
            user_content = (
                f"{body.user_message}\n\n현재 식단 계획:\n{json.dumps(meal_list, ensure_ascii=False)}"
            )
        except Exception:
            logger.warning("[ai-chat] WAS fetch_meal_list 실패 (user_id=%s) — 기존 데이터 없이 진행", body.user_id)
    else:
        logger.info("[ai-chat] %s → WAS 호출 불필요 (모드 3,5만 해당)", _mode_label(mode))

    # 6. Gemini 워커 호출
    response_schema = _get_worker_response_schema(mode)
    logger.info("[ai-chat] Gemini 워커 호출 시작 (%s)", _mode_label(mode))
    try:
        raw_json = await gemini.generate(
            system_prompt=system_prompt,
            user_content=user_content,
            response_schema=response_schema,
        )
    except genai_errors.ClientError as exc:
        logger.error("[ai-chat] Gemini 워커 호출 실패: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error": {
                    "code": "GEMINI_ERROR",
                    "message": str(exc),
                },
            },
        ) from exc
    logger.info("[ai-chat] Gemini 워커 응답 수신 완료 (%d자)", len(raw_json))

    # 7. 응답 구성 — 모드별 파싱
    parsed = json.loads(raw_json)
    chat_data = _build_ai_chat_data(mode, parsed)

    response = AiChatResponse(
        mode=mode,
        data=chat_data,
        db_modified_flag=db_flag,
    )
    logger.info("[ai-chat] 응답 반환 %s db_modified_flag=%s", _mode_label(mode), db_flag)

    # 8. Background Summary 등록 (CHAT-13)
    background_tasks.add_task(
        run_background_summary,
        user_id=body.user_id,
        user_message=body.user_message,
        ai_response=chat_data.message,
        gemini_client=gemini,
        embed_client=embed,
        pinecone_client=pinecone,
    )
    logger.info("[ai-chat] Background Summary 태스크 등록 완료")

    return response
