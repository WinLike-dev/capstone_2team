from app.schemas.common import ErrorDetail, ErrorResponse, SuccessResponse, UserProfile
from app.schemas.meal import MealAnalysisData, ProcessMealRequest
from app.schemas.recommend import (
    RecommendationData,
    RecommendedExercise,
    RecommendedMeal,
    RecommendRequest,
)

__all__ = [
    "UserProfile",
    "SuccessResponse",
    "ErrorResponse",
    "ErrorDetail",
    "ProcessMealRequest",
    "MealAnalysisData",
    "RecommendRequest",
    "RecommendationData",
    "RecommendedExercise",
    "RecommendedMeal",
]
