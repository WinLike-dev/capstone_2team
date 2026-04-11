"""Shared helpers for home-tab recommendation generation."""
from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.schemas.home import (
    DietRecommendationItem,
    DietRecommendationSlots,
    HomeRecommendationResponse,
    HomeRecommendationScope,
    WorkoutRecommendationItem,
    WorkoutRecommendationSlots,
)

KST = ZoneInfo("Asia/Seoul")
WORKOUT_SLOTS = ("upper_body", "lower_body", "cardio", "stretching")
DIET_SLOTS = ("breakfast", "lunch", "dinner")
PROMPT_PATH = "home/recommendations.md"


def kst_today_iso() -> str:
    return datetime.now(KST).date().isoformat()


def build_home_recommendation_prompt_input(
    *,
    date: str,
    scope: HomeRecommendationScope,
    user_profile: dict,
    today_plan: list[dict],
) -> str:
    today_exercise_names: list[str] = []
    today_meal_names: list[str] = []
    workout_by_slot = {slot: [] for slot in WORKOUT_SLOTS}
    diet_by_slot = {slot: [] for slot in DIET_SLOTS}

    for item in today_plan or []:
        item_type = str(item.get("type") or "").strip().lower()
        slot_name = str(item.get("name") or "").strip().lower()
        detail = str(item.get("detail") or "").strip()
        if not detail:
            continue

        if item_type == "exercise":
            today_exercise_names.append(detail)
            if slot_name in workout_by_slot:
                workout_by_slot[slot_name].append(detail)
            continue

        if item_type == "meal":
            today_meal_names.append(detail)
            if slot_name in diet_by_slot:
                diet_by_slot[slot_name].append(detail)

    profile = {
        "goal": user_profile.get("goal"),
        "activity_level": user_profile.get("activity_level"),
        "diet_type": user_profile.get("diet_type"),
        "allergies": user_profile.get("allergies") or [],
        "injury_history": user_profile.get("injury_history") or [],
        "age": user_profile.get("age"),
        "gender": user_profile.get("gender"),
        "weight": user_profile.get("weight"),
        "height": user_profile.get("height"),
    }

    return "\n\n".join(
        [
            f"[DATE]\n{date}",
            f"[SCOPE]\n{scope}",
            f"[USER_PROFILE]\n{json.dumps(profile, ensure_ascii=False)}",
            f"[TODAY_EXERCISE_EXCLUDE]\n{json.dumps(today_exercise_names, ensure_ascii=False)}",
            f"[TODAY_DIET_EXCLUDE]\n{json.dumps(today_meal_names, ensure_ascii=False)}",
            f"[TODAY_EXERCISE_BY_SLOT]\n{json.dumps(workout_by_slot, ensure_ascii=False)}",
            f"[TODAY_DIET_BY_SLOT]\n{json.dumps(diet_by_slot, ensure_ascii=False)}",
        ]
    )


def normalize_home_recommendations(
    response: HomeRecommendationResponse,
    *,
    scope: HomeRecommendationScope,
    date: str,
) -> HomeRecommendationResponse:
    workout = WorkoutRecommendationSlots(
        upper_body=_normalize_workout_item("upper_body", response.workout.upper_body),
        lower_body=_normalize_workout_item("lower_body", response.workout.lower_body),
        cardio=_normalize_workout_item("cardio", response.workout.cardio),
        stretching=_normalize_workout_item("stretching", response.workout.stretching),
    )
    diet = DietRecommendationSlots(
        breakfast=_normalize_diet_item(response.diet.breakfast),
        lunch=_normalize_diet_item(response.diet.lunch),
        dinner=_normalize_diet_item(response.diet.dinner),
    )

    if scope == "workout":
        diet = DietRecommendationSlots()
    elif scope == "diet":
        workout = WorkoutRecommendationSlots()

    return HomeRecommendationResponse(
        date=date,
        scope=scope,
        workout=workout,
        diet=diet,
    )


def empty_home_recommendations(
    *,
    date: str,
    scope: HomeRecommendationScope,
) -> HomeRecommendationResponse:
    response = HomeRecommendationResponse(date=date, scope=scope)
    if scope == "workout":
        response.diet = DietRecommendationSlots()
    elif scope == "diet":
        response.workout = WorkoutRecommendationSlots()
    return response


def _normalize_workout_item(
    slot: str,
    item: WorkoutRecommendationItem | None,
) -> WorkoutRecommendationItem | None:
    if item is None:
        return None

    exercise_name = item.exercise_name.strip()
    if not exercise_name:
        return None

    calories = max(0, int(item.calories or 0))
    summary = item.summary.strip()

    if slot == "cardio":
        duration_minutes = int(item.duration_minutes or 20)
        return WorkoutRecommendationItem(
            exercise_name=exercise_name,
            summary=summary,
            sets=None,
            duration_minutes=max(1, duration_minutes),
            calories=calories,
        )

    sets = int(item.sets or 3)
    return WorkoutRecommendationItem(
        exercise_name=exercise_name,
        summary=summary,
        sets=max(1, sets),
        duration_minutes=None,
        calories=calories,
    )


def _normalize_diet_item(item: DietRecommendationItem | None) -> DietRecommendationItem | None:
    if item is None:
        return None

    food_name = item.food_name.strip()
    if not food_name:
        return None

    return DietRecommendationItem(
        food_name=food_name,
        summary=item.summary.strip(),
        calories=max(0, int(item.calories or 0)),
    )
