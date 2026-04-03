"""피드백 루프 — Layer 3 피드백 루프 상세 구현.

응답 출력 후 백그라운드에서 실행:
1. 반응 분석 (친밀도 · 페르소나 진화 업데이트) — 플레이스홀더
2. should_save_episode=True → vdb_memory 저장
3. 감정 이력 저장 (emotion 추이 누적) — 플레이스홀더

FastAPI BackgroundTasks에서 호출되는 함수로 구현.
"""
from __future__ import annotations

import logging
from datetime import datetime

from app.graph.deps import NodeDeps

logger = logging.getLogger(__name__)


async def execute_feedback(
    deps: NodeDeps,
    user_id: str,
    user_message: str,
    response: str,
    should_save_episode: bool,
    emotion_label: str,
    emotion_intensity: float,
) -> None:
    """피드백 루프 실행."""

    # ── should_save_episode → vdb_memory 저장 ─────────────────────────────
    if should_save_episode:
        episode_text = (
            f"[{datetime.utcnow().strftime('%Y-%m-%d')}] "
            f"사용자: {user_message[:200]} | "
            f"감정: {emotion_label} ({emotion_intensity:.1f})"
        )
        try:
            vec = await deps.embed.embed(episode_text)
            await deps.pinecone.upsert_memory(
                user_id=user_id,
                vector=vec,
                text=episode_text,
                emotion_label=emotion_label,
                intensity=emotion_intensity,
            )
            logger.info("에피소드 vdb_memory 저장 완료: user_id=%s", user_id)
        except Exception as e:
            logger.warning("에피소드 저장 실패 (무시): %s", e)

    # ── 감정 이력 저장 (로그로 대체 — 향후 DB 연동) ────────────────────────
    logger.info(
        "EMOTION_LOG | user_id=%s | label=%s | intensity=%.2f",
        user_id,
        emotion_label,
        emotion_intensity,
    )
