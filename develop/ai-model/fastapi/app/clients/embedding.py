"""EmbeddingClient: async wrapper around Google gemini-embedding-001 API.

Uses google-generativeai SDK for embedContent.
output_dimensionality=384 keeps Pinecone index compatibility.
"""
from __future__ import annotations

import asyncio
from functools import partial

import google.generativeai as genai

EMBEDDING_DIM: int = 384


class EmbeddingClient:
    """Async wrapper over Google gemini-embedding-001 via google-generativeai SDK."""

    def __init__(self, api_key: str) -> None:
        genai.configure(api_key=api_key)

    async def embed(self, text: str) -> list[float]:
        """Return a float vector for *text* via Google gemini-embedding-001.

        Args:
            text: Input text (may be empty).

        Returns:
            A list of floats representing the embedding.
        """
        fn = partial(
            genai.embed_content,
            model="models/gemini-embedding-001",
            content=text,
            output_dimensionality=EMBEDDING_DIM,
        )
        result = await asyncio.get_event_loop().run_in_executor(None, fn)
        return result["embedding"]
