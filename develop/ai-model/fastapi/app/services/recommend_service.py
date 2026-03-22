"""Recommend 서비스 파이프라인.

POST /recommend 요청에 대해:
1. Pinecone에서 이전 맥락 검색 (실패 시 graceful degradation)
2. Gemini로 운동/식단 추천 생성
3. BackgroundTasks에 Background Summary 등록
4. SuccessResponse 반환
"""

import json
import logging

from fastapi import BackgroundTasks, HTTPException, Request
from google.genai import errors as genai_errors

from app.prompts.recommend import build_recommend_system_prompt
from app.schemas.common import SuccessResponse
from app.schemas.recommend import RecommendRequest, RecommendationData
from app.services.background_summary import run_background_summary

logger = logging.getLogger(__name__)


async def _fetch_context(pinecone_client, embed_client, user_id: str, query: str) -> str:
    """Pinecone에서 이전 맥락을 검색하여 context_text를 반환한다.

    Args:
        pinecone_client: Pinecone 클라이언트 인스턴스.
        embed_client: 임베딩 클라이언트 인스턴스.
        user_id: 사용자 식별자.
        query: 검색 쿼리 텍스트 (user_instruction).

    Returns:
        "이전 맥락:\\n1. ..." 형식의 문자열.
        검색 결과가 없거나 실패 시 "이전 맥락: 없음".
    """
    try:
        vector: list[float] = await embed_client.embed(query)
        results: list[dict] = await pinecone_client.search(
            user_id=user_id, vector=vector, top_k=3
        )
        if not results:
            return "이전 맥락: 없음"
        lines = "\n".join(
            f"{i + 1}. {item['summary']}" for i, item in enumerate(results)
        )
        return f"이전 맥락:\n{lines}"
    except Exception:
        logger.warning("Pinecone 맥락 검색 실패 (user_id=%s) — 맥락 없이 진행", user_id)
        return "이전 맥락: 없음"


async def recommend(
    body: RecommendRequest,
    request: Request,
    background_tasks: BackgroundTasks,
) -> SuccessResponse:
    """운동/식단 추천 파이프라인 오케스트레이터.

    Args:
        body: POST /recommend 요청 본문.
        request: FastAPI Request (app.state에서 클라이언트 인스턴스 접근).
        background_tasks: FastAPI BackgroundTasks.

    Returns:
        SuccessResponse(data={recommended_exercise: {...}, recommended_meal: {...}})

    Raises:
        HTTPException(500): Gemini API 호출 실패 시.
    """
    gemini_client = request.app.state.gemini_client
    embed_client = request.app.state.embed_client
    pinecone_client = request.app.state.pinecone_client

    # 1. Pinecone 맥락 검색 (graceful degradation)
    context_text = await _fetch_context(
        pinecone_client=pinecone_client,
        embed_client=embed_client,
        user_id=body.user_id,
        query=body.user_instruction,
    )

    # 2. 시스템 프롬프트 빌드
    system_prompt = build_recommend_system_prompt(
        user_profile=body.user_profile,
        context_text=context_text,
    )

    # 3. Gemini로 추천 생성
    try:
        raw_json = await gemini_client.generate(
            system_prompt=system_prompt,
            user_content=body.user_instruction,
            response_schema=RecommendationData,
        )
    except genai_errors.ClientError as exc:
        logger.error("Gemini 호출 실패 (user_id=%s): %s", body.user_id, exc)
        raise HTTPException(
            status_code=500,
            detail={"code": "GEMINI_ERROR", "message": str(exc)},
        ) from exc

    # 4. 응답 파싱
    parsed = json.loads(raw_json)
    data = RecommendationData(**parsed)

    # 5. BackgroundTasks에 Summary 등록
    background_tasks.add_task(
        run_background_summary,
        user_id=body.user_id,
        user_message=body.user_instruction,
        ai_response=str(data.model_dump()),
        gemini_client=gemini_client,
        embed_client=embed_client,
        pinecone_client=pinecone_client,
    )

    return SuccessResponse(data=data.model_dump())
