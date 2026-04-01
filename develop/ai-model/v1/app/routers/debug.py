"""Debug UI router — 파이프라인 각 단계의 입출력을 시각화.

GET  /debug                  → HTML 디버그 UI 페이지
POST /ai-chat-debug          → 파이프라인 실행 + 각 단계 데이터 수집
GET  /debug/system-prompts   → Router/Worker 시스템 지침서 전문 반환
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from pydantic import BaseModel

from app.prompts.meal import build_meal_system_prompt
from app.prompts.recommend import build_recommend_system_prompt
from app.prompts.router import ROUTER_SYSTEM_PROMPT
from app.prompts.worker import _COMMON_RULES, _MODE_INSTRUCTIONS, _CAUTION, build_worker_system_prompt
from app.schemas.chat import AiChatRequest, get_db_modified_flag
from app.schemas.gemini_outputs import (
    ExercisePlanOutput,
    MealLogOutput,
    MealPlanOutput,
    RecommendationOutput,
    SimpleAnswerOutput,
)
from app.schemas.meal import MealAnalysisData, ProcessMealRequest
from app.schemas.recommend import RecommendationData, RecommendRequest
from app.prompts.summary import SummaryOutput, build_summary_prompt
from app.services.chat_service import _build_ai_chat_data, _fetch_context


class VectorSearchRequest(BaseModel):
    user_id: str
    query: str
    top_k: int = 3


class VectorUpsertRequest(BaseModel):
    user_id: str
    summary: str


class WASTestRequest(BaseModel):
    user_id: str

logger = logging.getLogger(__name__)

router = APIRouter(tags=["debug"])

_MODE_SCHEMA_MAP: dict[int, type] = {
    1: SimpleAnswerOutput,
    2: ExercisePlanOutput,
    3: ExercisePlanOutput,
    4: MealPlanOutput,
    5: MealPlanOutput,
}

_MODE_NAMES: dict[int, str] = {
    1: "단순대화",
    2: "플랜 작성",
    3: "플랜 수정",
    4: "식단 작성",
    5: "식단 수정",
}


def _step(name: str, description: str, input_data: Any, output_data: Any, elapsed_ms: float) -> dict:
    return {
        "name": name,
        "description": description,
        "input": input_data,
        "output": output_data,
        "elapsed_ms": round(elapsed_ms, 1),
    }


@router.get("/debug", response_class=HTMLResponse)
async def debug_page():
    """디버그 UI HTML 페이지를 반환한다."""
    html_path = Path(__file__).parent.parent / "static" / "debug.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@router.post("/ai-chat-debug")
async def ai_chat_debug(body: AiChatRequest, request: Request) -> dict:
    """파이프라인을 실행하면서 각 단계별 입출력 데이터를 수집하여 반환한다."""
    steps: list[dict] = []
    total_start = time.perf_counter()

    router_client = request.app.state.router_client
    gemini = request.app.state.gemini_client
    pinecone = request.app.state.pinecone_client
    embed = request.app.state.embed_client
    was = request.app.state.was_client

    # ── Step 1: Router AI 의도 분류 ──
    t0 = time.perf_counter()
    try:
        router_output = await router_client.classify(body.user_message)
        router_result = {"mode": router_output.mode, "reason": router_output.reason}
        router_error = None
    except Exception as exc:
        from app.clients.router import RouterOutput
        router_output = RouterOutput(mode=1, reason="분류 실패 - 기본 모드")
        router_result = {"mode": 1, "reason": "분류 실패 - 기본 모드"}
        router_error = str(exc)
    t1 = time.perf_counter()

    steps.append(_step(
        "Router AI",
        "사용자 메시지를 분석하여 8개 모드 중 하나로 분류",
        {"user_message": body.user_message},
        {**router_result, "mode_name": _MODE_NAMES.get(router_output.mode, "알 수 없음"), "error": router_error},
        (t1 - t0) * 1000,
    ))

    mode = router_output.mode

    # ── Step 2: Vector DB 맥락 검색 ──
    t0 = time.perf_counter()
    context_text = await _fetch_context(pinecone, embed, body.user_id, body.user_message)
    t1 = time.perf_counter()

    steps.append(_step(
        "Vector DB",
        "Pinecone에서 사용자 이전 대화 맥락을 검색 (임베딩 → 유사도 검색)",
        {"user_id": body.user_id, "query": body.user_message},
        {"context_text": context_text},
        (t1 - t0) * 1000,
    ))

    # ── Step 3: db_modified_flag 결정 ──
    db_flag = get_db_modified_flag(mode)
    steps.append(_step(
        "DB Flag",
        "모드별 db_modified_flag 결정 (FastAPI가 판단, Gemini 아님)",
        {"mode": mode},
        {"db_modified_flag": db_flag},
        0.0,
    ))

    # ── Step 4: Worker 시스템 프롬프트 빌드 ──
    t0 = time.perf_counter()
    system_prompt = build_worker_system_prompt(
        mode=mode,
        user_profile=body.user_profile,
        context_text=context_text,
        user_instruction=body.user_instruction,
    )
    t1 = time.perf_counter()

    steps.append(_step(
        "Prompt Builder",
        "모드별 시스템 지시사항 + 사용자 프로필 + 맥락을 결합하여 워커 프롬프트 생성",
        {
            "mode": mode,
            "user_profile": body.user_profile.model_dump(exclude_none=True),
            "context_text": context_text[:200] + "..." if len(context_text) > 200 else context_text,
            "user_instruction": body.user_instruction or "(없음)",
        },
        {"system_prompt_preview": system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt,
         "prompt_length": len(system_prompt)},
        (t1 - t0) * 1000,
    ))

    # ── Step 5: WAS 조건부 호출 ──
    user_content = body.user_message
    was_data = None
    was_error = None

    if mode in (3, 5):
        t0 = time.perf_counter()
        try:
            if mode == 3:
                was_list = await was.fetch_exercise_list(body.user_id)
                user_content = f"{body.user_message}\n\n현재 운동 계획:\n{json.dumps(was_list, ensure_ascii=False)}"
            else:
                was_list = await was.fetch_meal_list(body.user_id)
                user_content = f"{body.user_message}\n\n현재 식단 계획:\n{json.dumps(was_list, ensure_ascii=False)}"
            was_data = was_list
        except Exception as exc:
            was_error = str(exc)
        t1 = time.perf_counter()

        steps.append(_step(
            "WAS Call",
            f"모드 {mode}: WAS에서 {'운동' if mode == 3 else '식단'} 리스트 조회",
            {"user_id": body.user_id, "endpoint": f"{'exercise' if mode == 3 else 'meal'}-list"},
            {"data": was_data, "error": was_error},
            (t1 - t0) * 1000,
        ))
    else:
        steps.append(_step(
            "WAS Call",
            f"모드 {mode}: WAS 호출 불필요 (모드 3, 5만 해당)",
            {"mode": mode},
            {"skipped": True, "reason": "모드 3, 5만 WAS 호출"},
            0.0,
        ))

    # ── Step 6: Gemini 워커 호출 ──
    response_schema = _MODE_SCHEMA_MAP.get(mode, SimpleAnswerOutput)
    t0 = time.perf_counter()
    gemini_error = None
    raw_json = None
    parsed = None
    try:
        raw_json = await gemini.generate(
            system_prompt=system_prompt,
            user_content=user_content,
            response_schema=response_schema,
        )
        parsed = json.loads(raw_json)
    except Exception as exc:
        gemini_error = str(exc)
    t1 = time.perf_counter()

    steps.append(_step(
        "Gemini Worker",
        f"Gemini Flash에 모드 {mode} 스키마({response_schema.__name__})로 JSON 생성 요청",
        {
            "system_prompt_length": len(system_prompt),
            "user_content_preview": user_content[:300] + "..." if len(user_content) > 300 else user_content,
            "response_schema": response_schema.__name__,
        },
        {"raw_json": parsed, "error": gemini_error},
        (t1 - t0) * 1000,
    ))

    # ── Step 7: 응답 구성 ──
    final_response = None
    if parsed is not None:
        chat_data = _build_ai_chat_data(mode, parsed)
        final_response = {
            "status": "success",
            "mode": mode,
            "data": chat_data.model_dump(),
            "db_modified_flag": db_flag,
        }

    steps.append(_step(
        "Response Build",
        "Gemini JSON → AiChatData 변환 + 최종 응답 구성",
        {"mode": mode, "parsed_json": parsed},
        {"final_response": final_response},
        0.0,
    ))

    # ── Step 8: Vector DB 저장 (요약 → 임베딩 → Pinecone upsert) ──
    summary_text = None
    vector_id = None
    save_error = None
    t0 = time.perf_counter()
    if parsed is not None:
        try:
            summary_prompt = build_summary_prompt()
            ai_response_text = json.dumps(parsed, ensure_ascii=False)
            user_content = f"질문: {body.user_message}\n답변: {ai_response_text}"
            raw_summary = await gemini.generate(
                system_prompt=summary_prompt,
                user_content=user_content,
                response_schema=SummaryOutput,
            )
            summary_text = json.loads(raw_summary)["summary"]
            vector = await embed.embed(summary_text)
            vector_id = await pinecone.upsert(
                user_id=body.user_id,
                vector=vector,
                summary=summary_text,
            )
        except Exception as exc:
            save_error = str(exc)
            logger.error("ai-chat-debug vector save 실패: %s", save_error)
    t1 = time.perf_counter()

    steps.append(_step(
        "Vector DB 저장",
        "대화 요약(Gemini) → 임베딩 → Pinecone upsert",
        {"user_id": body.user_id, "user_message": body.user_message},
        {"summary": summary_text, "vector_id": vector_id, "error": save_error,
         "skipped": parsed is None},
        (t1 - t0) * 1000,
    ))

    total_elapsed = (time.perf_counter() - total_start) * 1000

    return {
        "total_elapsed_ms": round(total_elapsed, 1),
        "mode": mode,
        "mode_name": _MODE_NAMES.get(mode, "알 수 없음"),
        "steps": steps,
        "final_response": final_response,
    }


@router.post("/debug/process-meal")
async def debug_process_meal(body: ProcessMealRequest, request: Request) -> dict:
    """Process Meal 파이프라인을 단계별로 실행하여 각 단계 입출력을 반환한다."""
    steps: list[dict] = []
    total_start = time.perf_counter()

    gemini = request.app.state.gemini_client
    pinecone = request.app.state.pinecone_client
    embed = request.app.state.embed_client

    # ── Step 1: Vector DB 맥락 검색 ──
    t0 = time.perf_counter()
    context_text = await _fetch_context(pinecone, embed, body.user_id, body.user_message)
    t1 = time.perf_counter()
    steps.append(_step(
        "Vector DB",
        "Pinecone에서 사용자 이전 대화 맥락 검색",
        {"user_id": body.user_id, "query": body.user_message},
        {"context_text": context_text},
        (t1 - t0) * 1000,
    ))

    # ── Step 2: 시스템 프롬프트 빌드 ──
    t0 = time.perf_counter()
    system_prompt = build_meal_system_prompt(body.user_profile, context_text)
    t1 = time.perf_counter()
    steps.append(_step(
        "Prompt Builder",
        "식단 분석 시스템 프롬프트 생성",
        {
            "user_profile": body.user_profile.model_dump(exclude_none=True),
            "context_text": context_text[:200] + "..." if len(context_text) > 200 else context_text,
        },
        {"system_prompt_preview": system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt},
        (t1 - t0) * 1000,
    ))

    # ── Step 3: Gemini 호출 ──
    t0 = time.perf_counter()
    raw_json = None
    parsed = None
    gemini_error = None
    try:
        raw_json = await gemini.generate(
            system_prompt=system_prompt,
            user_content=body.user_message,
            response_schema=MealAnalysisData,
        )
        parsed = json.loads(raw_json)
    except Exception as exc:
        gemini_error = str(exc)
    t1 = time.perf_counter()
    steps.append(_step(
        "Gemini Worker",
        "Gemini Flash로 식단 분석 (calories, message)",
        {"user_message": body.user_message, "response_schema": "MealAnalysisData"},
        {"raw_json": parsed, "error": gemini_error},
        (t1 - t0) * 1000,
    ))

    final_response = None
    if parsed is not None:
        final_response = {"status": "success", "data": parsed}

    return {
        "total_elapsed_ms": round((time.perf_counter() - total_start) * 1000, 1),
        "steps": steps,
        "final_response": final_response,
    }


@router.post("/debug/recommend")
async def debug_recommend(body: RecommendRequest, request: Request) -> dict:
    """Recommend 파이프라인을 단계별로 실행하여 각 단계 입출력을 반환한다."""
    steps: list[dict] = []
    total_start = time.perf_counter()

    gemini = request.app.state.gemini_client
    pinecone = request.app.state.pinecone_client
    embed = request.app.state.embed_client

    # ── Step 1: Vector DB 맥락 검색 ──
    t0 = time.perf_counter()
    context_text = await _fetch_context(pinecone, embed, body.user_id, body.user_instruction)
    t1 = time.perf_counter()
    steps.append(_step(
        "Vector DB",
        "Pinecone에서 사용자 이전 대화 맥락 검색",
        {"user_id": body.user_id, "query": body.user_instruction},
        {"context_text": context_text},
        (t1 - t0) * 1000,
    ))

    # ── Step 2: 시스템 프롬프트 빌드 ──
    t0 = time.perf_counter()
    system_prompt = build_recommend_system_prompt(body.user_profile, context_text)
    t1 = time.perf_counter()
    steps.append(_step(
        "Prompt Builder",
        "추천 시스템 프롬프트 생성",
        {
            "user_profile": body.user_profile.model_dump(exclude_none=True),
            "context_text": context_text[:200] + "..." if len(context_text) > 200 else context_text,
        },
        {"system_prompt_preview": system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt},
        (t1 - t0) * 1000,
    ))

    # ── Step 3: Gemini 호출 ──
    t0 = time.perf_counter()
    raw_json = None
    parsed = None
    gemini_error = None
    try:
        raw_json = await gemini.generate(
            system_prompt=system_prompt,
            user_content=body.user_instruction,
            response_schema=RecommendationData,
        )
        parsed = json.loads(raw_json)
    except Exception as exc:
        gemini_error = str(exc)
    t1 = time.perf_counter()
    steps.append(_step(
        "Gemini Worker",
        "Gemini Flash로 운동/식단 추천 생성",
        {"user_instruction": body.user_instruction, "response_schema": "RecommendationData"},
        {"raw_json": parsed, "error": gemini_error},
        (t1 - t0) * 1000,
    ))

    final_response = None
    if parsed is not None:
        final_response = {"status": "success", "data": parsed}

    return {
        "total_elapsed_ms": round((time.perf_counter() - total_start) * 1000, 1),
        "steps": steps,
        "final_response": final_response,
    }


@router.post("/debug/vector-search")
async def debug_vector_search(body: VectorSearchRequest, request: Request) -> dict:
    """쿼리 텍스트를 임베딩하여 Pinecone에서 유사 벡터를 검색하고 결과를 반환한다."""
    embed = request.app.state.embed_client
    pinecone = request.app.state.pinecone_client

    # Step 1: embedding
    embed_error = None
    vector: list[float] = []
    t0 = time.perf_counter()
    try:
        vector = await embed.embed(body.query)
    except Exception as exc:
        embed_error = f"{type(exc).__name__}: {exc}"
        logger.error("debug/vector-search embed 실패: %s", embed_error)
    embed_elapsed = (time.perf_counter() - t0) * 1000

    if embed_error:
        return {
            "user_id": body.user_id,
            "query": body.query,
            "embed_elapsed_ms": round(embed_elapsed, 1),
            "embed_error": embed_error,
            "search_elapsed_ms": 0.0,
            "search_error": None,
            "result_count": 0,
            "results": [],
        }

    # Step 2: vector search
    search_error = None
    results: list[dict] = []
    t0 = time.perf_counter()
    try:
        results = await pinecone.search(body.user_id, vector, top_k=body.top_k)
    except Exception as exc:
        search_error = f"{type(exc).__name__}: {exc}"
        logger.error("debug/vector-search pinecone 실패: %s", search_error)
    search_elapsed = (time.perf_counter() - t0) * 1000

    return {
        "user_id": body.user_id,
        "query": body.query,
        "embed_elapsed_ms": round(embed_elapsed, 1),
        "embed_error": None,
        "search_elapsed_ms": round(search_elapsed, 1),
        "search_error": search_error,
        "result_count": len(results),
        "results": results,
    }


@router.post("/debug/vector-upsert")
async def debug_vector_upsert(body: VectorUpsertRequest, request: Request) -> dict:
    """요약 텍스트를 임베딩하여 Pinecone에 저장하고 생성된 ID를 반환한다."""
    embed = request.app.state.embed_client
    pinecone = request.app.state.pinecone_client

    # Step 1: embedding
    embed_error = None
    vector: list[float] = []
    t0 = time.perf_counter()
    try:
        vector = await embed.embed(body.summary)
    except Exception as exc:
        embed_error = f"{type(exc).__name__}: {exc}"
        logger.error("debug/vector-upsert embed 실패: %s", embed_error)
    embed_elapsed = (time.perf_counter() - t0) * 1000

    if embed_error:
        return {
            "user_id": body.user_id,
            "summary": body.summary,
            "embed_elapsed_ms": round(embed_elapsed, 1),
            "embed_error": embed_error,
            "upsert_elapsed_ms": 0.0,
            "upsert_error": None,
            "vector_id": None,
        }

    # Step 2: upsert
    upsert_error = None
    vector_id = None
    t0 = time.perf_counter()
    try:
        vector_id = await pinecone.upsert(body.user_id, vector, body.summary)
    except Exception as exc:
        upsert_error = f"{type(exc).__name__}: {exc}"
        logger.error("debug/vector-upsert pinecone 실패: %s", upsert_error)
    upsert_elapsed = (time.perf_counter() - t0) * 1000

    return {
        "user_id": body.user_id,
        "summary": body.summary,
        "embed_elapsed_ms": round(embed_elapsed, 1),
        "embed_error": None,
        "upsert_elapsed_ms": round(upsert_elapsed, 1),
        "upsert_error": upsert_error,
        "vector_id": vector_id,
    }


@router.post("/debug/was-test")
async def debug_was_test(body: WASTestRequest, request: Request) -> dict:
    """WAS REST 통신 상태를 직접 테스트한다.

    exercise-list, meal-list 두 엔드포인트를 각각 호출하여
    응답 상태, 데이터, 소요시간, 오류를 반환한다.
    """
    was = request.app.state.was_client
    results: dict = {}

    for endpoint_key, fetch_fn in (
        ("exercise_list", lambda: was.fetch_exercise_list(body.user_id)),
        ("meal_list", lambda: was.fetch_meal_list(body.user_id)),
    ):
        t0 = time.perf_counter()
        try:
            data = await fetch_fn()
            results[endpoint_key] = {
                "status": "ok",
                "data": data,
                "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1),
                "error": None,
            }
        except Exception as exc:
            results[endpoint_key] = {
                "status": "error",
                "data": None,
                "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1),
                "error": str(exc),
            }

    overall_ok = all(r["status"] == "ok" for r in results.values())
    return {
        "user_id": body.user_id,
        "overall": "ok" if overall_ok else "error",
        "endpoints": results,
    }


@router.get("/debug/system-prompts")
async def debug_system_prompts() -> dict:
    """Router AI / Worker AI 시스템 지침서 전문을 반환한다."""
    return {
        "router": ROUTER_SYSTEM_PROMPT,
        "worker_common": _COMMON_RULES + "\n" + _CAUTION,
        "worker_modes": {
            str(mode): instruction
            for mode, instruction in _MODE_INSTRUCTIONS.items()
        },
        "mode_names": _MODE_NAMES,
    }
