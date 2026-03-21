"""Mode 8: 운동/식단 추천 시스템 프롬프트."""

from app.schemas.common import UserProfile

RECOMMENDATION_SYSTEM_PROMPT: str = (
    "당신은 운동/식단 추천 전문가입니다.\n"
    "사용자의 지시사항을 기반으로 적합한 운동(이름+소모칼로리)과 식단(이름+칼로리)을 각 1개씩 추천하세요.\n"
    "한국어로 응답하세요."
)


def build_recommend_system_prompt(user_profile: UserProfile) -> str:
    """UserProfile 필드를 주입한 추천 시스템 프롬프트를 반환한다.

    None 필드는 "정보 없음"으로 대체된다.
    """
    gender = user_profile.gender if user_profile.gender is not None else "정보 없음"
    age = str(user_profile.age) if user_profile.age is not None else "정보 없음"
    bmi = str(user_profile.bmi) if user_profile.bmi is not None else "정보 없음"
    goal = user_profile.goal if user_profile.goal is not None else "정보 없음"
    activity_level = (
        user_profile.activity_level
        if user_profile.activity_level is not None
        else "정보 없음"
    )

    return (
        "당신은 운동/식단 추천 전문가입니다.\n"
        f"사용자 프로필: 성별={gender}, 나이={age}, BMI={bmi}, 목표={goal}, 활동 수준={activity_level}\n"
        "사용자의 지시사항을 기반으로 적합한 운동(이름+소모칼로리)과 식단(이름+칼로리)을 각 1개씩 추천하세요.\n"
        "한국어로 응답하세요."
    )
