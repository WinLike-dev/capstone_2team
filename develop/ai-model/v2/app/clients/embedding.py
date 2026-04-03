"""EmbeddingClient: Google gemini-embedding-001 비동기 래퍼.

google.genai (신 SDK) 사용 — gemini.py와 동일한 SDK로 통일.
"""
from __future__ import annotations

from google import genai
from google.genai import types

EMBEDDING_DIM: int = 384


class EmbeddingClient:
    def __init__(self, api_key: str) -> None:
        self._client = genai.Client(api_key=api_key)

    async def embed(self, text: str) -> list[float]:
        result = await self._client.aio.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
        )
        return list(result.embeddings[0].values)
