from fastapi import APIRouter, BackgroundTasks, Request

from app.schemas.chat import AiChatRequest, AiChatResponse
from app.services.chat_service import handle_ai_chat

router = APIRouter(tags=["chat"])


@router.post("/ai-chat", response_model=AiChatResponse)
async def ai_chat_endpoint(
    body: AiChatRequest,
    request: Request,
    background_tasks: BackgroundTasks,
) -> AiChatResponse:
    """AI 채팅 파이프라인을 실행한다. Router AI 의도분류 -> 병렬 맥락검색 -> 워커 AI 응답."""
    return await handle_ai_chat(body, request, background_tasks)
