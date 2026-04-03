"""Gemini 비동기 클라이언트.

- generate(): JSON 구조화 출력 (Pydantic 스키마 기반)
- generate_text(): 자유 텍스트 출력 (응답 생성용)
- tenacity로 429 ResourceExhausted 재시도 적용
"""
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
