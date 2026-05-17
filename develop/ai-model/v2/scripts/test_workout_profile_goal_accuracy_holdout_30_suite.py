from __future__ import annotations

import asyncio
import json
import os
import re
import statistics
import sys
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
os.environ.setdefault("CHECKPOINT_DB_PATH", str(ROOT / "data" / "workout_profile_goal_accuracy_holdout_30.sqlite"))

from app.core import config as app_config  # noqa: E402

app_config.Settings.model_config = {"env_file": None}
app_config.get_settings.cache_clear()

from scripts.test_chat_e2e import build_test_stack  # noqa: E402
from scripts.test_workout_profile_goal_accuracy_suite import (  # noqa: E402
    CATEGORY_LABELS,
    _exercise_numbers,
    _flatten_text,
    _profile,
    _run_chat_request,
    _score_chat_case,
)

DATA_DIR = ROOT / "data"
REPORT_DIR = ROOT / "docs" / "quality"
PROFILE_DATA_PATH = DATA_DIR / "workout_profile_goal_holdout_profiles_30.json"
REPORT_JSON_PATH = REPORT_DIR / "workout_profile_goal_accuracy_holdout_30_report.json"
REPORT_MD_PATH = REPORT_DIR / "workout_profile_goal_accuracy_holdout_30_report.md"


def build_holdout_cases() -> list[dict[str, Any]]:
    raw = [
        ("h01", 24, "female", 70, "beginner", "fat_loss", "내향형", 12, 2, "재택근무 후 방에서 짧게 운동", [], [], [], "cardio", 2, 12, True, (), ()),
        ("h02", 35, "male", 88, "intermediate", "fat_loss", "외향형", 30, 4, "회사 동료와 운동 챌린지 선호", [], [], [], "cardio", 3, None, False, (), ()),
        ("h03", 29, "male", 74, "advanced", "muscle_gain", "introvert", 50, 5, "홈짐에서 혼자 근력 운동", [], [], [], "upper_body", 4, None, False, (), ()),
        ("h04", 43, "female", 67, "advanced", "strength", "extroverted", 45, 5, "그룹 PT와 수업을 선호", [], [], [], "upper_body", 4, None, False, (), ()),
        ("h05", 68, "female", 61, "beginner", "mobility", "내향형", 15, 3, "집에서 균형감 있게 천천히", ["knee osteoarthritis"], [], ["무릎"], "stretching", 2, 15, False, ("무릎", "knee osteoarthritis"), ("점프", "버피", "깊은 스쿼트")),
        ("h06", 55, "male", 90, "beginner", "health", "외향형", 20, 3, "고혈압 관리와 산책 모임", [], ["hypertension"], [], "stretching", 2, 20, False, ("hypertension",), ("전력질주", "버피")),
        ("h07", 31, "nonbinary", 64, "beginner", "consistency", "혼자 운동 선호", 10, 2, "운동을 자주 포기해서 낮은 기준 필요", [], [], [], "stretching", 2, 10, False, (), ()),
        ("h08", 26, "female", 59, "intermediate", "habit", "group workout", 25, 3, "친구와 꾸준히 하는 습관 만들기", [], [], [], "stretching", 3, None, False, (), ()),
        ("h09", 47, "male", 95, "beginner", "weight_loss", "I", 18, 3, "헬스장보다 거실 운동", ["knee pain"], [], ["무릎"], "cardio", 2, 18, True, ("무릎", "knee pain"), ("점프", "버피", "깊은 스쿼트")),
        ("h10", 39, "female", 80, "intermediate", "fat_loss", "E", 25, 4, "걷기 모임은 좋지만 발목 부담 있음", ["ankle sprain"], [], ["발목"], "cardio", 2, 20, False, ("발목", "ankle sprain"), ("점프", "버피", "전력질주")),
        ("h11", 34, "male", 72, "intermediate", "muscle_gain", "quiet solo routine", 35, 4, "어깨 충돌 증후군 이후 홈트", ["shoulder impingement"], [], ["어깨"], "upper_body", 2, 20, False, ("어깨", "shoulder impingement"), ("숄더프레스", "오버헤드프레스")),
        ("h12", 30, "female", 58, "advanced", "strength", "social", 40, 5, "수업은 좋아하지만 손목 통증 있음", ["wrist pain"], [], ["손목"], "upper_body", 2, 20, False, ("손목", "wrist pain"), ("버피", "물구나무")),
        ("h13", 50, "female", 66, "beginner", "health", "내향형", 15, 3, "오래 앉아 일하고 허리 뻐근함", ["lower back pain"], [], ["허리"], "stretching", 2, 15, False, ("허리", "lower back pain"), ("점프", "버피")),
        ("h14", 72, "male", 70, "beginner", "mobility", "외향형", 12, 2, "복지관 운동 친구는 있지만 고관절 이력", ["hip replacement"], ["hypertension"], ["고관절"], "stretching", 2, 12, False, ("고관절", "hip replacement"), ("깊은 런지", "점프")),
        ("h15", 22, "female", 49, "beginner", "fat_loss", "introverted", 20, 3, "사진 촬영 전 감량 불안감", [], [], [], "cardio", 2, 20, True, (), ("굶기", "단식")),
        ("h16", 44, "male", 103, "advanced", "fat_loss", "외향형", 35, 5, "동호회와 체중 감량 도전", [], [], [], "cardio", 4, None, False, (), ("점프", "버피")),
        ("h17", 27, "female", 55, "beginner", "muscle_gain", "내향형", 25, 3, "집에서 덤벨로 근육 만들기", [], [], [], "upper_body", 2, None, False, (), ()),
        ("h18", 33, "male", 78, "beginner", "strength", "외향형", 20, 2, "친구와 주 2회 운동", [], [], [], "upper_body", 2, 20, False, (), ()),
        ("h19", 52, "female", 84, "beginner", "glucose_control", "introvert", 20, 4, "혈당 관리와 저녁 홈트", [], ["type 2 diabetes"], [], "stretching", 2, 20, False, ("type 2 diabetes",), ("단식", "전력질주")),
        ("h20", 60, "male", 82, "beginner", "heart_health", "extrovert", 15, 3, "가벼운 운동은 허가받았지만 심장 질환 있음", [], ["heart disease"], [], "stretching", 2, 15, False, ("heart disease",), ("최대심박", "전력")),
        ("h21", 45, "female", 89, "beginner", "habit", "혼자 조용히", 8, 2, "돌봄 때문에 8분 단위만 가능", [], [], [], "stretching", 2, 8, False, (), ()),
        ("h22", 38, "male", 76, "intermediate", "consistency", "함께 운동 선호", 20, 3, "운동 모임에 맞춘 지속 루틴", [], [], [], "stretching", 3, 20, False, (), ()),
        ("h23", 36, "female", 77, "intermediate", "fat_loss", "solo home workout", 25, 4, "허리 부담 때문에 집에서 감량 운동", ["back strain"], [], ["허리"], "cardio", 2, 20, True, ("허리", "back strain"), ("점프", "버피")),
        ("h24", 66, "female", 87, "beginner", "weight_loss", "외향형", 20, 3, "친구와 걷고 싶지만 무릎 부담 있음", ["knee osteoarthritis"], [], ["무릎"], "cardio", 2, 20, False, ("무릎", "knee osteoarthritis"), ("점프", "버피", "깊은 스쿼트")),
        ("h25", 40, "male", 69, "intermediate", "mobility", "introvert", 30, 4, "손목 부담 없는 가동성 루틴", ["wrist pain"], [], ["손목"], "stretching", 2, 20, False, ("손목", "wrist pain"), ("물구나무", "버피")),
        ("h26", 25, "female", 60, "intermediate", "health", "extrovert", 35, 4, "어깨가 아파도 수업 분위기는 좋아함", ["shoulder pain"], [], ["어깨"], "stretching", 2, 20, False, ("어깨", "shoulder pain"), ("숄더프레스", "오버헤드프레스")),
        ("h27", 65, "male", 71, "advanced", "muscle_gain", "내향형", 20, 3, "혼자 하되 나이에 맞게 근력 유지", [], [], [], "upper_body", 2, 20, False, (), ()),
        ("h28", 23, "female", 63, "advanced", "strength", "외향형", 60, 6, "동아리 운동을 주 6회 진행", [], [], [], "upper_body", 4, None, False, (), ()),
        ("h29", 34, "female", 82, "beginner", "diet", "내향형", 10, 2, "육아 후 10분 홈트로 감량", [], [], [], "cardio", 2, 10, True, (), ()),
        ("h30", 70, "female", 65, "beginner", "health", "외향형", 10, 2, "복지관 친구는 좋지만 어지럼 이력", ["vertigo history"], [], ["어지럼"], "stretching", 2, 10, False, ("어지럼", "vertigo history"), ("눈감고 균형", "빠른 회전")),
    ]

    cases: list[dict[str, Any]] = []
    for (
        case_id,
        age,
        gender,
        weight,
        level,
        goal,
        orientation,
        available,
        frequency,
        lifestyle,
        injuries,
        conditions,
        pains,
        first_category,
        max_sets,
        max_duration,
        home_cardio,
        constraints,
        forbidden,
    ) in raw:
        expected_goal = _expected_goal(goal)
        cases.append(
            {
                "case_id": case_id,
                "source": "chat_api",
                "profile": _profile(
                    age=age,
                    gender=gender,
                    weight=weight,
                    exercise_level=level,
                    activity_level="low" if level == "beginner" else "high" if level == "advanced" else "moderate",
                    goal=goal,
                    social_orientation=orientation,
                    available_time_minutes=available,
                    exercise_frequency=frequency,
                    lifestyle=lifestyle,
                    injury_history=injuries,
                    medical_conditions=conditions,
                    pain_points=pains,
                ),
                "expected": {
                    "orientation": _expected_orientation(orientation),
                    "goal": expected_goal,
                    "first_category": first_category,
                    "max_sets": max_sets,
                    "max_duration": max_duration,
                    "frequency": frequency,
                    "home_cardio": home_cardio,
                    "constraints": constraints,
                    "forbidden": forbidden,
                },
            }
        )
    return cases


def _expected_goal(goal: str) -> str:
    lowered = goal.lower()
    if any(marker in lowered for marker in ("fat_loss", "weight_loss", "diet")):
        return "fat_loss"
    if any(marker in lowered for marker in ("muscle", "strength")):
        return "muscle_gain"
    if any(marker in lowered for marker in ("mobility", "health", "glucose")):
        return "mobility"
    return "consistency"


def _expected_orientation(value: str) -> str:
    lowered = value.lower()
    if lowered.strip() == "e":
        return "extrovert"
    if any(marker in lowered for marker in ("외향", "extro", "social", "group", "함께")) and "intro" not in lowered:
        return "extrovert"
    return "introvert"


def write_holdout_profiles(cases: list[dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "case_id": case["case_id"],
            "profile": case["profile"],
            "expected": case["expected"],
        }
        for case in cases
    ]
    PROFILE_DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _profile_signal_fit(case: dict[str, Any], response: dict[str, Any]) -> bool:
    profile = case["profile"]
    expected = case["expected"]
    debug = response.get("debug_state") or {}
    plan = debug.get("proposed_plan") or []
    full_text = _flatten_text([response.get("response"), plan])
    compact = _compact(full_text)
    sets = _exercise_numbers(plan, "sets")
    durations = _exercise_numbers(plan, "duration_minutes")

    available = profile.get("available_time_minutes")
    if available:
        within_duration = not durations or max(durations) <= int(expected.get("max_duration") or available or max(durations))
        if f"가능시간{available}분" not in compact and not within_duration:
            return False

    frequency = profile.get("exercise_frequency")
    if frequency and f"주{frequency}회" not in compact:
        return False

    level = str(profile.get("exercise_level") or "").lower()
    if "beginner" in level and not ("초보자" in full_text or "저강도" in full_text):
        return False
    if "intermediate" in level and not ("중급자" in full_text or "기본 볼륨" in full_text):
        return False
    if "advanced" in level and int(profile.get("age") or 0) < 65 and not ("숙련자" in full_text or "강도는 유지" in full_text):
        return False

    age = int(profile.get("age") or 0)
    if age >= 65 and (sets and max(sets) > 2):
        return False

    weight = int(profile.get("weight") or 0)
    if weight >= 90 and not ("체중 부담" in full_text or "저충격" in full_text):
        return False
    if weight <= 50 and expected.get("goal") == "fat_loss" and not ("낮은 체중" in full_text or "굶기" in full_text):
        return False

    return True


def _safety_fit(case: dict[str, Any], response: dict[str, Any]) -> bool:
    profile = case["profile"]
    full_text = _flatten_text([response.get("response"), (response.get("debug_state") or {}).get("proposed_plan")])
    has_physical_constraint = bool(
        (profile.get("injury_history") or [])
        or (profile.get("pain_points") or [])
        or (profile.get("medical_conditions") or [])
    )
    if not has_physical_constraint:
        return True
    if profile.get("injury_history") or profile.get("pain_points"):
        if not ("통증" in full_text and ("중단" in full_text or "낮추" in full_text)):
            return False
    if profile.get("medical_conditions"):
        if not ("전문가 상담" in full_text or "질환 정보" in full_text):
            return False
    return True


def _score_holdout_case(case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    evaluation = _score_chat_case(case, response)
    checks = dict(evaluation["checks"])
    checks["profile_signal_fit"] = _profile_signal_fit(case, response)
    checks["safety_fit"] = _safety_fit(case, response)
    passed = sum(1 for value in checks.values() if value)
    score = round(passed / len(checks), 3)
    evaluation["checks"] = checks
    evaluation["score"] = score
    evaluation["grade"] = "pass" if score >= 0.9 else "review" if score >= 0.75 else "fail"
    evaluation["failed_checks"] = [key for key, value in checks.items() if not value]
    evaluation["profile"] = case["profile"]
    evaluation["expected"] = case["expected"]
    return evaluation


async def run_suite() -> dict[str, Any]:
    cases = build_holdout_cases()
    write_holdout_profiles(cases)
    evaluations: list[dict[str, Any]] = []
    app, _graph, _deps, _fake_was, checkpointer = await build_test_stack()
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            for case in cases:
                response = await _run_chat_request(client, profile=case["profile"])
                evaluations.append(_score_holdout_case(case, response))
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
        "goal_distribution": _distribution(item["expected"]["goal"] for item in evaluations),
        "orientation_distribution": _distribution(item["expected"]["orientation"] for item in evaluations),
    }
    return {
        "runner": Path(__file__).name,
        "profile_data": str(PROFILE_DATA_PATH),
        "summary": summary,
        "cases": evaluations,
    }


def _distribution(values: Any) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        result[str(value)] = result.get(str(value), 0) + 1
    return result


def write_report(report: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Workout Profile Goal Accuracy Holdout 30 Report",
        "",
        f"- Runner: `{report['runner']}`",
        f"- Profile data: `{report['profile_data']}`",
        f"- Cases: {report['summary']['case_count']}",
        f"- Overall average: {report['summary']['overall_average']}",
        f"- Pass/Review/Fail: {report['summary']['pass_count']}/{report['summary']['review_count']}/{report['summary']['fail_count']}",
        f"- Goal distribution: `{json.dumps(report['summary']['goal_distribution'], ensure_ascii=False)}`",
        f"- Orientation distribution: `{json.dumps(report['summary']['orientation_distribution'], ensure_ascii=False)}`",
        "",
        "## Criterion Pass Rate",
        "",
    ]
    for key, score in report["summary"]["criterion_pass_rate"].items():
        lines.append(f"- {key}: {score}")
    lines.extend(["", "## Case Details", ""])
    for case in report["cases"]:
        failed = ", ".join(case["failed_checks"]) or "none"
        expected = case["expected"]
        profile = case["profile"]
        positions = {
            CATEGORY_LABELS.get(category, category): position
            for category, position in (case.get("category_positions") or {}).items()
        }
        lines.append(f"### {case['case_id']} / {case['grade']} ({case['score']})")
        lines.append(
            f"- Profile: {profile.get('age')}세, {profile.get('gender')}, {profile.get('weight')}kg, "
            f"{profile.get('exercise_level')}, {profile.get('goal')}, {profile.get('social_orientation')}, "
            f"주 {profile.get('exercise_frequency')}회, {profile.get('available_time_minutes')}분"
        )
        lines.append(
            f"- Expected: orientation={expected.get('orientation')}, goal={expected.get('goal')}, first={expected.get('first_category')}"
        )
        lines.append(f"- Failed checks: {failed}")
        if positions:
            lines.append(f"- Category positions: `{json.dumps(positions, ensure_ascii=False)}`")
        lines.append("")
    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


async def main() -> None:
    report = await run_suite()
    write_report(report)
    print("[workout-profile-goal-holdout-30] profiles:", PROFILE_DATA_PATH)
    print("[workout-profile-goal-holdout-30] report json:", REPORT_JSON_PATH)
    print("[workout-profile-goal-holdout-30] report md:", REPORT_MD_PATH)
    print("[workout-profile-goal-holdout-30] summary:", json.dumps(report["summary"], ensure_ascii=False))
    if report["summary"]["fail_count"] or report["summary"]["review_count"]:
        failed = [
            {"case_id": item["case_id"], "grade": item["grade"], "failed_checks": item["failed_checks"]}
            for item in report["cases"]
            if item["grade"] != "pass"
        ]
        raise AssertionError(json.dumps(failed, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
