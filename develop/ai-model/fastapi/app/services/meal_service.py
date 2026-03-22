"""식단 분석 서비스 파이프라인.

POST /process-meal 요청을 받아:
  1. Pinecone에서 사용자 맥락 검색
  2. 맥락을 주입한 시스템 프롬프트 빌드
  3. Gemini로 식단 분석
  4. BackgroundTasks에 요약 저장 태스크 등록
  5. SuccessResponse 반환
"""

import json
import logging

from fastapi import BackgroundTasks, HTTPException, Request
from google.genai import errors as genai_errors

from app.prompts.meal import build_meal_system_prompt
from app.schemas.common import SuccessResponse
from app.schemas.meal import MealAnalysisData, ProcessMealRequest
from app.services.background_summary import run_background_summary

logger = logging.getLogger(__name__)


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


async def process_meal(
    body: ProcessMealRequest,
    request: Request,
    background_tasks: BackgroundTasks,
) -> SuccessResponse:
    """식단 분석 전체 파이프라인을 실행하고 SuccessResponse를 반환한다.

    파이프라인:
        1. app.state에서 클라이언트 인스턴스 획득
        2. Pinecone 맥락 검색 (_fetch_context — 실패 시 graceful degradation)
        3. 맥락 주입 시스템 프롬프트 빌드
        4. Gemini 식단 분석 호출
        5. BackgroundTasks에 run_background_summary 등록
        6. SuccessResponse 반환

    Args:
        body: POST /process-meal 요청 바디.
        request: FastAPI Request 객체 (app.state 접근에 사용).
        background_tasks: FastAPI BackgroundTasks 인스턴스.

    Returns:
        SuccessResponse(data={calories: float, message: str})

    Raises:
        HTTPException(500): Gemini API 호출이 ClientError로 실패한 경우.
    """
    gemini = request.app.state.gemini_client
    pinecone = request.app.state.pinecone_client
    embed = request.app.state.embed_client

    # 1. Pinecone 맥락 검색 (실패해도 진행)
    context_text = await _fetch_context(pinecone, embed, body.user_id, body.user_message)

    # 2. 시스템 프롬프트 빌드
    system_prompt = build_meal_system_prompt(body.user_profile, context_text)

    # 3. Gemini 호출
    try:
        raw_json = await gemini.generate(
            system_prompt=system_prompt,
            user_content=body.user_message,
            response_schema=MealAnalysisData,
        )
    except genai_errors.ClientError as exc:
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

    # 4. 응답 파싱
    parsed = json.loads(raw_json)
    data = MealAnalysisData(**parsed)

    # 5. Background Summary 등록
    background_tasks.add_task(
        run_background_summary,
        user_id=body.user_id,
        user_message=body.user_message,
        ai_response=data.message,
        gemini_client=gemini,
        embed_client=embed,
        pinecone_client=pinecone,
    )

    # 6. 응답 반환
    return SuccessResponse(data=data.model_dump())
