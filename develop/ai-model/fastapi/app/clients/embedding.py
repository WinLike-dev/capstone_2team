"""EmbeddingClient: async wrapper around Google text-embedding-004 API.

Uses google-genai SDK to generate embeddings via the Gemini API.
output_dimensionality=384 keeps Pinecone index compatibility.
"""
from __future__ import annotations

from google import genai
from google.genai import types

# text-embedding-004 with output_dimensionality=384 for Pinecone compatibility.
EMBEDDING_DIM: int = 384


class EmbeddingClient:
    """Async wrapper over Google text-embedding-004."""

    def __init__(self, api_key: str) -> None:
        self._client = genai.Client(api_key=api_key)

    async def embed(self, text: str) -> list[float]:
        """Return a 384-dim float vector for *text* via Google text-embedding-004.

        Args:
            text: Input text (may be empty).

        Returns:
            A list of 384 floats representing the embedding.
        """
        response = await self._client.aio.models.embed_content(
            model="text-embedding-004",
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
        )
        return response.embeddings[0].values
