"""Worker AI 시스템 프롬프트 빌더.

모드(1-8), UserProfile, 맥락 텍스트, 사용자 지시사항을 받아
Gemini 워커 AI에게 전달할 시스템 프롬프트를 구성한다.

우선순위 (CHAT-12):
  사용자 메시지 > 사용자 지시사항 > 시스템 지시사항
"""

from app.schemas.common import UserProfile

# ---------------------------------------------------------------------------
# 공통 지시사항
# ---------------------------------------------------------------------------

_COMMON_RULES: str = (
    "당신은 사용자의 건강과 피트니스를 추적하고 최적화하는 '워커 AI(영양 및 운동 전문가)'입니다.\n"
    "라우터 AI가 분류한 모드와 사용자의 입력을 바탕으로 최적의 결과를 제공하십시오.\n\n"
    "### 공통 규칙\n"
    "- **모든 출력은 반드시 JSON 형식을 유지해야 합니다.** 예외는 없습니다.\n"
    "- **우선순위 (판단 근거)**: 계획 세우기나 추천 시 다음 순서로 고려하십시오.\n"
    "    1. **사용자의 성향 (MBTI 등)**: 대화 톤이나 활동 선호도 반영\n"
    "    2. **헬스 목표**: 다이어트, 벌크업, 근력 증진 등\n"
    "    3. **건강 상태**: 부상 부위, 지병, 현재 체력 수준 등\n"
    "- **우선순위 (명령어)**: 1순위(사용자 메시지) > 2순위(사용자 지시사항) > 3순위(시스템 지시사항).\n"
    "- **형식 준수**: 출력 시 마크다운 코드 블록(```json ... ```)을 사용하고, 블록 외부에는 어떤 텍스트도 포함하지 마십시오.\n"
)

# ---------------------------------------------------------------------------
# 모드별 지시사항
# ---------------------------------------------------------------------------

_MODE_INSTRUCTIONS: dict[int, str] = {
    1: (
        "### 모드 1: 단순대화 (Simple Conversation)\n"
        "- **목적**: 인사, 일반 건강 상식, 피드백 등 일상적인 대화 처리.\n"
        "- **출력 형식**:\n"
        "  ```json\n"
        "  {\n"
        '    "answer": "사용자의 질문에 대한 답변 내용"\n'
        "  }\n"
        "  ```\n"
    ),
    2: (
        "### 모드 2: 플랜 작성 (Plan Creation)\n"
        "- **목적**: 새로운 운동 루틴 생성.\n"
        "- **출력 형식**:\n"
        "  ```json\n"
        "  [\n"
        "    {\n"
        '      "date": "YYYY-MM-DD",\n'
        '      "type": "운동 종류",\n'
        '      "detail": "운동 세부 항목",\n'
        '      "count": "횟수/시간"\n'
        "    }\n"
        "  ]\n"
        "  ```\n"
        "- **디폴트**: 사용자 지시사항/사용자 메세지에 언급이 없으면 **1달(30일)** 분량의 운동 계획을 작성합니다.\n"
    ),
    3: (
        "### 모드 3: 플랜 수정 (Plan Modification)\n"
        "- **목적**: 기존 운동 루틴의 변경, 추가, 삭제.\n"
        "- **출력 형식**:\n"
        "  ```json\n"
        "  [\n"
        "    {\n"
        '      "date": "YYYY-MM-DD",\n'
        '      "type": "운동 종류",\n'
        '      "detail": "운동 세부 항목",\n'
        '      "count": "횟수/시간"\n'
        "    }\n"
        "  ]\n"
        "  ```\n"
        "- **디폴트**: 사용자 지시사항/사용자 메세지에 언급이 없으면 해당 계획을 **전체적으로 재구성**하여 반환합니다.\n"
    ),
    4: (
        "### 모드 4: 식단 작성 (Meal Plan Creation)\n"
        "- **목적**: 사용자의 목표에 맞는 식단 생성.\n"
        "- **출력 형식**:\n"
        "  ```json\n"
        "  [\n"
        "    {\n"
        '      "date": "YYYY-MM-DD",\n'
        '      "food": "식품 종류",\n'
        '      "time": "아침/점심/저녁"\n'
        "    }\n"
        "  ]\n"
        "  ```\n"
        "- **디폴트**: 사용자 지시사항/사용자 메세지에 언급이 없으면 **1달(30일)치의 아침, 점심, 저녁 (총 90개의 리스트 요소)**를 작성합니다.\n"
    ),
    5: (
        "### 모드 5: 식단 수정 (Meal Plan Modification)\n"
        "- **목적**: 기존 식단 계획의 특정 메뉴나 영양소 비중 조정.\n"
        "- **출력 형식**:\n"
        "  ```json\n"
        "  [\n"
        "    {\n"
        '      "date": "YYYY-MM-DD",\n'
        '      "food": "식품 종류",\n'
        '      "time": "아침/점심/저녁"\n'
        "    }\n"
        "  ]\n"
        "  ```\n"
        "- **디폴트**: 사용자 지시사항/사용자 메세지에 언급이 없으면 **전체 식단**을 업데이트하여 반환합니다.\n"
    ),
    6: (
        "### 모드 6: 사용자 DB 수정 (User DB Modification)\n"
        "- **목적**: 사용자의 신체 정보(키, 몸무게, 활동량 등) 또는 목표 업데이트.\n"
        "- **출력 형식**:\n"
        "  ```json\n"
        "  {\n"
        '    "updated_fields": {\n'
        '      "field_name": "value"\n'
        "    }\n"
        "  }\n"
        "  ```\n"
        "- **지침**: 변경이 필요한 모든 필드와 그 값을 포함하십시오.\n"
    ),
}

# ---------------------------------------------------------------------------
# 주의 사항
# ---------------------------------------------------------------------------

_CAUTION: str = (
    "### 주의 사항\n"
    "- 사용자의 판단 근거 우선순위(**성향 > 목표 > 건강 상태**)를 준수하여 개인화된 답변을 제공하십시오.\n"
    "- 모든 수치(칼로리, 영양소, 횟수)는 사용자의 신체 정보와 목표를 바탕으로 합리적으로 계산되어야 합니다.\n"
    "- **JSON 출력 시 마크다운 코드 블록(```json ... ```)을 사용하고, 다른 불필요한 텍스트를 절대 포함하지 마십시오.**\n"
)


# ---------------------------------------------------------------------------
# 헬퍼 함수
# ---------------------------------------------------------------------------


def _format_user_profile(profile: UserProfile) -> str:
    """UserProfile에서 None이 아닌 필드만 '키: 값' 형태로 포매팅한다.

    Args:
        profile: 사용자 프로필 정보.

    Returns:
        포매팅된 프로필 문자열. 모든 필드가 None이면 '정보 없음'을 반환한다.
    """
    field_labels: dict[str, str] = {
        "gender": "성별",
        "age": "나이",
        "bmi": "BMI",
        "goal": "목표",
        "personality": "성향(MBTI)",
        "medical_history": "의료 이력",
        "allergies": "알레르기",
        "activity_level": "활동 수준",
    }

    lines: list[str] = []
    for field, label in field_labels.items():
        value = getattr(profile, field)
        if value is None:
            continue
        if isinstance(value, list):
            formatted_value = ", ".join(value) if value else "없음"
        else:
            formatted_value = str(value)
        lines.append(f"{label}: {formatted_value}")

    return "\n".join(lines) if lines else "정보 없음"


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------


def build_worker_system_prompt(
    mode: int,
    user_profile: UserProfile,
    context_text: str,
    user_instruction: str = "",
) -> str:
    """워커 AI(Gemini Flash)에게 전달할 시스템 프롬프트를 구성한다.

    프롬프트 구성 순서 (CHAT-12 — 우선순위: 사용자 메시지 > 사용자 지시사항 > 시스템 지시사항):
      1. [선택] 사용자 지시사항 섹션 (user_instruction이 비어있지 않을 때만)
      2. 시스템 지시사항 (공통 규칙 + 모드별 지시사항 + 주의 사항)
      3. 사용자 프로필
      4. 이전 대화 맥락 (Vector DB 검색 결과)

    Args:
        mode: 라우터 AI가 분류한 모드 번호 (1-6).
        user_profile: 사용자 프로필 정보.
        context_text: Pinecone에서 검색된 이전 대화 맥락 텍스트.
        user_instruction: 사용자 지시사항 (없으면 빈 문자열).

    Returns:
        완성된 시스템 프롬프트 문자열.
    """
    parts: list[str] = []

    # 1. 사용자 지시사항 (있을 때만)
    if user_instruction.strip():
        parts.append(f"사용자 지시사항: {user_instruction}\n")

    # 2. 시스템 지시사항 — 공통 규칙
    parts.append("## 시스템 지시사항\n")
    parts.append(_COMMON_RULES)

    # 3. 모드별 지시사항
    mode_instruction = _MODE_INSTRUCTIONS.get(mode, _MODE_INSTRUCTIONS[1])
    parts.append(f"\n## 모드 {mode} 지시사항\n")
    parts.append(mode_instruction)

    # 4. 주의 사항
    parts.append(f"\n{_CAUTION}")

    # 5. 사용자 프로필
    formatted_profile = _format_user_profile(user_profile)
    parts.append(f"\n## 사용자 프로필\n{formatted_profile}\n")

    # 6. 이전 대화 맥락
    parts.append(f"\n## 이전 대화 맥락\n{context_text}\n")

    return "".join(parts)
