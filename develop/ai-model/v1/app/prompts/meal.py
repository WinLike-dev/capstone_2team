"""Mode 7: 식단 분석 시스템 프롬프트."""

from app.schemas.common import UserProfile

MEAL_ANALYSIS_SYSTEM_PROMPT: str = (
    "당신은 식단 분석 전문가입니다.\n"
    "사용자가 제공하는 식단 정보를 분석하여 칼로리를 추정하고 간결한 피드백 메시지를 작성하세요.\n"
    "한국어로 응답하세요."
)


def build_meal_system_prompt(
    user_profile: UserProfile,
    context_text: str = "이전 맥락: 없음",
) -> str:
    """UserProfile 필드와 맥락 텍스트를 주입한 식단 분석 시스템 프롬프트를 반환한다.

    None 필드는 "정보 없음"으로 대체된다.

    Args:
        user_profile: 사용자 프로필 정보.
        context_text: Pinecone에서 검색된 이전 대화 맥락 텍스트.
            기본값은 "이전 맥락: 없음".
    """
    gender = user_profile.gender if user_profile.gender is not None else "정보 없음"
    age = str(user_profile.age) if user_profile.age is not None else "정보 없음"
    bmi = str(user_profile.bmi) if user_profile.bmi is not None else "정보 없음"
    goal = user_profile.goal if user_profile.goal is not None else "정보 없음"
    medical_history = (
        ", ".join(user_profile.medical_history)
        if user_profile.medical_history is not None
        else "정보 없음"
    )
    allergies = (
        ", ".join(user_profile.allergies)
        if user_profile.allergies is not None
        else "정보 없음"
    )

    return (
        "당신은 식단 분석 전문가입니다.\n"
        f"사용자 프로필: 성별={gender}, 나이={age}, BMI={bmi}, 목표={goal}\n"
        f"의료 이력: {medical_history}, 알레르기: {allergies}\n"
        "사용자가 제공하는 식단 정보를 분석하여 칼로리를 추정하고 간결한 피드백 메시지를 작성하세요.\n"
        f"{context_text}\n"
        "한국어로 응답하세요."
    )
