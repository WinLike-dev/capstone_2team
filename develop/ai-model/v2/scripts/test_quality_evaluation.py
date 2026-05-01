from __future__ import annotations

import os
import sys
from pathlib import Path

for key, value in {
    "GEMINI_API_KEY": "test-gemini",
    "ROUTER_API_KEY": "test-router",
    "PINECONE_API_KEY": "test-pinecone",
    "PINECONE_INDEX_NAME": "test-index",
    "WAS_BASE_URL": "http://was.test",
}.items():
    os.environ.setdefault(key, value)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.trace_store import TraceStore
from app.services.langsmith_quality import record_quality_for_trace


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    store = TraceStore()
    good_trace_id = store.start_trace(
        kind="chat",
        user_id="user-1",
        session_id="session-1",
        message="오늘 운동 계획 짜줘",
        request_payload={"user_message": "오늘 운동 계획 짜줘"},
    )
    store.finish_trace(
        good_trace_id,
        status="response_sent",
        response={"response": "오늘은 하체 루틴과 가벼운 유산소를 제안할게요."},
        state_summary={
            "intent": "계획",
            "action_intent": "create",
            "domain": "workout",
            "search_quality": "ok",
            "search_results_count": 2,
            "proposed_plan_count": 2,
            "pending_writes_count": 0,
            "needs_clarification": False,
            "draft_components": {"suggested_action": "이 계획으로 진행할지 알려주세요."},
        },
    )
    good_quality = record_quality_for_trace(store, good_trace_id)
    require(good_quality is not None, "good trace quality should be recorded")
    require(good_quality["grade"] == "pass", "good trace should pass")
    require(store.list_traces(limit=1)[0]["summary"]["quality_grade"] == "pass", "summary should expose quality grade")

    bad_trace_id = store.start_trace(
        kind="chat",
        user_id="user-2",
        session_id="session-2",
        message="오늘 운동 계획 짜줘",
        request_payload={"user_message": "오늘 운동 계획 짜줘"},
    )
    store.finish_trace(
        bad_trace_id,
        status="failed",
        response={"response": ""},
        state_summary={
            "intent": "계획",
            "action_intent": "create",
            "domain": "workout",
            "search_quality": "degraded",
            "search_results_count": 0,
            "proposed_plan_count": 0,
            "pending_writes_count": 0,
            "needs_clarification": False,
        },
    )
    bad_quality = record_quality_for_trace(store, bad_trace_id)
    require(bad_quality is not None, "bad trace quality should be recorded")
    require(bad_quality["grade"] == "fail", "bad trace should fail")
    require(bad_quality["issue_count"] >= 2, "bad trace should expose issues")

    print("[quality-evaluation] 2/2 passed")


if __name__ == "__main__":
    main()
