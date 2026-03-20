"""
health_chain.py — AI Core 파이프라인 오케스트레이터

[담당 분리]
  ■ 이 파일에서 구현 완료 (Router AI 담당)
      - Router AI 실행 및 모드 1~6 분류
      - 모드 3/5 백엔드 데이터 페치
      - Router AI 결과를 Worker AI 인터페이스로 전달

  □ 팀원 구현 예정 (Worker AI 담당)
      - _call_worker_ai() 함수 본체
      - run_meal_chain() 함수 본체
      - run_recommend_chain() 함수 본체
"""

import logging
from typing import Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI

from config import get_settings
from chains.prompt_templates import build_router_prompt
from models.request_models import AIChatRequest, MealRequest, RecommendRequest
from models.response_models import RouterResult

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# 폴백 응답
# ──────────────────────────────────────────────────────────────────────────────

CHAT_FALLBACK: dict[str, Any] = {
    "status": "success",
    "mode": 1,
    "data": {
        "message": "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
        "plan": None,
        "db_update": None,
    },
}

MEAL_FALLBACK: dict[str, Any] = {
    "status": "success",
    "data": {"calories": 0, "message": "식사 기록 중 오류가 발생했습니다."},
}

RECOMMEND_FALLBACK: dict[str, Any] = {
    "status": "success",
    "data": {
        "recommended_exercise": {"name": "걷기 30분", "burn_calories": 150},
        "recommended_meal": {"name": "혼합 채소 샐러드", "calories": 300},
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# 공통 유틸
# ──────────────────────────────────────────────────────────────────────────────

def _build_llm() -> ChatGoogleGenerativeAI:
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        temperature=settings.gemini_temperature,
        google_api_key=settings.google_api_key,
    )


def _build_user_vars(profile: Any) -> dict[str, str]:
    """어떤 UserProfile 타입이든 프롬프트 변수 딕셔너리로 변환합니다."""
    medical = getattr(profile, "medical_history", None)
    allergies = getattr(profile, "allergies", None)
    activity = getattr(profile, "activity_level", None)
    return {
        "gender": profile.gender,
        "age": str(profile.age),
        "bmi": str(profile.bmi),
        "goal": profile.goal,
        "activity_level": activity or "정보 없음",
        "medical_history": ", ".join(medical) if medical else "없음",
        "allergies": ", ".join(allergies) if allergies else "없음",
    }


# ──────────────────────────────────────────────────────────────────────────────
# [Router AI 담당] 백엔드 데이터 페치 (Mode 3, 5)
# ──────────────────────────────────────────────────────────────────────────────

async def _fetch_current_exercise_list(user_id: str) -> list[dict]:
    """[더미] 백엔드에서 현재 운동 계획 목록을 가져옵니다.
    실제 구현 시: GET /api/users/{user_id}/exercise-plans
    """
    logger.info("운동 계획 페치 (더미). user_id=%s", user_id)
    # TODO: 실제 백엔드 API 호출로 교체
    return []


async def _fetch_current_diet_list(user_id: str) -> list[dict]:
    """[더미] 백엔드에서 현재 식단 목록을 가져옵니다.
    실제 구현 시: GET /api/users/{user_id}/diet-plans
    """
    logger.info("식단 페치 (더미). user_id=%s", user_id)
    # TODO: 실제 백엔드 API 호출로 교체
    return []


def _format_exercise_list_block(exercise_list: list[dict]) -> str:
    if not exercise_list:
        return "## 현재 운동 계획\n(등록된 운동 계획이 없습니다.)"
    lines = ["## 현재 운동 계획"]
    for item in exercise_list:
        lines.append(
            f"- {item.get('detail', '?')} | {item.get('type', '?')} | {item.get('value', '?')}"
        )
    return "\n".join(lines)


def _format_diet_list_block(diet_list: list[dict]) -> str:
    if not diet_list:
        return "## 현재 식단 계획\n(등록된 식단 계획이 없습니다.)"
    lines = ["## 현재 식단 계획"]
    for item in diet_list:
        lines.append(
            f"- {item.get('detail', '?')}: {item.get('type', '?')} ({item.get('value', '?')})"
        )
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# [Router AI 담당] Router AI 실행
# ──────────────────────────────────────────────────────────────────────────────

async def _run_router(llm: ChatGoogleGenerativeAI, message: str) -> RouterResult:
    """Router AI: 사용자 메시지를 분석하여 모드 1~6을 결정합니다.

    LangChain with_structured_output으로 RouterResult 스키마를 강제합니다.
    Input  : Router 시스템 지침서 + 사용자 메시지
    Output : { selected_mode: int(1~6), reason: str }
    """
    structured_llm = llm.with_structured_output(RouterResult)
    chain = build_router_prompt() | structured_llm
    result: RouterResult = await chain.ainvoke({"current_message": message})
    logger.info(
        "Router AI 분류 완료. mode=%d, reason=%s",
        result.selected_mode,
        result.reason,
    )
    return result


# ──────────────────────────────────────────────────────────────────────────────
# [Worker AI 담당] Worker AI 인터페이스 (팀원 구현 예정)
# ──────────────────────────────────────────────────────────────────────────────

async def _call_worker_ai(
    mode: int,
    router_result: RouterResult,
    request: AIChatRequest,
    user_vars: dict[str, str],
    extra_context: str = "",
) -> dict[str, Any]:
    """[Worker AI 인터페이스] 팀원이 이 함수를 구현합니다.

    Args:
        mode         : Router AI가 분류한 모드 번호 (1~6)
        router_result: Router AI 결과 (selected_mode + reason) — 모드 1~5에 전달
        request      : 원본 요청 (user_message, user_instruction, user_id 등)
        user_vars    : 프롬프트용 사용자 정보 딕셔너리
        extra_context: 모드 3 → 현재 운동 목록 블록 / 모드 5 → 현재 식단 목록 블록

    Returns:
        AIChatResponse 형식의 딕셔너리
            {
                "status": "success",
                "mode": int,
                "data": {
                    "message": str,
                    "plan": { "date": str, "items": [...] } | None,
                    "db_update": { "field": str, "new_value": any } | None
                }
            }
    """
    # ── TODO: 아래 stub을 Worker AI 호출 로직으로 교체하세요 ──────────────
    MODE_NAMES = {
        1: "단순 대화",
        2: "운동 플랜 작성",
        3: "운동 플랜 수정",
        4: "식단 플랜 작성",
        5: "식단 플랜 수정",
        6: "사용자 정보 수정",
    }
    logger.warning(
        "[STUB] Worker AI 미구현. mode=%d, user_id=%s", mode, request.user_id
    )
    return {
        "status": "success",
        "mode": mode,
        "data": {
            "message": (
                f"[Worker AI 미구현] "
                f"Router AI가 '{MODE_NAMES.get(mode, mode)}' 모드로 분류했습니다. "
                f"(근거: {router_result.reason})"
            ),
            "plan": None,
            "db_update": None,
        },
    }


async def _call_meal_worker_ai(
    request: MealRequest,
    user_vars: dict[str, str],
) -> dict[str, Any]:
    """[Worker AI 인터페이스] 식단 기록 Worker AI — 팀원이 이 함수를 구현합니다.

    Args:
        request  : MealRequest (user_message에 식사 내용 포함)
        user_vars: 프롬프트용 사용자 정보 딕셔너리

    Returns:
        MealResponse 형식의 딕셔너리
            { "status": "success", "data": { "calories": int, "message": str } }
    """
    # ── TODO: 아래 stub을 Worker AI 호출 로직으로 교체하세요 ──────────────
    logger.warning("[STUB] Meal Worker AI 미구현. user_id=%s", request.user_id)
    return {
        "status": "success",
        "data": {"calories": 0, "message": "[Worker AI 미구현] 식단 기록 처리 예정"},
    }


async def _call_recommend_worker_ai(
    request: RecommendRequest,
    user_vars: dict[str, str],
) -> dict[str, Any]:
    """[Worker AI 인터페이스] 추천 기능 — 팀원이 이 함수를 구현합니다.

    Args:
        request  : RecommendRequest
        user_vars: 프롬프트용 사용자 정보 딕셔너리

    Returns:
        RecommendResponse 형식의 딕셔너리
            {
                "status": "success",
                "data": {
                    "recommended_exercise": { "name": str, "burn_calories": int },
                    "recommended_meal": { "name": str, "calories": int }
                }
            }
    """
    # ── TODO: 아래 stub을 추천 알고리즘으로 교체하세요 ───────────────────
    logger.warning("[STUB] Recommend Worker AI 미구현. user_id=%s", request.user_id)
    return {
        "status": "success",
        "data": {
            "recommended_exercise": {"name": "[미구현]", "burn_calories": 0},
            "recommended_meal": {"name": "[미구현]", "calories": 0},
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# 엔트리포인트 1: POST /ai-chat
# ──────────────────────────────────────────────────────────────────────────────

async def run_chat_chain(request: AIChatRequest) -> dict[str, Any]:
    """Router AI → Worker AI 파이프라인 (모드 1~6).

    [Router AI 담당 흐름]
        1. Router AI 실행 → 모드 1~6 분류
        2. 모드 3 → 백엔드에서 현재 운동 목록 페치
           모드 5 → 백엔드에서 현재 식단 목록 페치
        3. 수집한 컨텍스트와 함께 Worker AI 인터페이스 호출

    [Worker AI 담당 — _call_worker_ai() 구현 필요]
        4. 모드별 Worker AI 프롬프트 실행 → Gemini 응답 → 응답 조립
    """
    try:
        llm = _build_llm()
        user_vars = _build_user_vars(request.user_profile)

        # ── Step 1: Router AI 실행 ────────────────────────────────────────
        logger.info("Router AI 호출. user_id=%s, message=%r",
                    request.user_id, request.user_message[:50])
        router_result = await _run_router(llm, request.user_message)
        mode = router_result.selected_mode
        logger.info("Router AI 완료. user_id=%s, mode=%d", request.user_id, mode)

        # ── Step 2: 모드 3/5 — 백엔드 현재 데이터 페치 ───────────────────
        extra_context = ""
        if mode == 3:
            exercise_list = await _fetch_current_exercise_list(request.user_id)
            extra_context = _format_exercise_list_block(exercise_list)
            logger.info("운동 목록 페치 완료. count=%d", len(exercise_list))
        elif mode == 5:
            diet_list = await _fetch_current_diet_list(request.user_id)
            extra_context = _format_diet_list_block(diet_list)
            logger.info("식단 목록 페치 완료. count=%d", len(diet_list))

        # ── Step 3: Worker AI 호출 ────────────────────────────────────────
        return await _call_worker_ai(
            mode=mode,
            router_result=router_result,
            request=request,
            user_vars=user_vars,
            extra_context=extra_context,
        )

    except Exception:
        logger.exception("run_chat_chain 예외. user_id=%s", request.user_id)
        return CHAT_FALLBACK


# ──────────────────────────────────────────────────────────────────────────────
# 엔트리포인트 2: POST /process-meal (Router AI 바이패스)
# ──────────────────────────────────────────────────────────────────────────────

async def run_meal_chain(request: MealRequest) -> dict[str, Any]:
    """식단 기록 체인 — Router AI 바이패스, Worker AI 직행.
    [Worker AI 담당 — _call_meal_worker_ai() 구현 필요]
    """
    try:
        user_vars = _build_user_vars(request.user_profile)
        return await _call_meal_worker_ai(request, user_vars)
    except Exception:
        logger.exception("run_meal_chain 예외. user_id=%s", request.user_id)
        return MEAL_FALLBACK


# ──────────────────────────────────────────────────────────────────────────────
# 엔트리포인트 3: POST /recommend (Router AI + Worker AI 바이패스)
# ──────────────────────────────────────────────────────────────────────────────

async def run_recommend_chain(request: RecommendRequest) -> dict[str, Any]:
    """추천 기능 — Router AI + Worker AI 모두 바이패스, 정적 알고리즘 처리.
    [Worker AI 담당 — _call_recommend_worker_ai() 구현 필요]
    """
    try:
        user_vars = _build_user_vars(request.user_profile)
        return await _call_recommend_worker_ai(request, user_vars)
    except Exception:
        logger.exception("run_recommend_chain 예외. user_id=%s", request.user_id)
        return RECOMMEND_FALLBACK
