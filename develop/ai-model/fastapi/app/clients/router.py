"""Router AI client for classifying user messages into 6 modes.

Uses Gemini Flash Lite with a separate API key (ROUTER_API_KEY) and model
(ROUTER_MODEL_NAME), independent of the main GeminiClient.
"""

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.prompts.router import ROUTER_SYSTEM_PROMPT


class RouterOutput(BaseModel):
    """Output schema for router classification.

    mode: int between 1-6
      1 = 단순대화, 2 = 플랜 작성, 3 = 플랜 수정,
      4 = 식단 작성, 5 = 식단 수정, 6 = DB 수정
    reason: short explanation of the classification decision
    """

    mode: int
    reason: str


class RouterClient:
    """Classifies user messages into one of 6 intent modes.

    Designed to operate independently from GeminiClient —
    uses its own API key and model name.
    """

    def __init__(self, api_key: str, model_name: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    async def classify(self, user_message: str) -> RouterOutput:
        """Classify user_message into one of 6 modes.

        On JSON parse failure, returns mode=1 (단순대화) as a safe fallback.

        Args:
            user_message: The raw message text from the user.

        Returns:
            RouterOutput with mode (1-6) and reason string.
        """
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model_name,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=ROUTER_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=RouterOutput,
                ),
            )
            return RouterOutput.model_validate_json(response.text)
        except Exception:
            return RouterOutput(mode=1, reason="파싱 실패 - 기본 모드로 처리")
