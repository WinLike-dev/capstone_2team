"""EmbeddingClient: async wrapper around SentenceTransformer encode().

Uses run_in_threadpool to offload CPU-bound encode() calls so the asyncio
event loop is never blocked.
"""
from __future__ import annotations

from starlette.concurrency import run_in_threadpool

# paraphrase-multilingual-MiniLM-L12-v2 outputs 384-dim vectors.
# This constant is also used to validate the Pinecone index dimension.
EMBEDDING_DIM: int = 384


class EmbeddingClient:
    """Thin async wrapper over a SentenceTransformer model."""

    def __init__(self, model: object) -> None:
        """
        Args:
            model: A SentenceTransformer instance (or any object with an
                   ``encode(text: str) -> np.ndarray`` method).
        """
        self._model = model

    async def embed(self, text: str) -> list[float]:
        """Return a 384-dim float vector for *text*.

        The underlying ``encode()`` call is offloaded to a thread pool to
        prevent blocking the asyncio event loop.

        Args:
            text: Input text (may be empty).

        Returns:
            A list of 384 floats representing the embedding.
        """
        vector = await run_in_threadpool(self._model.encode, text)
        return vector.tolist()
