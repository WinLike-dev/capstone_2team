"""Unit tests for context_text parameter in prompt builders."""

from app.prompts.meal import build_meal_system_prompt
from app.prompts.recommend import build_recommend_system_prompt
from app.schemas.common import UserProfile


_BASE_PROFILE = UserProfile(gender="male", age=25, bmi=22.0, goal="체중 감량")


# ---------------------------------------------------------------------------
# build_meal_system_prompt context_text tests
# ---------------------------------------------------------------------------


def test_meal_prompt_with_context() -> None:
    """context_text 전달 시 반환 문자열에 해당 내용이 포함된다."""
    context = "이전 맥락:\n1. 어제 치킨 먹음"
    result = build_meal_system_prompt(_BASE_PROFILE, context_text=context)

    assert context in result


def test_meal_prompt_default_context() -> None:
    """context_text 없이 호출 시 기본값 '이전 맥락: 없음'이 포함된다."""
    result = build_meal_system_prompt(_BASE_PROFILE)

    assert "이전 맥락: 없음" in result


# ---------------------------------------------------------------------------
# build_recommend_system_prompt context_text tests
# ---------------------------------------------------------------------------


def test_recommend_prompt_with_context() -> None:
    """context_text 전달 시 반환 문자열에 해당 내용이 포함된다."""
    context = "이전 맥락:\n1. 지난주 조깅 30분"
    result = build_recommend_system_prompt(_BASE_PROFILE, context_text=context)

    assert context in result


def test_recommend_prompt_default_context() -> None:
    """context_text 없이 호출 시 기본값 '이전 맥락: 없음'이 포함된다."""
    result = build_recommend_system_prompt(_BASE_PROFILE)

    assert "이전 맥락: 없음" in result
