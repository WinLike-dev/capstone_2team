"""공감_케어 노드 — Layer 3 공감_케어 상세 구현.

requires_past_memory에 따라 라우팅을 결정한다.
- false: 즉각 위로 모드 (감정 기반 톤 조절) → 응답 생성으로
- true:  기억 검색 필요 → 검색 파이프라인으로

이 노드 자체는 State를 가공하지 않고 라우팅 신호만 세팅한다.
"""
from __future__ import annotations

from app.graph.deps import NodeDeps
from app.schemas.state import GraphState


def make_care_node(deps: NodeDeps):
    async def care_node(state: GraphState) -> dict:
        requires_past_memory = state.get("requires_past_memory", False)

        if requires_past_memory:
            # 검색 파이프라인으로 진입: vdb_memory 우선 검색
            return {"search_targets": ["vdb_memory", "vdb_user_important"]}

        # 즉각 위로 모드: 검색 없이 바로 응답 생성
        return {}

    return care_node
