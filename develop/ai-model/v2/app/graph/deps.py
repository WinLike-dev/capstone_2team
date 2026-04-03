"""NodeDependencies — 그래프 노드에 주입할 클라이언트 컨테이너."""
from dataclasses import dataclass

from app.clients.embedding import EmbeddingClient
from app.clients.gemini import GeminiClient
from app.clients.pinecone import PineconeClient
from app.clients.was import WASClient


@dataclass
class NodeDeps:
    gemini: GeminiClient      # Flash — 응답 생성
    router: GeminiClient      # Flash-Lite — 의도 분석 · 검색 평가
    was: WASClient
    pinecone: PineconeClient
    embed: EmbeddingClient
