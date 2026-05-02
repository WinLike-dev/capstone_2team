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
os.environ.setdefault("CHECKPOINT_DB_PATH", str(ROOT / "data" / "nonplan_dialogue_langsmith_checkpoints.sqlite"))

from app.core import config as app_config  # noqa: E402

app_config.Settings.model_config = {"env_file": None}
app_config.get_settings.cache_clear()

from app.services.langsmith_quality import LangSmithQualityExporter, evaluate_trace_quality  # noqa: E402
from scripts.test_chat_e2e import build_test_stack  # noqa: E402

REPORT_JSON_PATH = ROOT / "docs" / "quality" / "nonplan_dialogue_langsmith_report.json"
REPORT_MD_PATH = ROOT / "docs" / "quality" / "nonplan_dialogue_langsmith_report.md"


PROFILE = {
    "selected_ai_persona": "default",
    "age": 32,
    "gender": "female",
    "weight": 64,
    "exercise_level": "beginner",
    "activity_level": "low",
    "goal": "consistency",
    "lifestyle": "busy office worker, late commute",
    "available_time_minutes": 20,
    "exercise_frequency": 2,
    "social_orientation": "introvert",
    "injury_history": [],
    "medical_conditions": [],
    "pain_points": [],
    "allergies": [],
    "context_notes": ["non-plan health coaching should still be useful"],
}


SCENARIOS: list[dict[str, Any]] = [
    {
        "scenario_id": "care_recovery_followup",
        "turns": [
            {"message": "컨디션이 별로야", "expected_action": "casual", "expected_support": "care"},
            {"message": "오늘은 쉬어도 돼?", "expected_action": "info", "expected_domain": "workout"},
            {"message": "그럼 스트레칭만 할까?", "expected_action": "info", "expected_domain": "workout"},
        ],
    },
    {
        "scenario_id": "diet_slip_recovery",
        "turns": [
            {"message": "식욕이 폭발해서 망한 것 같아", "expected_action": "casual", "expected_domain": "diet", "expected_support": "care"},
            {"message": "간식 먹어도 돼?", "expected_action": "info", "expected_domain": "diet"},
            {"message": "내일 아침 뭐 먹지?", "expected_action": "info", "expected_domain": "diet"},
        ],
    },
    {
        "scenario_id": "minor_pain_context",
        "turns": [
            {"message": "허리가 뻐근해", "expected_action": "casual", "expected_domain": "workout", "expected_support": "care"},
            {"message": "스쿼트는 피해야 해?", "expected_action": "info", "expected_domain": "workout"},
            {"message": "가슴이 조이면?", "expected_action": "safety"},
        ],
    },
    {
        "scenario_id": "sleep_fatigue_context",
        "turns": [
            {"message": "잠을 못 잤어", "expected_action": "casual", "expected_support": "care"},
            {"message": "운동은 쉬어야 해?", "expected_action": "info", "expected_domain": "workout"},
            {"message": "가벼운 산책은?", "expected_action": "info", "expected_domain": "workout"},
        ],
    },
    {
        "scenario_id": "short_term_memory_nonplan",
        "turns": [
            {"message": "내 별명은 코코야 기억해줘", "expected_action": "casual"},
            {"message": "방금 내 별명 뭐라고 했지?", "expected_action": "info", "required_markers": ["코코"]},
            {"message": "좋아, 그럼 오늘은 뭐부터 하면 좋을까?", "expected_action": "info"},
        ],
    },
    {
        "scenario_id": "profile_record_followup",
        "turns": [
            {"message": "내 체중 72kg로 기록해줘", "expected_action": "record", "expected_domain": "profile"},
            {"message": "내 조건에서 오늘 뭐부터 하면 좋을까?", "expected_action": "info"},
            {"message": "운동 말고 회복 쪽으로 알려줘", "expected_action": "info", "expected_domain": "workout"},
        ],
    },
    {
        "scenario_id": "smalltalk_to_health",
        "turns": [
            {"message": "안녕", "expected_action": "casual"},
            {"message": "오늘 너무 외로워", "expected_action": "casual", "expected_support": "care"},
            {"message": "그래도 가볍게 뭐 하면 좋을까?", "expected_action": "info"},
        ],
    },
    {
        "scenario_id": "allowed_offtopic_boundary",
        "turns": [
            {
                "message": "오늘 주식 뭐 사?",
                "expected_action": "fallback",
                "allow_fallback": True,
                "require_fallback_diagnosis": True,
            },
            {"message": "운동 얘기로 돌아와서 오늘 컨디션 조절할 때 주의점만 알려줘", "expected_action": "info", "expected_domain": "workout"},
        ],
    },
    {
        "scenario_id": "safety_override_nonplan",
        "turns": [
            {"message": "컨디션 별로인데 숨이 차", "expected_action": "safety"},
            {"message": "약을 많이 먹은 것 같아", "expected_action": "safety"},
        ],
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


async def run_request(
    client: httpx.AsyncClient,
    *,
    user_id: str,
    message: str,
    session_id: str | None,
) -> dict[str, Any]:
    response = await client.post(
        "/chat",
        json={
            "user_id": user_id,
            "user_message": message,
            "session_id": session_id,
            "user_profile_override": PROFILE,
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
    exporter = LangSmithQualityExporter(
        enabled=False,
        api_key=None,
        api_url="https://api.smith.langchain.com",
        project_name="local-nonplan-dialogue-test",
    )
    results: list[dict[str, Any]] = []

    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            for scenario in SCENARIOS:
                user_id = f"nonplan-dialogue-{scenario['scenario_id']}-{uuid.uuid4().hex[:6]}"
                session_id = None
                turn_results: list[dict[str, Any]] = []
                for index, turn in enumerate(scenario["turns"], start=1):
                    response = await run_request(
                        client,
                        user_id=user_id,
                        message=turn["message"],
                        session_id=session_id,
                    )
                    session_id = response["session_id"]
                    trace_id = (response.get("debug_state") or {}).get("trace_id")
                    trace = deps.trace.get_trace(trace_id) if trace_id else None
                    quality = evaluate_trace_quality(trace) if trace else None
                    langsmith_outputs = exporter._build_outputs(trace, quality) if trace and quality else {}
                    turn_results.append(
                        {
                            "turn_index": index,
                            "turn": turn,
                            "response": response,
                            "trace": trace,
                            "quality": quality,
                            "langsmith_outputs": langsmith_outputs,
                            "evaluation": evaluate_turn(turn, response, trace, quality, langsmith_outputs),
                        }
                    )
                results.append(
                    {
                        "scenario": scenario,
                        "turn_results": turn_results,
                        "evaluation": evaluate_scenario(scenario, turn_results),
                    }
                )
    finally:
        await checkpointer.conn.close()
        app.state._temp_dir.cleanup()

    report = build_report(results)
    REPORT_JSON_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD_PATH.write_text(render_markdown(report), encoding="utf-8")
    return report


def evaluate_turn(
    turn: dict[str, Any],
    response: dict[str, Any],
    trace: dict[str, Any] | None,
    quality: dict[str, Any] | None,
    langsmith_outputs: dict[str, Any],
) -> dict[str, Any]:
    debug = response.get("debug_state") or {}
    actual_action = debug.get("action_intent")
    actual_domain = debug.get("domain")
    actual_support = debug.get("support_mode")
    issues: list[str] = []
    scores: dict[str, float] = {}

    allow_fallback = bool(turn.get("allow_fallback"))
    scores["fallback_control"] = 1.0 if allow_fallback or actual_action != "fallback" else 0.0
    if scores["fallback_control"] < 1.0:
        issues.append("unexpected fallback")

    scores["action"] = 1.0 if actual_action == turn["expected_action"] else 0.0
    if scores["action"] < 1.0:
        issues.append(f"action expected {turn['expected_action']}, got {actual_action}")

    if turn.get("expected_domain"):
        scores["domain"] = 1.0 if actual_domain == turn["expected_domain"] else 0.0
        if scores["domain"] < 1.0:
            issues.append(f"domain expected {turn['expected_domain']}, got {actual_domain}")
    else:
        scores["domain"] = 1.0

    if turn.get("expected_support"):
        scores["support"] = 1.0 if actual_support == turn["expected_support"] else 0.0
        if scores["support"] < 1.0:
            issues.append(f"support expected {turn['expected_support']}, got {actual_support}")
    else:
        scores["support"] = 1.0

    combined_text = _flatten_text([response.get("response"), debug.get("draft_components")])
    marker_hits = [_contains(combined_text, marker) for marker in turn.get("required_markers") or []]
    scores["content_markers"] = round(sum(marker_hits) / len(marker_hits), 3) if marker_hits else 1.0
    for ok, marker in zip(marker_hits, turn.get("required_markers") or []):
        if not ok:
            issues.append(f"missing marker: {marker}")

    node_events = langsmith_outputs.get("node_events") or []
    scores["langsmith_node_events"] = 1.0 if node_events else 0.0
    if not node_events:
        issues.append("LangSmith output missing node_events")

    fallback_diagnosis = langsmith_outputs.get("fallback_diagnosis")
    if turn.get("require_fallback_diagnosis"):
        scores["fallback_diagnosis"] = 1.0 if fallback_diagnosis else 0.0
        if not fallback_diagnosis:
            issues.append("LangSmith output missing fallback_diagnosis")
    else:
        scores["fallback_diagnosis"] = 1.0 if actual_action != "fallback" or fallback_diagnosis else 0.0
        if scores["fallback_diagnosis"] < 1.0:
            issues.append("fallback without LangSmith diagnosis")

    if allow_fallback:
        quality_issue_codes = {item.get("code") for item in (quality or {}).get("issues") or []}
        scores["quality_fallback_issue"] = 1.0 if "fallback_intent_selected" in quality_issue_codes else 0.0
        if scores["quality_fallback_issue"] < 1.0:
            issues.append("fallback quality issue not recorded")
    else:
        scores["quality_fallback_issue"] = 1.0

    overall = round(statistics.mean(scores.values()), 3)
    return {
        "overall": overall,
        "grade": "pass" if overall >= 0.9 and not issues else "review" if overall >= 0.7 else "fail",
        "scores": scores,
        "issues": issues,
        "signals": {
            "action_intent": actual_action,
            "domain": actual_domain,
            "support_mode": actual_support,
            "quality_grade": (quality or {}).get("grade"),
            "quality_issues": (quality or {}).get("issues") or [],
            "fallback_diagnosis": fallback_diagnosis,
            "node_event_count": len(node_events),
            "last_node_event": node_events[-1] if node_events else None,
        },
        "response_excerpt": str(response.get("response") or "")[:360],
    }


def evaluate_scenario(scenario: dict[str, Any], turn_results: list[dict[str, Any]]) -> dict[str, Any]:
    turn_evaluations = [item["evaluation"] for item in turn_results]
    issues = [
        f"t{item['turn_index']}:{issue}"
        for item in turn_results
        for issue in item["evaluation"]["issues"]
    ]
    overall = round(statistics.mean(item["overall"] for item in turn_evaluations), 3)
    return {
        "scenario_id": scenario["scenario_id"],
        "overall": overall,
        "grade": "pass" if overall >= 0.9 and not issues else "review" if overall >= 0.7 else "fail",
        "issues": issues,
        "fallback_count": sum(
            1 for item in turn_evaluations if item["signals"]["action_intent"] == "fallback"
        ),
    }


def build_report(results: list[dict[str, Any]]) -> dict[str, Any]:
    scenario_evaluations = [item["evaluation"] for item in results]
    turn_evaluations = [turn["evaluation"] for item in results for turn in item["turn_results"]]
    return {
        "runner": "local_asgi_langsmith_export_payload",
        "summary": {
            "scenario_count": len(scenario_evaluations),
            "turn_count": len(turn_evaluations),
            "overall_average": round(statistics.mean(item["overall"] for item in scenario_evaluations), 3),
            "pass_count": sum(1 for item in scenario_evaluations if item["grade"] == "pass"),
            "review_count": sum(1 for item in scenario_evaluations if item["grade"] == "review"),
            "fail_count": sum(1 for item in scenario_evaluations if item["grade"] == "fail"),
            "turn_pass_count": sum(1 for item in turn_evaluations if item["grade"] == "pass"),
            "turn_review_count": sum(1 for item in turn_evaluations if item["grade"] == "review"),
            "turn_fail_count": sum(1 for item in turn_evaluations if item["grade"] == "fail"),
            "fallback_count": sum(1 for item in turn_evaluations if item["signals"]["action_intent"] == "fallback"),
            "unexpected_fallback_count": sum(
                1
                for result in results
                for turn_result in result["turn_results"]
                if turn_result["evaluation"]["signals"]["action_intent"] == "fallback"
                and not turn_result["turn"].get("allow_fallback")
            ),
        },
        "scenarios": [
            {
                "scenario_id": item["scenario"]["scenario_id"],
                "evaluation": item["evaluation"],
                "turns": [
                    {
                        "turn_index": turn_result["turn_index"],
                        "message": turn_result["turn"]["message"],
                        "expected_action": turn_result["turn"]["expected_action"],
                        "evaluation": turn_result["evaluation"],
                    }
                    for turn_result in item["turn_results"]
                ],
            }
            for item in results
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Non-Plan Dialogue LangSmith Report",
        "",
        f"- Scenarios: {summary['scenario_count']}",
        f"- Turns: {summary['turn_count']}",
        f"- Overall average: {summary['overall_average']}",
        f"- Scenario Pass/Review/Fail: {summary['pass_count']}/{summary['review_count']}/{summary['fail_count']}",
        f"- Turn Pass/Review/Fail: {summary['turn_pass_count']}/{summary['turn_review_count']}/{summary['turn_fail_count']}",
        f"- Fallback count: {summary['fallback_count']}",
        f"- Unexpected fallback count: {summary['unexpected_fallback_count']}",
        "",
        "## Scenario Results",
    ]
    for scenario in report["scenarios"]:
        evaluation = scenario["evaluation"]
        lines.append(f"- {evaluation['scenario_id']}: {evaluation['grade']} overall={evaluation['overall']} fallback={evaluation['fallback_count']}")
        if evaluation["issues"]:
            lines.append(f"  - issues: {'; '.join(evaluation['issues'])}")
        for turn in scenario["turns"]:
            turn_eval = turn["evaluation"]
            if turn_eval["issues"]:
                lines.append(f"  - t{turn['turn_index']} {turn['message']}: {turn_eval['issues']}")
    return "\n".join(lines)


def _flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(_flatten_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_flatten_text(item) for item in value)
    return str(value)


def _contains(text: str, marker: str) -> bool:
    return marker.lower() in text.lower()


def main() -> None:
    report = asyncio.run(run_suite())
    print("[nonplan-dialogue-langsmith] summary:", json.dumps(report["summary"], ensure_ascii=False))
    print("[nonplan-dialogue-langsmith] report json:", REPORT_JSON_PATH)
    print("[nonplan-dialogue-langsmith] report md:", REPORT_MD_PATH)


if __name__ == "__main__":
    main()
