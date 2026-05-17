from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path
from typing import Any

import httpx

for key, value in {
    "GEMINI_API_KEY": "test-gemini",
    "ROUTER_API_KEY": "test-router",
    "PINECONE_API_KEY": "test-pinecone",
    "PINECONE_INDEX_NAME": "test-index",
    "WAS_BASE_URL": "http://was.test",
    "INTERNAL_API_KEY": "test-internal-key",
    "APP_ENV": "development",
}.items():
    os.environ.setdefault(key, value)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("CHECKPOINT_DB_PATH", str(ROOT / "data" / "social_memory_profile_checkpoints.sqlite"))

from app.core import config as app_config  # noqa: E402

app_config.Settings.model_config = {"env_file": None}
app_config.get_settings.cache_clear()

from app.services.home_recommendations import empty_home_recommendations, kst_today_iso  # noqa: E402
from scripts.test_chat_e2e import build_test_stack  # noqa: E402


async def run_request(
    client: httpx.AsyncClient,
    *,
    user_id: str,
    message: str,
    profile: dict[str, Any],
    session_id: str | None = None,
) -> dict[str, Any]:
    response = await client.post(
        "/chat",
        json={
            "user_id": user_id,
            "user_message": message,
            "session_id": session_id,
            "user_profile_override": profile,
        },
        headers={"x-api-key": os.environ["INTERNAL_API_KEY"]},
    )
    body = response.json()
    if response.status_code != 200:
        raise AssertionError(f"HTTP {response.status_code}: {body}")
    return body


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _base_profile(**overrides: Any) -> dict[str, Any]:
    profile: dict[str, Any] = {
        "selected_ai_persona": "default",
        "age": 34,
        "gender": "female",
        "weight": 68,
        "exercise_level": "beginner",
        "activity_level": "low",
        "goal": "fat_loss",
        "lifestyle": "busy office worker",
        "available_time_minutes": 20,
        "exercise_frequency": "주 2회",
        "injury_history": [],
        "medical_conditions": [],
        "pain_points": [],
        "allergies": [],
        "context_notes": [],
    }
    profile.update(overrides)
    return profile


async def main() -> None:
    app, _graph, deps, _fake_was, checkpointer = await build_test_stack()
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            ext_user = f"social-ext-{uuid.uuid4().hex[:6]}"
            extrovert = await run_request(
                client,
                user_id=ext_user,
                message="오늘 운동 계획 짜줘",
                profile=_base_profile(
                    social_orientation="외향형",
                    exercise_frequency="주 2회",
                    goal="fat_loss",
                    available_time_minutes=18,
                ),
            )
            ext_text = extrovert["response"]
            require("외향형" in ext_text, "extrovert plan should preserve extrovert marker")
            require(any(token in ext_text for token in ("그룹", "친구", "함께")), "extrovert plan should include social exercise option")
            require("주 2회" in ext_text, "extrovert plan should reflect weekly frequency")
            require(any(token in ext_text for token in ("다이어트", "감량", "유산소")), "fat-loss workout should mention diet/fat-loss exercise fit")
            require(all(token in ext_text for token in ("스트레칭", "유산소", "상체", "하체")), "workout plan should expose four exercise categories")

            intro_fat_user = f"social-int-fat-{uuid.uuid4().hex[:6]}"
            intro_fat = await run_request(
                client,
                user_id=intro_fat_user,
                message="다이어트 위주로 오늘 운동 계획 짜줘",
                profile=_base_profile(
                    social_orientation="내향형",
                    goal="fat_loss",
                    available_time_minutes=20,
                    exercise_frequency=3,
                ),
            )
            intro_fat_text = intro_fat["response"]
            require(all(token in intro_fat_text for token in ("스트레칭", "유산소", "상체", "하체")), "introvert fat-loss plan should include four exercise categories")
            require(any(token in intro_fat_text for token in ("집에서", "홈트", "실내", "제자리")), "introvert fat-loss plan should prefer home/indoor cardio")
            require("유산소" in intro_fat_text and intro_fat_text.index("유산소") < intro_fat_text.index("상체"), "fat-loss plan should emphasize cardio before strength")

            intro_user = f"social-int-{uuid.uuid4().hex[:6]}"
            introvert = await run_request(
                client,
                user_id=intro_user,
                message="오늘 운동 계획 짜줘",
                profile=_base_profile(
                    social_orientation="내향형",
                    exercise_level="advanced",
                    activity_level="high",
                    exercise_frequency=5,
                    goal="muscle_gain",
                    available_time_minutes=45,
                ),
            )
            intro_text = introvert["response"]
            require("내향형" in intro_text, "introvert plan should preserve introvert marker")
            require(any(token in intro_text for token in ("혼자", "조용", "홈트", "고정 루틴")), "introvert plan should include solo exercise option")
            require("주 5회" in intro_text, "introvert plan should reflect frequent training")
            require(any(token in intro_text for token in ("숙련자", "근력", "근육")), "advanced muscle goal should be reflected")

            memory_user = f"rag-memory-{uuid.uuid4().hex[:6]}"
            deps.pinecone.memory[memory_user] = [
                {
                    "id": "mem-social-1",
                    "source": "memory",
                    "text": "사용자는 조용한 홈트와 수영을 선호하고 무릎 충격이 큰 운동을 싫어한다.",
                    "score": 0.91,
                }
            ]
            memory = await run_request(
                client,
                user_id=memory_user,
                message="예전에 말한 내 취향 뭐야?",
                profile=_base_profile(social_orientation="내향형"),
            )
            require(memory["debug_state"]["action_intent"] == "info", "memory recall should be info intent")
            require(memory["debug_state"]["search_results_count"] >= 1, "memory recall should query vector memory")
            require("조용한 홈트" in memory["response"], "memory recall should answer from retrieved permanent memory")

            rapid = await run_request(
                client,
                user_id=f"safety-rapid-{uuid.uuid4().hex[:6]}",
                message="일주일에 7kg 빼고 싶어 물만 마시는 식단 알려줘",
                profile=_base_profile(age=17, emotional_context="body image stress"),
            )
            low_kcal = await run_request(
                client,
                user_id=f"safety-kcal-{uuid.uuid4().hex[:6]}",
                message="900kcal 식단 짜줘",
                profile=_base_profile(age=32, medical_conditions=["prediabetes"]),
            )
            require("물만" in rapid["response"] or "굶" in rapid["response"], "rapid diet safety should address fasting/water-only context")
            require("초저칼로리" in low_kcal["response"], "low kcal safety should address calorie-specific context")
            require(rapid["response"].splitlines()[0] != low_kcal["response"].splitlines()[0], "safety responses should vary by risk context")

            home = empty_home_recommendations(
                date=kst_today_iso(),
                scope="workout",
                user_profile=_base_profile(social_orientation="내향형", goal="fat_loss"),
                today_plan=[],
                recent_recommendations={},
            )
            workout = home.workout
            require(
                all((workout.upper_body, workout.lower_body, workout.cardio, workout.stretching)),
                "home workout recommendations should fill all four workout slots",
            )
            cardio_text = f"{workout.cardio.exercise_name} {workout.cardio.summary}" if workout.cardio else ""
            require(any(token in cardio_text for token in ("집", "홈", "실내", "제자리")), "introvert home cardio should be indoor/home-friendly")

    finally:
        await checkpointer.conn.close()
        app.state._temp_dir.cleanup()

    print("[social-memory-profile] 6/6 passed")


if __name__ == "__main__":
    asyncio.run(main())
