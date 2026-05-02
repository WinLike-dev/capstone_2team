from __future__ import annotations

import asyncio
import json
import os
import statistics
import sys
import uuid
from pathlib import Path
from typing import Any

import aiosqlite
import httpx

for key, value in {
    "GEMINI_API_KEY": "test-gemini",
    "ROUTER_API_KEY": "test-router",
    "PINECONE_API_KEY": "test-pinecone",
    "PINECONE_INDEX_NAME": "test-index",
    "WAS_BASE_URL": "http://was.test",
    "INTERNAL_API_KEY": "test-internal-key",
    "APP_ENV": "development",
}.items():
    os.environ.setdefault(key, value)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("CHECKPOINT_DB_PATH", str(ROOT / "data" / "fallback_langsmith_trace_checkpoints.sqlite"))

from app.core import config as app_config  # noqa: E402

app_config.Settings.model_config = {"env_file": None}
app_config.get_settings.cache_clear()

from app.services.langsmith_quality import evaluate_trace_quality  # noqa: E402
from scripts.test_chat_e2e import build_test_stack  # noqa: E402

REPORT_JSON_PATH = ROOT / "docs" / "quality" / "fallback_langsmith_trace_report.json"
REPORT_MD_PATH = ROOT / "docs" / "quality" / "fallback_langsmith_trace_report.md"


CASES: list[dict[str, Any]] = [
    {
        "case_id": "nonplan_start_hint",
        "message": "오늘 뭐부터 하면 좋을까?",
        "expected_action": "info",
    },
    {
        "case_id": "recovery_rest_question",
        "message": "오늘은 쉬어도 돼?",
        "expected_action": "info",
    },
    {
        "case_id": "low_condition_statement",
        "message": "컨디션이 별로야",
        "expected_action": "casual",
        "expected_support": "care",
    },
    {
        "case_id": "fatigue_statement",
        "message": "오늘 너무 피곤해",
        "expected_action": "casual",
        "expected_support": "care",
    },
    {
        "case_id": "poor_sleep_statement",
        "message": "잠을 못 잤어",
        "expected_action": "casual",
        "expected_support": "care",
    },
    {
        "case_id": "appetite_spike_statement",
        "message": "식욕이 폭발해서 망한 것 같아",
        "expected_action": "casual",
        "expected_support": "care",
    },
    {
        "case_id": "meal_choice_question",
        "message": "오늘 뭐 먹지?",
        "expected_action": "info",
        "expected_domain": "diet",
    },
    {
        "case_id": "back_stiff_statement",
        "message": "허리가 뻐근해",
        "expected_action": "casual",
        "expected_support": "care",
    },
    {
        "case_id": "muscle_soreness_question",
        "message": "운동 후 근육통이 심한데 어떻게 해야 해?",
        "expected_action": "info",
        "expected_domain": "workout",
    },
    {
        "case_id": "walking_allowed_question",
        "message": "걷기 해도 될까?",
        "expected_action": "info",
        "expected_domain": "workout",
    },
    {
        "case_id": "water_amount_question",
        "message": "물 얼마나 마셔야 해?",
        "expected_action": "info",
    },
    {
        "case_id": "protein_amount_question",
        "message": "단백질은 어느 정도 먹으면 좋아?",
        "expected_action": "info",
        "expected_domain": "diet",
    },
    {
        "case_id": "stretching_only_question",
        "message": "오늘 스트레칭만 해도 괜찮아?",
        "expected_action": "info",
        "expected_domain": "workout",
    },
    {
        "case_id": "snack_allowed_question",
        "message": "배고픈데 간식 먹어도 돼?",
        "expected_action": "info",
        "expected_domain": "diet",
    },
]


async def ensure_activity_table(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS session_activity ("
            "  thread_id TEXT PRIMARY KEY,"
            "  last_active TEXT NOT NULL DEFAULT (datetime('now'))"
            ")"
        )
        await db.commit()


async def run_request(client: httpx.AsyncClient, *, user_id: str, message: str) -> dict[str, Any]:
    response = await client.post(
        "/chat",
        json={
            "user_id": user_id,
            "user_message": message,
            "user_profile_override": {
                "selected_ai_persona": "default",
                "age": 32,
                "gender": "female",
                "weight": 64,
                "exercise_level": "beginner",
                "activity_level": "low",
                "goal": "consistency",
                "lifestyle": "busy office worker",
                "available_time_minutes": 20,
                "exercise_frequency": 2,
                "injury_history": [],
                "medical_conditions": [],
                "pain_points": [],
                "allergies": [],
                "context_notes": [],
            },
        },
        headers={"x-api-key": os.environ["INTERNAL_API_KEY"]},
    )
    body = response.json()
    if response.status_code != 200:
        raise AssertionError(f"HTTP {response.status_code}: {body}")
    return body


async def run_suite() -> dict[str, Any]:
    await ensure_activity_table(os.environ["CHECKPOINT_DB_PATH"])
    app, _graph, deps, _fake_was, checkpointer = await build_test_stack()
    transport = httpx.ASGITransport(app=app)
    results: list[dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            for case in CASES:
                response = await run_request(
                    client,
                    user_id=f"fallback-trace-{case['case_id']}-{uuid.uuid4().hex[:6]}",
                    message=case["message"],
                )
                trace_id = (response.get("debug_state") or {}).get("trace_id")
                trace = deps.trace.get_trace(trace_id) if trace_id else None
                quality = evaluate_trace_quality(trace) if trace else None
                results.append(
                    {
                        "case": case,
                        "response": response,
                        "trace": trace,
                        "quality": quality,
                        "evaluation": evaluate_case(case, response, trace, quality),
                    }
                )
    finally:
        await checkpointer.conn.close()
        app.state._temp_dir.cleanup()

    report = build_report(results)
    REPORT_JSON_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD_PATH.write_text(render_markdown(report), encoding="utf-8")
    return report


def evaluate_case(
    case: dict[str, Any],
    response: dict[str, Any],
    trace: dict[str, Any] | None,
    quality: dict[str, Any] | None,
) -> dict[str, Any]:
    debug = response.get("debug_state") or {}
    issues: list[str] = []
    scores: dict[str, float] = {}
    actual_action = debug.get("action_intent")
    actual_domain = debug.get("domain")
    actual_support = debug.get("support_mode")

    scores["not_fallback"] = 0.0 if actual_action == "fallback" else 1.0
    if actual_action == "fallback":
        issues.append("unexpected fallback")

    scores["action"] = 1.0 if actual_action == case["expected_action"] else 0.0
    if scores["action"] < 1.0:
        issues.append(f"action expected {case['expected_action']}, got {actual_action}")

    if case.get("expected_domain"):
        scores["domain"] = 1.0 if actual_domain == case["expected_domain"] else 0.0
        if scores["domain"] < 1.0:
            issues.append(f"domain expected {case['expected_domain']}, got {actual_domain}")
    else:
        scores["domain"] = 1.0

    if case.get("expected_support"):
        scores["support"] = 1.0 if actual_support == case["expected_support"] else 0.0
        if scores["support"] < 1.0:
            issues.append(f"support expected {case['expected_support']}, got {actual_support}")
    else:
        scores["support"] = 1.0

    fallback_text = "질문을 정확히 이해하지 못" in str(response.get("response") or "")
    scores["no_clarification_text"] = 0.0 if fallback_text else 1.0
    if fallback_text:
        issues.append("fallback clarification text returned")

    overall = round(statistics.mean(scores.values()), 3)
    return {
        "case_id": case["case_id"],
        "overall": overall,
        "grade": "pass" if overall >= 0.9 and not issues else "review" if overall >= 0.7 else "fail",
        "scores": scores,
        "issues": issues,
        "signals": {
            "action_intent": actual_action,
            "domain": actual_domain,
            "support_mode": actual_support,
            "fallback_diagnosis": fallback_diagnosis(trace),
            "quality_issues": (quality or {}).get("issues") or [],
        },
        "response_excerpt": str(response.get("response") or "")[:300],
    }


def fallback_diagnosis(trace: dict[str, Any] | None) -> dict[str, Any]:
    events = (trace or {}).get("events") or []
    intent_events = [event for event in events if event.get("stage") in {"intent", "context_resolver", "fallback"}]
    return {
        "state_action": ((trace or {}).get("state_summary") or {}).get("action_intent"),
        "state_domain": ((trace or {}).get("state_summary") or {}).get("domain"),
        "events": [
            {
                "stage": event.get("stage"),
                "status": event.get("status"),
                "title": event.get("title"),
                "detail": event.get("detail"),
            }
            for event in intent_events
        ],
    }


def build_report(results: list[dict[str, Any]]) -> dict[str, Any]:
    evaluations = [item["evaluation"] for item in results]
    return {
        "runner": "local_asgi_langsmith_trace_source",
        "summary": {
            "case_count": len(evaluations),
            "overall_average": round(statistics.mean(item["overall"] for item in evaluations), 3),
            "pass_count": sum(1 for item in evaluations if item["grade"] == "pass"),
            "review_count": sum(1 for item in evaluations if item["grade"] == "review"),
            "fail_count": sum(1 for item in evaluations if item["grade"] == "fail"),
            "fallback_count": sum(1 for item in evaluations if item["signals"]["action_intent"] == "fallback"),
        },
        "cases": [
            {
                "case_id": item["case"]["case_id"],
                "message": item["case"]["message"],
                "expected_action": item["case"]["expected_action"],
                "evaluation": item["evaluation"],
            }
            for item in results
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Fallback LangSmith Trace Report",
        "",
        f"- Cases: {summary['case_count']}",
        f"- Overall average: {summary['overall_average']}",
        f"- Pass/Review/Fail: {summary['pass_count']}/{summary['review_count']}/{summary['fail_count']}",
        f"- Fallback count: {summary['fallback_count']}",
        "",
        "## Case Results",
    ]
    for item in report["cases"]:
        evaluation = item["evaluation"]
        lines.append(f"- {evaluation['case_id']}: {evaluation['grade']} overall={evaluation['overall']}")
        if evaluation["issues"]:
            lines.append(f"  - issues: {'; '.join(evaluation['issues'])}")
            diagnosis = evaluation["signals"]["fallback_diagnosis"]
            last_event = (diagnosis.get("events") or [{}])[-1]
            lines.append(f"  - last_trace_event: {last_event.get('stage')} / {last_event.get('title')} / {last_event.get('detail')}")
    return "\n".join(lines)


def main() -> None:
    report = asyncio.run(run_suite())
    print("[fallback-langsmith-trace] summary:", json.dumps(report["summary"], ensure_ascii=False))
    print("[fallback-langsmith-trace] report json:", REPORT_JSON_PATH)
    print("[fallback-langsmith-trace] report md:", REPORT_MD_PATH)


if __name__ == "__main__":
    main()
