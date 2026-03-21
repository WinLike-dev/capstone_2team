import pytest
from pydantic import ValidationError

from app.schemas.common import ErrorDetail, ErrorResponse, SuccessResponse, UserProfile
from app.schemas.meal import MealAnalysisData, ProcessMealRequest
from app.schemas.recommend import (
    RecommendationData,
    RecommendedExercise,
    RecommendedMeal,
    RecommendRequest,
)


# --- UserProfile ---

def test_user_profile_optional_fields_default_none():
    """UserProfile의 모든 필드는 Optional로 기본값 None."""
    profile = UserProfile()
    assert profile.gender is None
    assert profile.age is None
    assert profile.bmi is None
    assert profile.goal is None
    assert profile.medical_history is None
    assert profile.allergies is None
    assert profile.activity_level is None


def test_user_profile_partial_fields():
    """UserProfile이 일부 필드만 설정 가능."""
    profile = UserProfile(gender="male", age=30, activity_level="moderate")
    assert profile.gender == "male"
    assert profile.age == 30
    assert profile.activity_level == "moderate"
    assert profile.bmi is None


# --- ProcessMealRequest ---

def test_process_meal_request_valid():
    """ProcessMealRequest가 유효한 JSON을 파싱한다."""
    data = {
        "user_id": "user_123",
        "user_profile": {
            "gender": "female",
            "age": 25,
            "bmi": 22.5,
            "goal": "체중 감량",
            "medical_history": ["고혈압"],
            "allergies": ["견과류"],
        },
        "user_instruction": "칼로리를 최소화해줘",
        "user_message": "점심에 비빔밥 먹었어",
    }
    req = ProcessMealRequest(**data)
    assert req.user_id == "user_123"
    assert req.user_profile.gender == "female"
    assert req.user_profile.medical_history == ["고혈압"]
    assert req.user_message == "점심에 비빔밥 먹었어"


def test_process_meal_request_missing_user_id_raises():
    """ProcessMealRequest가 user_id 누락 시 ValidationError를 발생시킨다."""
    with pytest.raises(ValidationError) as exc_info:
        ProcessMealRequest(
            user_profile={},
            user_instruction="test",
            user_message="test",
        )
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("user_id",) for e in errors)


def test_process_meal_request_empty_profile():
    """ProcessMealRequest가 빈 user_profile을 허용한다 (모든 필드 Optional)."""
    req = ProcessMealRequest(
        user_id="u1",
        user_profile={},
        user_instruction="test",
        user_message="test msg",
    )
    assert req.user_profile.gender is None
    assert req.user_profile.allergies is None


# --- MealAnalysisData ---

def test_meal_analysis_data_serialization():
    """MealAnalysisData가 올바르게 직렬화된다."""
    data = MealAnalysisData(calories=350.0, message="균형 잡힌 식사입니다.")
    dumped = data.model_dump()
    assert dumped["calories"] == 350.0
    assert dumped["message"] == "균형 잡힌 식사입니다."


# --- RecommendRequest ---

def test_recommend_request_valid():
    """RecommendRequest가 유효한 JSON을 파싱한다."""
    data = {
        "user_id": "user_456",
        "user_profile": {
            "gender": "male",
            "age": 35,
            "bmi": 24.0,
            "goal": "근력 증가",
            "activity_level": "high",
        },
        "user_instruction": "운동과 식단 추천해줘",
    }
    req = RecommendRequest(**data)
    assert req.user_id == "user_456"
    assert req.user_profile.activity_level == "high"
    assert req.user_instruction == "운동과 식단 추천해줘"


def test_recommend_request_missing_user_id_raises():
    """RecommendRequest가 user_id 누락 시 ValidationError를 발생시킨다."""
    with pytest.raises(ValidationError) as exc_info:
        RecommendRequest(
            user_profile={},
            user_instruction="추천해줘",
        )
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("user_id",) for e in errors)


# --- RecommendationData ---

def test_recommendation_data_serialization():
    """RecommendationData가 올바르게 직렬화된다."""
    data = RecommendationData(
        recommended_exercise=RecommendedExercise(name="조깅", burn_calories=300.0),
        recommended_meal=RecommendedMeal(name="닭가슴살 샐러드", calories=400.0),
    )
    dumped = data.model_dump()
    assert dumped["recommended_exercise"]["name"] == "조깅"
    assert dumped["recommended_exercise"]["burn_calories"] == 300.0
    assert dumped["recommended_meal"]["name"] == "닭가슴살 샐러드"
    assert dumped["recommended_meal"]["calories"] == 400.0


# --- SuccessResponse / ErrorResponse ---

def test_success_response_default_status():
    """SuccessResponse의 status 기본값은 'success'."""
    resp = SuccessResponse(data={"key": "value"})
    assert resp.status == "success"


def test_error_response_structure():
    """ErrorResponse가 올바른 구조를 가진다."""
    resp = ErrorResponse(error=ErrorDetail(code="INVALID_INPUT", message="잘못된 입력입니다."))
    assert resp.status == "error"
    assert resp.error.code == "INVALID_INPUT"
