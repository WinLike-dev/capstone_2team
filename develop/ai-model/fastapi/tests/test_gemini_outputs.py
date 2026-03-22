"""gemini_outputs.py 스키마 유닛 테스트 (TDD RED phase).

검증 항목:
  1. SimpleAnswerOutput — 모드 1 기본 응답 스키마
  2. ExercisePlanItem / ExercisePlanOutput — 모드 2, 3 운동 계획
  3. MealPlanItem / MealPlanOutput — 모드 4, 5 식단 계획
  4. UserDbUpdateOutput — 모드 6 프로필 업데이트
  5. MealLogOutput — 모드 7 식사 기록 분석
  6. RecommendationExercise / RecommendationMeal / RecommendationOutput — 모드 8 추천
  7. 각 스키마의 JSON 직렬화/역직렬화 라운드트립
"""

import json

import pytest

from app.schemas.gemini_outputs import (
    ExercisePlanItem,
    ExercisePlanOutput,
    MealLogOutput,
    MealPlanItem,
    MealPlanOutput,
    RecommendationExercise,
    RecommendationMeal,
    RecommendationOutput,
    SimpleAnswerOutput,
    UserDbUpdateOutput,
)


# ---------------------------------------------------------------------------
# Test 1: SimpleAnswerOutput (모드 1)
# ---------------------------------------------------------------------------


def test_simple_answer_output_instantiation():
    """SimpleAnswerOutput은 answer 필드로 인스턴스화된다."""
    obj = SimpleAnswerOutput(answer="안녕하세요!")
    assert obj.answer == "안녕하세요!"


def test_simple_answer_output_roundtrip():
    """SimpleAnswerOutput JSON 직렬화/역직렬화 라운드트립."""
    original = SimpleAnswerOutput(answer="테스트 답변")
    json_str = original.model_dump_json()
    restored = SimpleAnswerOutput.model_validate_json(json_str)
    assert restored.answer == original.answer


# ---------------------------------------------------------------------------
# Test 2: ExercisePlanItem / ExercisePlanOutput (모드 2, 3)
# ---------------------------------------------------------------------------


def test_exercise_plan_item_instantiation():
    """ExercisePlanItem은 date, type, detail, count 필드로 인스턴스화된다."""
    item = ExercisePlanItem(
        date="2026-03-22",
        type="유산소",
        detail="러닝",
        count="30분",
    )
    assert item.date == "2026-03-22"
    assert item.type == "유산소"
    assert item.detail == "러닝"
    assert item.count == "30분"


def test_exercise_plan_output_instantiation():
    """ExercisePlanOutput은 items: list[ExercisePlanItem] wrapper이다."""
    items = [
        ExercisePlanItem(date="2026-03-22", type="유산소", detail="러닝", count="30분"),
        ExercisePlanItem(date="2026-03-23", type="근력", detail="스쿼트", count="3세트"),
    ]
    output = ExercisePlanOutput(items=items)
    assert len(output.items) == 2
    assert output.items[0].detail == "러닝"


def test_exercise_plan_output_roundtrip():
    """ExercisePlanOutput JSON 직렬화/역직렬화 라운드트립."""
    original = ExercisePlanOutput(
        items=[ExercisePlanItem(date="2026-03-22", type="근력", detail="데드리프트", count="5회")]
    )
    json_str = original.model_dump_json()
    restored = ExercisePlanOutput.model_validate_json(json_str)
    assert len(restored.items) == 1
    assert restored.items[0].detail == "데드리프트"


# ---------------------------------------------------------------------------
# Test 3: MealPlanItem / MealPlanOutput (모드 4, 5)
# ---------------------------------------------------------------------------


def test_meal_plan_item_instantiation():
    """MealPlanItem은 date, food, time 필드로 인스턴스화된다."""
    item = MealPlanItem(date="2026-03-22", food="닭가슴살 샐러드", time="12:00")
    assert item.date == "2026-03-22"
    assert item.food == "닭가슴살 샐러드"
    assert item.time == "12:00"


def test_meal_plan_output_instantiation():
    """MealPlanOutput은 items: list[MealPlanItem] wrapper이다."""
    output = MealPlanOutput(
        items=[
            MealPlanItem(date="2026-03-22", food="오트밀", time="08:00"),
            MealPlanItem(date="2026-03-22", food="닭가슴살", time="12:00"),
        ]
    )
    assert len(output.items) == 2
    assert output.items[1].food == "닭가슴살"


def test_meal_plan_output_roundtrip():
    """MealPlanOutput JSON 직렬화/역직렬화 라운드트립."""
    original = MealPlanOutput(
        items=[MealPlanItem(date="2026-03-22", food="현미밥", time="18:00")]
    )
    json_str = original.model_dump_json()
    restored = MealPlanOutput.model_validate_json(json_str)
    assert restored.items[0].food == "현미밥"


# ---------------------------------------------------------------------------
# Test 4: UserDbUpdateOutput (모드 6)
# ---------------------------------------------------------------------------


def test_user_db_update_output_instantiation():
    """UserDbUpdateOutput은 updated_fields: dict[str, Any]로 인스턴스화된다."""
    obj = UserDbUpdateOutput(updated_fields={"age": 30, "goal": "근력 강화"})
    assert obj.updated_fields["age"] == 30
    assert obj.updated_fields["goal"] == "근력 강화"


def test_user_db_update_output_roundtrip():
    """UserDbUpdateOutput JSON 직렬화/역직렬화 라운드트립."""
    original = UserDbUpdateOutput(updated_fields={"bmi": 22.5})
    json_str = original.model_dump_json()
    restored = UserDbUpdateOutput.model_validate_json(json_str)
    assert restored.updated_fields["bmi"] == 22.5


# ---------------------------------------------------------------------------
# Test 5: MealLogOutput (모드 7)
# ---------------------------------------------------------------------------


def test_meal_log_output_instantiation():
    """MealLogOutput은 calories, carbs, protein, fat, message 필드로 인스턴스화된다."""
    obj = MealLogOutput(
        calories=500,
        carbs=60,
        protein=35,
        fat=15,
        message="균형 잡힌 식사입니다.",
    )
    assert obj.calories == 500
    assert obj.carbs == 60
    assert obj.protein == 35
    assert obj.fat == 15
    assert obj.message == "균형 잡힌 식사입니다."


def test_meal_log_output_roundtrip():
    """MealLogOutput JSON 직렬화/역직렬화 라운드트립."""
    original = MealLogOutput(calories=700, carbs=80, protein=40, fat=20, message="고단백 식단")
    json_str = original.model_dump_json()
    restored = MealLogOutput.model_validate_json(json_str)
    assert restored.calories == 700
    assert restored.message == "고단백 식단"


# ---------------------------------------------------------------------------
# Test 6: RecommendationExercise / RecommendationMeal / RecommendationOutput (모드 8)
# ---------------------------------------------------------------------------


def test_recommendation_exercise_instantiation():
    """RecommendationExercise는 name, calories 필드로 인스턴스화된다."""
    obj = RecommendationExercise(name="러닝", calories=300)
    assert obj.name == "러닝"
    assert obj.calories == 300


def test_recommendation_meal_instantiation():
    """RecommendationMeal은 name, calories 필드로 인스턴스화된다."""
    obj = RecommendationMeal(name="닭가슴살 샐러드", calories=250)
    assert obj.name == "닭가슴살 샐러드"
    assert obj.calories == 250


def test_recommendation_output_instantiation():
    """RecommendationOutput은 recommended_exercises와 recommended_meals 배열을 담는다."""
    output = RecommendationOutput(
        recommended_exercises=[RecommendationExercise(name="사이클", calories=400)],
        recommended_meals=[RecommendationMeal(name="그릭 요거트", calories=150)],
    )
    assert len(output.recommended_exercises) == 1
    assert len(output.recommended_meals) == 1
    assert output.recommended_exercises[0].name == "사이클"
    assert output.recommended_meals[0].name == "그릭 요거트"


def test_recommendation_output_roundtrip():
    """RecommendationOutput JSON 직렬화/역직렬화 라운드트립."""
    original = RecommendationOutput(
        recommended_exercises=[RecommendationExercise(name="줄넘기", calories=200)],
        recommended_meals=[RecommendationMeal(name="두부", calories=100)],
    )
    json_str = original.model_dump_json()
    restored = RecommendationOutput.model_validate_json(json_str)
    assert restored.recommended_exercises[0].name == "줄넘기"
    assert restored.recommended_meals[0].name == "두부"
