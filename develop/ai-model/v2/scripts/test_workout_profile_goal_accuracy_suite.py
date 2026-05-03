from __future__ import annotations

import asyncio
import json
import os
import re
import statistics
import sys
import uuid
from pathlib import Path
from typing import Any

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
os.environ.setdefault("CHECKPOINT_DB_PATH", str(ROOT / "data" / "workout_profile_goal_accuracy.sqlite"))

from app.core import config as app_config  # noqa: E402

app_config.Settings.model_config = {"env_file": None}
app_config.get_settings.cache_clear()

from app.services.home_recommendations import empty_home_recommendations, kst_today_iso  # noqa: E402
from scripts.test_chat_e2e import build_test_stack  # noqa: E402

REPORT_DIR = ROOT / "docs" / "quality"
REPORT_JSON_PATH = REPORT_DIR / "workout_profile_goal_accuracy_report.json"
REPORT_MD_PATH = REPORT_DIR / "workout_profile_goal_accuracy_report.md"

CATEGORIES = ("stretching", "cardio", "upper_body", "lower_body")
CATEGORY_LABELS = {
    "stretching": "스트레칭",
    "cardio": "유산소",
    "upper_body": "상체",
    "lower_body": "하체",
}
CATEGORY_MARKERS = {
    "stretching": ("스트레칭", "stretch", "가동성", "전신"),
    "cardio": ("유산소", "cardio", "걷기", "walk", "treadmill", "자전거"),
    "upper_body": ("상체", "upper", "푸시업", "로우", "push", "row"),
    "lower_body": ("하체", "lower", "leg", "스쿼트", "런지", "브릿지", "bridge"),
}
INTROVERT_MARKERS = ("집", "홈", "실내", "제자리", "혼자", "조용", "고정 루틴")
EXTROVERT_MARKERS = ("친구", "그룹", "함께", "챌린지", "수업")
FAT_LOSS_MARKERS = ("다이어트", "감량", "체중 감량", "유산소 비중")
MUSCLE_MARKERS = ("근력", "근육", "과부하", "큰 근육")
MOBILITY_MARKERS = ("가동성", "건강", "관절", "부상 예방", "저강도")
CONSISTENCY_MARKERS = ("지속", "습관", "낮은 기준", "회복일", "반복 가능")


def _profile(**overrides: Any) -> dict[str, Any]:
    profile: dict[str, Any] = {
        "selected_ai_persona": "default",
        "age": 34,
        "gender": "female",
        "weight": 68,
        "exercise_level": "beginner",
        "activity_level": "low",
        "goal": "fat_loss",
        "lifestyle": "busy office worker",
        "available_time_minutes": 20,
        "exercise_frequency": 3,
        "injury_history": [],
        "medical_conditions": [],
        "pain_points": [],
        "allergies": [],
        "context_notes": [],
    }
    profile.update(overrides)
    return profile


def workout_profile_cases() -> list[dict[str, Any]]:
    return [
        {
            "case_id": "api_introvert_fat_loss_beginner",
            "source": "chat_api",
            "profile": _profile(
                age=29,
                gender="female",
                weight=73,
                social_orientation="내향형",
                goal="fat_loss",
                exercise_level="beginner",
                exercise_frequency=3,
                available_time_minutes=20,
                lifestyle="퇴근 후 집에서만 운동 가능",
            ),
            "expected": {
                "orientation": "introvert",
                "goal": "fat_loss",
                "first_category": "cardio",
                "max_sets": 2,
                "max_duration": 20,
                "frequency": 3,
                "home_cardio": True,
            },
        },
        {
            "case_id": "api_extrovert_fat_loss_busy",
            "source": "chat_api",
            "profile": _profile(
                age=37,
                gender="male",
                weight=86,
                social_orientation="외향형",
                goal="fat_loss",
                exercise_level="beginner",
                exercise_frequency=2,
                available_time_minutes=18,
                lifestyle="야근이 잦아 짧게 운동",
            ),
            "expected": {
                "orientation": "extrovert",
                "goal": "fat_loss",
                "first_category": "cardio",
                "max_sets": 2,
                "max_duration": 18,
                "frequency": 2,
            },
        },
        {
            "case_id": "api_introvert_muscle_advanced",
            "source": "chat_api",
            "profile": _profile(
                age=32,
                gender="male",
                weight=76,
                social_orientation="introvert",
                goal="muscle_gain",
                exercise_level="advanced",
                exercise_frequency=5,
                available_time_minutes=45,
                lifestyle="홈짐에서 혼자 운동",
            ),
            "expected": {
                "orientation": "introvert",
                "goal": "muscle_gain",
                "first_category": "upper_body",
                "max_sets": 4,
                "frequency": 5,
            },
        },
        {
            "case_id": "api_extrovert_muscle_intermediate",
            "source": "chat_api",
            "profile": _profile(
                age=28,
                gender="female",
                weight=61,
                social_orientation="extroverted",
                goal="strength",
                exercise_level="intermediate",
                exercise_frequency=4,
                available_time_minutes=40,
                lifestyle="동료와 헬스장 수업 선호",
            ),
            "expected": {
                "orientation": "extrovert",
                "goal": "muscle_gain",
                "first_category": "upper_body",
                "max_sets": 3,
                "frequency": 4,
            },
        },
        {
            "case_id": "api_introvert_mobility_back_pain",
            "source": "chat_api",
            "profile": _profile(
                age=46,
                gender="female",
                weight=64,
                social_orientation="내향형",
                goal="mobility",
                exercise_level="beginner",
                exercise_frequency=3,
                available_time_minutes=15,
                injury_history=["lower back pain"],
                pain_points=["허리"],
                lifestyle="오래 앉아 일하고 조용한 홈트 선호",
            ),
            "expected": {
                "orientation": "introvert",
                "goal": "mobility",
                "first_category": "stretching",
                "max_sets": 2,
                "max_duration": 15,
                "frequency": 3,
                "constraints": ("허리", "lower back pain"),
                "forbidden": ("점프", "버피"),
            },
        },
        {
            "case_id": "api_extrovert_consistency_beginner",
            "source": "chat_api",
            "profile": _profile(
                age=41,
                gender="male",
                weight=79,
                social_orientation="외향형",
                goal="consistency",
                exercise_level="beginner",
                exercise_frequency=2,
                available_time_minutes=15,
                lifestyle="운동 실패 경험이 많아 낮은 부담 선호",
            ),
            "expected": {
                "orientation": "extrovert",
                "goal": "consistency",
                "first_category": "stretching",
                "max_sets": 2,
                "max_duration": 15,
                "frequency": 2,
            },
        },
        {
            "case_id": "api_introvert_knee_fat_loss",
            "source": "chat_api",
            "profile": _profile(
                age=52,
                gender="female",
                weight=92,
                social_orientation="introvert",
                goal="weight_loss",
                exercise_level="beginner",
                exercise_frequency=3,
                available_time_minutes=20,
                injury_history=["knee osteoarthritis"],
                pain_points=["무릎"],
                lifestyle="헬스장보다 집에서 운동",
            ),
            "expected": {
                "orientation": "introvert",
                "goal": "fat_loss",
                "first_category": "cardio",
                "max_sets": 2,
                "max_duration": 20,
                "frequency": 3,
                "constraints": ("무릎", "knee osteoarthritis"),
                "forbidden": ("점프", "버피", "깊은 스쿼트"),
                "home_cardio": True,
            },
        },
        {
            "case_id": "home_introvert_fat_loss",
            "source": "home_service",
            "profile": _profile(
                social_orientation="내향형",
                goal="fat_loss",
                exercise_level="beginner",
                exercise_frequency=3,
                available_time_minutes=25,
            ),
            "expected": {
                "orientation": "introvert",
                "goal": "fat_loss",
                "home_cardio": True,
                "min_cardio_duration": 25,
            },
        },
        {
            "case_id": "home_extrovert_fat_loss",
            "source": "home_service",
            "profile": _profile(
                social_orientation="외향형",
                goal="fat_loss",
                exercise_level="intermediate",
                exercise_frequency=4,
                available_time_minutes=30,
            ),
            "expected": {
                "orientation": "extrovert",
                "goal": "fat_loss",
                "min_cardio_duration": 25,
            },
        },
    ]


async def _run_chat_request(client: httpx.AsyncClient, *, profile: dict[str, Any]) -> dict[str, Any]:
    response = await client.post(
        "/chat",
        json={
            "user_id": f"workout-accuracy-{uuid.uuid4().hex[:8]}",
            "user_message": "오늘 운동 계획 짜줘",
            "user_profile_override": profile,
        },
        headers={"x-api-key": os.environ["INTERNAL_API_KEY"]},
    )
    body = response.json()
    if response.status_code != 200:
        raise AssertionError(f"HTTP {response.status_code}: {body}")
    return body


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


def _item_text(item: dict[str, Any]) -> str:
    return _flatten_text(
        [
            item.get("name"),
            item.get("detail"),
            [exercise.get("exercise_name") for exercise in item.get("ex_list") or [] if isinstance(exercise, dict)],
        ]
    )


def _category_of_item(item: dict[str, Any]) -> str | None:
    name = str(item.get("name") or "").lower()
    for category, label in CATEGORY_LABELS.items():
        if label.lower() in name:
            return category
    text = _item_text(item).lower()
    scores = {
        category: sum(1 for marker in markers if marker.lower() in text)
        for category, markers in CATEGORY_MARKERS.items()
    }
    best = max(scores.values() or [0])
    if best <= 0:
        return None
    winners = [category for category, score in scores.items() if score == best]
    return winners[0] if len(winners) == 1 else None


def _category_positions(plan: list[dict[str, Any]]) -> dict[str, int | None]:
    positions = dict.fromkeys(CATEGORIES, None)
    for index, item in enumerate(plan):
        category = _category_of_item(item)
        if category and positions[category] is None:
            positions[category] = index
    return positions


def _category_item(plan: list[dict[str, Any]], category: str) -> dict[str, Any] | None:
    for item in plan:
        if _category_of_item(item) == category:
            return item
    return None


def _has_any(text: str, markers: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in markers)


def _exercise_numbers(plan: list[dict[str, Any]], key: str) -> list[int]:
    values: list[int] = []
    for item in plan:
        for exercise in item.get("ex_list") or []:
            if not isinstance(exercise, dict):
                continue
            value = exercise.get(key)
            if isinstance(value, int):
                values.append(value)
    return values


def _frequency_reflected(text: str, expected: dict[str, Any]) -> bool:
    frequency = expected.get("frequency")
    if not frequency:
        return True
    compact = re.sub(r"\s+", "", text)
    return f"주{frequency}회" in compact


def _score_chat_case(case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    expected = case["expected"]
    debug = response.get("debug_state") or {}
    plan = debug.get("proposed_plan") or []
    plan_text = _flatten_text(plan)
    full_text = f"{response.get('response') or ''} {plan_text}"
    positions = _category_positions(plan)
    first_category = min(
        (category for category in CATEGORIES if positions.get(category) is not None),
        key=lambda category: positions[category] if positions[category] is not None else 999,
        default=None,
    )
    cardio_item = _category_item(plan, "cardio")
    cardio_text = _item_text(cardio_item or {})

    checks = {
        "routed_to_workout_plan": bool(plan)
        and debug.get("action_intent") == "create"
        and debug.get("domain") == "workout"
        and debug.get("proposed_plan_type") == "workout",
        "four_category_coverage": all(positions.get(category) is not None for category in CATEGORIES),
        "goal_priority": first_category == expected.get("first_category"),
        "social_orientation_fit": _orientation_fit(full_text, cardio_text, expected),
        "goal_marker_fit": _goal_marker_fit(full_text, expected),
        "level_time_frequency_fit": _level_time_frequency_fit(plan, full_text, expected),
        "constraint_fit": _constraint_fit(full_text, expected, plan),
    }
    return _case_evaluation(case, checks, response, plan=plan, positions=positions)


def _score_home_case(case: dict[str, Any]) -> dict[str, Any]:
    expected = case["expected"]
    result = empty_home_recommendations(
        date=kst_today_iso(),
        scope="workout",
        user_profile=case["profile"],
        today_plan=[],
        recent_recommendations={},
    )
    workout = result.workout
    slots = {
        "upper_body": workout.upper_body,
        "lower_body": workout.lower_body,
        "cardio": workout.cardio,
        "stretching": workout.stretching,
    }
    slot_text = _flatten_text([item.model_dump() for item in slots.values() if item])
    cardio = workout.cardio
    cardio_text = _flatten_text(cardio.model_dump() if cardio else {})
    checks = {
        "four_category_coverage": all(slots.values()),
        "social_orientation_fit": _orientation_fit(slot_text, cardio_text, expected),
        "goal_marker_fit": _goal_marker_fit(slot_text, expected),
        "home_cardio_duration_fit": bool(cardio)
        and int(cardio.duration_minutes or 0) >= int(expected.get("min_cardio_duration") or 0),
    }
    payload = {
        "home_workout": {key: value.model_dump() if value else None for key, value in slots.items()},
    }
    return _case_evaluation(case, checks, payload, plan=[], positions={})


def _orientation_fit(full_text: str, cardio_text: str, expected: dict[str, Any]) -> bool:
    orientation = expected.get("orientation")
    if orientation == "introvert":
        if expected.get("home_cardio") and not _has_any(cardio_text, INTROVERT_MARKERS):
            return False
        return _has_any(full_text, INTROVERT_MARKERS)
    if orientation == "extrovert":
        return _has_any(full_text, EXTROVERT_MARKERS)
    return True


def _goal_marker_fit(full_text: str, expected: dict[str, Any]) -> bool:
    goal = expected.get("goal")
    if goal == "fat_loss":
        return _has_any(full_text, FAT_LOSS_MARKERS)
    if goal == "muscle_gain":
        return _has_any(full_text, MUSCLE_MARKERS)
    if goal == "mobility":
        return _has_any(full_text, MOBILITY_MARKERS)
    if goal == "consistency":
        return _has_any(full_text, CONSISTENCY_MARKERS)
    return True


def _level_time_frequency_fit(plan: list[dict[str, Any]], full_text: str, expected: dict[str, Any]) -> bool:
    sets = _exercise_numbers(plan, "sets")
    durations = _exercise_numbers(plan, "duration_minutes")
    max_sets = expected.get("max_sets")
    max_duration = expected.get("max_duration")
    if max_sets is not None and sets and max(sets) > int(max_sets):
        return False
    if max_duration is not None and durations and max(durations) > int(max_duration):
        return False
    return _frequency_reflected(full_text, expected)


def _constraint_fit(full_text: str, expected: dict[str, Any], plan: list[dict[str, Any]] | None = None) -> bool:
    constraints = tuple(expected.get("constraints") or ())
    forbidden = tuple(expected.get("forbidden") or ())
    if constraints and not any(token.lower() in full_text.lower() for token in constraints):
        return False
    exercise_names = _flatten_text(
        [
            exercise.get("exercise_name")
            for item in plan or []
            for exercise in item.get("ex_list") or []
            if isinstance(exercise, dict)
        ]
    ).lower()
    if forbidden and any(token.lower() in exercise_names for token in forbidden):
        return False
    return True


def _case_evaluation(
    case: dict[str, Any],
    checks: dict[str, bool],
    payload: dict[str, Any],
    *,
    plan: list[dict[str, Any]],
    positions: dict[str, int | None],
) -> dict[str, Any]:
    passed = sum(1 for value in checks.values() if value)
    score = round(passed / len(checks), 3)
    grade = "pass" if score >= 0.9 else "review" if score >= 0.75 else "fail"
    return {
        "case_id": case["case_id"],
        "source": case["source"],
        "score": score,
        "grade": grade,
        "checks": checks,
        "failed_checks": [key for key, value in checks.items() if not value],
        "category_positions": {
            CATEGORY_LABELS.get(category, category): position for category, position in positions.items()
        },
        "plan_preview": plan,
        "response_debug": payload.get("debug_state"),
        "response_text": payload.get("response"),
        "home_workout": payload.get("home_workout"),
    }


async def run_suite() -> dict[str, Any]:
    cases = workout_profile_cases()
    evaluations: list[dict[str, Any]] = []
    app, _graph, _deps, _fake_was, checkpointer = await build_test_stack()
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            for case in cases:
                if case["source"] == "chat_api":
                    response = await _run_chat_request(client, profile=case["profile"])
                    evaluations.append(_score_chat_case(case, response))
                else:
                    evaluations.append(_score_home_case(case))
    finally:
        await checkpointer.conn.close()
        app.state._temp_dir.cleanup()

    criterion_totals: dict[str, list[int]] = {}
    for evaluation in evaluations:
        for key, passed in evaluation["checks"].items():
            criterion_totals.setdefault(key, []).append(1 if passed else 0)
    summary = {
        "case_count": len(evaluations),
        "overall_average": round(statistics.mean(item["score"] for item in evaluations), 3),
        "pass_count": sum(1 for item in evaluations if item["grade"] == "pass"),
        "review_count": sum(1 for item in evaluations if item["grade"] == "review"),
        "fail_count": sum(1 for item in evaluations if item["grade"] == "fail"),
        "criterion_pass_rate": {
            key: round(statistics.mean(values), 3) for key, values in sorted(criterion_totals.items())
        },
    }
    return {
        "runner": Path(__file__).name,
        "summary": summary,
        "cases": evaluations,
    }


def write_report(report: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Workout Profile Goal Accuracy Report",
        "",
        f"- Runner: `{report['runner']}`",
        f"- Cases: {report['summary']['case_count']}",
        f"- Overall average: {report['summary']['overall_average']}",
        f"- Pass/Review/Fail: {report['summary']['pass_count']}/{report['summary']['review_count']}/{report['summary']['fail_count']}",
        "",
        "## Criterion Pass Rate",
        "",
    ]
    for key, score in report["summary"]["criterion_pass_rate"].items():
        lines.append(f"- {key}: {score}")
    lines.extend(["", "## Case Details", ""])
    for case in report["cases"]:
        failed = ", ".join(case["failed_checks"]) or "none"
        lines.append(f"### {case['case_id']} / {case['source']} / {case['grade']} ({case['score']})")
        lines.append(f"- Failed checks: {failed}")
        if case["category_positions"]:
            lines.append(f"- Category positions: `{json.dumps(case['category_positions'], ensure_ascii=False)}`")
        lines.append("")
    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


async def main() -> None:
    report = await run_suite()
    write_report(report)
    print("[workout-profile-goal-accuracy] report json:", REPORT_JSON_PATH)
    print("[workout-profile-goal-accuracy] report md:", REPORT_MD_PATH)
    print("[workout-profile-goal-accuracy] summary:", json.dumps(report["summary"], ensure_ascii=False))
    if report["summary"]["fail_count"] or report["summary"]["review_count"]:
        failed = [
            {"case_id": item["case_id"], "grade": item["grade"], "failed_checks": item["failed_checks"]}
            for item in report["cases"]
            if item["grade"] != "pass"
        ]
        raise AssertionError(json.dumps(failed, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
