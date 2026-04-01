"""Gemini Flash 비동기 클라이언트.

google-genai SDK를 래핑하여 JSON 응답을 생성한다.
tenacity로 429 ResourceExhausted 에러 시 exponential backoff + jitter 재시도를 적용한다.
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
    """429 ResourceExhausted 에러인지 확인한다."""
    return isinstance(exc, genai_errors.ClientError) and exc.code == 429


class GeminiClient:
    """Gemini Flash API를 호출하는 비동기 클라이언트."""

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
        """시스템 프롬프트와 사용자 입력으로 Gemini API를 호출하고 JSON text를 반환한다.

        Args:
            system_prompt: 모드별 시스템 지시사항.
            user_content: 사용자 입력 내용.
            response_schema: JSON 출력 스키마 (Pydantic BaseModel 서브클래스).

        Returns:
            Gemini API의 JSON 응답 텍스트.

        Raises:
            genai_errors.ClientError: 5회 재시도 후에도 429 에러가 지속될 때, 또는
                                      재시도 불가 4xx 에러 발생 시.
        """
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
