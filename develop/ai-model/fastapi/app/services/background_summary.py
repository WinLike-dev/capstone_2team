"""Background Summary 파이프라인.

대화(user_message + ai_response)를 Gemini로 요약하고
임베딩 후 Pinecone에 저장한다.
에러 발생 시 예외를 전파하지 않고 로그만 남긴다.
"""

import json
import logging

from app.clients.embedding import EmbeddingClient
from app.clients.gemini import GeminiClient
from app.clients.pinecone import PineconeClient
from app.prompts.summary import SummaryOutput, build_summary_prompt

logger = logging.getLogger(__name__)


async def run_background_summary(
    user_id: str,
    user_message: str,
    ai_response: str,
    gemini_client: GeminiClient,
    embed_client: EmbeddingClient,
    pinecone_client: PineconeClient,
) -> None:
    """대화 요약 -> 임베딩 -> Pinecone 저장 파이프라인을 실행한다.

    Args:
        user_id: 사용자 식별자 (Pinecone namespace에 사용).
        user_message: 사용자 질문 텍스트.
        ai_response: AI 응답 텍스트.
        gemini_client: Gemini API 클라이언트.
        embed_client: 임베딩 클라이언트.
        pinecone_client: Pinecone 클라이언트.

    Notes:
        예외가 발생해도 전파되지 않음. 로그만 남김 (BGSM-05).
        Request 객체를 인자로 받지 않음 — 클라이언트를 직접 주입받음.
    """
    try:
        system_prompt = build_summary_prompt()
        user_content = f"질문: {user_message}\n답변: {ai_response}"

        raw_json = await gemini_client.generate(
            system_prompt=system_prompt,
            user_content=user_content,
            response_schema=SummaryOutput,
        )

        summary_text: str = json.loads(raw_json)["summary"]

        vector: list[float] = await embed_client.embed(summary_text)

        await pinecone_client.upsert(
            user_id=user_id,
            vector=vector,
            summary=summary_text,
        )

    except Exception:
        logger.exception(
            "Background summary 파이프라인 오류 (user_id=%s)", user_id
        )
