"""Dependency container injected into graph nodes."""
from dataclasses import dataclass

from app.clients.embedding import EmbeddingClient
from app.clients.gemini import GeminiClient
from app.clients.pinecone import PineconeClient
from app.clients.was import WASClient
from app.core.profile_sync import ProfileSyncTracker


@dataclass
class NodeDeps:
    gemini: GeminiClient
    router: GeminiClient
    was: WASClient
    pinecone: PineconeClient
    embed: EmbeddingClient
    profile_sync: ProfileSyncTracker
