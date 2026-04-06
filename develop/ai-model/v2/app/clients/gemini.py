"""Gemini 비동기 클라이언트.

- generate(): JSON 구조화 출력 (Pydantic 스키마 기반)
- generate_text(): 자유 텍스트 출력 (응답 생성용)
- search_web(): Google Search grounding 기반 웹 검색 결과 정규화
- tenacity로 429 ResourceExhausted 재시도 적용
"""
from collections import defaultdict
from typing import Any

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)


def _is_resource_exhausted(exc: BaseException) -> bool:
    return isinstance(exc, genai_errors.ClientError) and exc.code == 429


def _get_value(obj: Any, *names: str, default: Any = None) -> Any:
    if obj is None:
        return default
    for name in names:
        if isinstance(obj, dict) and name in obj and obj[name] is not None:
            return obj[name]
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default


def _grounding_to_results(
    grounding_metadata: Any,
    fallback_text: str,
    max_results: int,
) -> list[dict[str, Any]]:
    supports = _get_value(
        grounding_metadata,
        "grounding_supports",
        "groundingSupports",
        default=[],
    ) or []
    chunks = _get_value(
        grounding_metadata,
        "grounding_chunks",
        "groundingChunks",
        default=[],
    ) or []

    snippets_by_chunk: dict[int, list[str]] = defaultdict(list)
    for support in supports:
        segment = _get_value(support, "segment")
        segment_text = (_get_value(segment, "text", default="") or "").strip()
        chunk_indices = _get_value(
            support,
            "grounding_chunk_indices",
            "groundingChunkIndices",
            default=[],
        ) or []
        if not segment_text:
            continue
        for chunk_index in chunk_indices:
            if isinstance(chunk_index, int):
                snippets_by_chunk[chunk_index].append(segment_text)

    results: list[dict[str, Any]] = []
    for idx, chunk in enumerate(chunks[:max_results]):
        web = _get_value(chunk, "web")
        url = (_get_value(web, "uri", "url", default="") or "").strip()
        title = (_get_value(web, "title", default="") or "").strip()
        snippet_parts = snippets_by_chunk.get(idx, [])
        snippet = " ".join(dict.fromkeys(snippet_parts)).strip()
        if not snippet:
            snippet = fallback_text.strip()[:500]
        if not any((url, title, snippet)):
            continue
        results.append(
            {
                "id": f"web-{idx}",
                "score": max(0.35, 0.60 - idx * 0.02),
                "text": snippet,
                "source": "web",
                "title": title or url or "Google Search",
                "url": url,
                "timestamp": "",
            }
        )

    if results:
        return results

    text = fallback_text.strip()
    if not text:
        return []
    return [
        {
            "id": "web-summary-0",
            "score": 0.55,
            "text": text[:500],
            "source": "web",
            "title": "Google Search",
            "url": "",
            "timestamp": "",
        }
    ]


class GeminiClient:
    def __init__(self, api_key: str, model_name: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    @retry(
        wait=wait_exponential_jitter(initial=1, max=60, jitter=5),
        stop=stop_after_attempt(5),
        retry=retry_if_exception(_is_resource_exhausted),
        reraise=True,
    )
    async def generate(
        self,
        system_prompt: str,
        user_content: str,
        response_schema: type,
    ) -> str:
        """JSON 구조화 출력 생성 (의도 분석 · 검색 평가용)."""
        response = await self._client.aio.models.generate_content(
            model=self._model_name,
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=response_schema,
            ),
        )
        return response.text

    @retry(
        wait=wait_exponential_jitter(initial=1, max=60, jitter=5),
        stop=stop_after_attempt(5),
        retry=retry_if_exception(_is_resource_exhausted),
        reraise=True,
    )
    async def generate_text(
        self,
        system_prompt: str,
        user_content: str,
    ) -> str:
        """자유 텍스트 응답 생성 (응답 생성 노드용)."""
        response = await self._client.aio.models.generate_content(
            model=self._model_name,
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        return response.text

    @retry(
        wait=wait_exponential_jitter(initial=1, max=60, jitter=5),
        stop=stop_after_attempt(5),
        retry=retry_if_exception(_is_resource_exhausted),
        reraise=True,
    )
    async def search_web(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Google Search grounding 결과를 검색 파이프라인 형식으로 정규화한다."""
        response = await self._client.aio.models.generate_content(
            model=self._model_name,
            contents=query,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0,
            ),
        )

        candidates = getattr(response, "candidates", None) or []
        candidate = candidates[0] if candidates else None
        grounding_metadata = _get_value(
            candidate,
            "grounding_metadata",
            "groundingMetadata",
        )
        return _grounding_to_results(
            grounding_metadata,
            fallback_text=response.text or "",
            max_results=max_results,
        )
