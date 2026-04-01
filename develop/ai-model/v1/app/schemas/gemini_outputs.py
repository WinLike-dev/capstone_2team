"""7개 모드별 Gemini structured output Pydantic 스키마.

Gemini response_schema 파라미터는 Pydantic BaseModel 서브클래스를 받는다.
top-level list는 지원되지 않으므로 items wrapper 패턴을 사용한다.

모드별 스키마:
  모드 1 — SimpleAnswerOutput(answer: str)
  모드 2, 3 — ExercisePlanOutput(items: list[ExercisePlanItem])
  모드 4, 5 — MealPlanOutput(items: list[MealPlanItem])
  모드 7 — MealLogOutput(calories, carbs, protein, fat, message)
  모드 8 — RecommendationOutput(recommended_exercises, recommended_meals)
"""

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# 모드 1 — 단순 대화 응답
# ---------------------------------------------------------------------------


class SimpleAnswerOutput(BaseModel):
    """모드 1 기본 응답 스키마.

    Gemini 응답 형태: {"answer": "..."}
    """

    answer: str


# ---------------------------------------------------------------------------
# 모드 2, 3 — 운동 계획 생성 / 수정
# ---------------------------------------------------------------------------


class ExercisePlanItem(BaseModel):
    """운동 계획의 단일 항목.

    Gemini 응답 배열 원소: {"date": "...", "type": "...", "detail": "...", "count": "..."}
    """

    date: str
    type: str
    detail: str
    count: str


class ExercisePlanOutput(BaseModel):
    """모드 2, 3 운동 계획 응답 스키마.

    Gemini top-level list 미지원으로 items wrapper 사용.
    Gemini 응답 형태: {"items": [{"date", "type", "detail", "count"}, ...]}
    """

    items: list[ExercisePlanItem]


# ---------------------------------------------------------------------------
# 모드 4, 5 — 식단 계획 생성 / 수정
# ---------------------------------------------------------------------------


class MealPlanItem(BaseModel):
    """식단 계획의 단일 항목.

    Gemini 응답 배열 원소: {"date": "...", "food": "...", "time": "..."}
    """

    date: str
    food: str
    time: str


class MealPlanOutput(BaseModel):
    """모드 4, 5 식단 계획 응답 스키마.

    Gemini top-level list 미지원으로 items wrapper 사용.
    Gemini 응답 형태: {"items": [{"date", "food", "time"}, ...]}
    """

    items: list[MealPlanItem]


# ---------------------------------------------------------------------------
# 모드 7 — 식사 기록 칼로리/영양소 분석
# ---------------------------------------------------------------------------


class MealLogOutput(BaseModel):
    """모드 7 식사 기록 분석 응답 스키마.

    Gemini 응답 형태: {"calories": N, "carbs": N, "protein": N, "fat": N, "message": "..."}
    """

    calories: int
    carbs: int
    protein: int
    fat: int
    message: str


# ---------------------------------------------------------------------------
# 모드 8 — 운동/식단 추천
# ---------------------------------------------------------------------------


class RecommendationExercise(BaseModel):
    """추천 운동 단일 항목."""

    name: str
    calories: int


class RecommendationMeal(BaseModel):
    """추천 식단 단일 항목."""

    name: str
    calories: int


class RecommendationOutput(BaseModel):
    """모드 8 운동/식단 추천 응답 스키마.

    Gemini 응답 형태:
      {
        "recommended_exercises": [{"name": "...", "calories": N}, ...],
        "recommended_meals": [{"name": "...", "calories": N}, ...]
      }
    """

    recommended_exercises: list[RecommendationExercise]
    recommended_meals: list[RecommendationMeal]
