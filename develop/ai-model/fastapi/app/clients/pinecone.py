"""
PineconeClient — async 벡터 저장/검색 클라이언트.

user_id를 Pinecone namespace로 사용하여 사용자 간 벡터를 격리한다.
"""
from datetime import datetime
from typing import Any
from uuid import uuid4


class PineconeClient:
    """Pinecone IndexAsyncio 래퍼.

    Args:
        index: pinecone.Pinecone().IndexAsyncio(host=...) 인스턴스.
               lifespan에서 초기화되어 주입된다.
    """

    def __init__(self, index: Any) -> None:
        self._index = index

    async def upsert(
        self,
        user_id: str,
        vector: list[float],
        summary: str,
    ) -> str:
        """벡터를 user_id namespace에 저장하고 생성된 ID를 반환한다.

        Args:
            user_id: 사용자 식별자. Pinecone namespace로 사용된다.
            vector: 임베딩 벡터.
            summary: 저장할 텍스트 요약.

        Returns:
            생성된 UUID4 문자열.
        """
        vector_id = str(uuid4())
        metadata: dict[str, str] = {
            "user_id": user_id,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self._index.upsert(
            vectors=[{"id": vector_id, "values": vector, "metadata": metadata}],
            namespace=user_id,
        )
        return vector_id

    async def search(
        self,
        user_id: str,
        vector: list[float],
        top_k: int = 3,
    ) -> list[dict]:
        """user_id namespace에서 유사한 벡터를 검색한다.

        Args:
            user_id: 사용자 식별자. Pinecone namespace로 사용된다.
            vector: 쿼리 벡터.
            top_k: 반환할 최대 결과 수 (기본값 3).

        Returns:
            [{id, score, summary, timestamp}] 형태의 dict 리스트.
            score 내림차순 정렬.
        """
        result = await self._index.query(
            vector=vector,
            top_k=top_k,
            namespace=user_id,
            include_metadata=True,
        )
        return [
            {
                "id": match.id,
                "score": match.score,
                "summary": match.metadata.get("summary", ""),
                "timestamp": match.metadata.get("timestamp", ""),
            }
            for match in result.matches
        ]
