#!/usr/bin/env python3
from __future__ import annotations

import json
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


BACKEND_BASE_URL = "https://34.50.45.68.nip.io"
AI_DEBUG_BASE_URL = "http://34.50.21.162:8000"
HTTP_TIMEOUT = 45
TRACE_POLL_TIMEOUT = 20
PLAN_POLL_TIMEOUT = 25
SUMMARY_PATH = Path(__file__).with_name("latest_e2e_intent_suite_summary.json")

INTENT_CASES: dict[str, list[str]] = {
    "casual": [
        "안녕",
        "고마워",
        "반가워",
        "굿밤",
        "바이",
    ],
    "공감_케어": [
        "요즘 운동 의욕이 너무 없어져서 속상해.",
        "식단을 계속 실패해서 자책하게 돼.",
        "운동해도 달라지는 게 없는 것 같아 우울해.",
        "몸이 예전 같지 않아서 자신감이 줄어들어.",
        "계획대로 못 지켜서 스트레스가 너무 커.",
    ],
    "기록": [
        "오늘 몸무게 71.8kg으로 기록해줘.",
        "무릎 부상 이력이 있어. 부상 이력에 추가해줘.",
        "오늘 체중 72.1kg으로 저장해줘.",
        "알레르기에 새우 추가해줘.",
        "키를 176cm로 수정 기록해줘.",
    ],
    "계획": [
        "이번 주 주 4회 근력 운동 계획 짜줘.",
        "감량 목표로 일주일 식단 계획 만들어줘.",
        "오늘 저녁 30분 홈트 루틴 추천해줘.",
        "다음 주 유산소 중심 운동 플랜 짜줘.",
        "내일 아침 단백질 위주 식단 추천해줘.",
    ],
    "수정": [
        "이번 주 계획 강도를 조금 낮춰줘.",
        "목요일 하체 운동을 수요일로 바꿔줘.",
        "저녁 식단을 좀 더 가볍게 바꿔줘.",
        "무릎 부담 적게 운동 계획을 다시 조정해줘.",
        "이번 주 식단에서 유제품을 빼고 수정해줘.",
    ],
    "정보": [
        "감량 중에는 단백질을 많이 먹어야 해?",
        "HIIT를 주 몇 번 하는 게 좋아?",
        "운동 전에 탄수화물 먹는 게 왜 중요해?",
        "근력 운동 후 유산소를 하면 효과가 줄어들어?",
        "하루 물은 얼마나 마시는 게 좋아?",
    ],
    "안전경고": [
        "운동하다가 가슴이 조여오고 숨이 차.",
        "운동 중에 어지럽고 쓰러질 것 같아.",
        "약을 과다 복용한 것 같은데 운동해도 될까?",
        "죽고 싶을 만큼 힘든데 운동으로 버티면 괜찮을까?",
        "자해 충동이 심한데 그냥 걸으면 나아질까?",
    ],
    "fallback": [
        "그거 좀 다르게 해줘.",
        "아까 말한 거 기준으로 다시 해줘.",
        "다른 관점으로 풀어봐.",
        "그 방식 말고 다른 걸로.",
        "그거 그대로 말고 좀 수정.",
    ],
}

APPROVAL_CASES: list[tuple[str, str]] = [
    ("이번 주 유산소 중심 운동 계획을 구체적으로 짜줘.", "좋아, 그 계획으로 진행해줘."),
    ("내일 아침 단백질 위주 식단 계획 자세히 짜줘.", "응, 이대로 반영해줘."),
    ("이번 주 운동 계획 강도를 조금 낮춰서 다시 짜줘.", "확인했어, 그렇게 저장해줘."),
    ("이번 주 식단에서 유제품을 빼는 수정안을 만들어줘.", "좋아, 그대로 적용해줘."),
    ("주말 포함 5일 운동 계획 새로 짜줘.", "확정할게, 이대로 해줘."),
]


@dataclass
class HttpResponse:
    status: int
    body: Any


@dataclass
class ChatTraceResult:
    message: str
    expected_intent: str
    actual_intent: str | None
    response_text: str
    trace_intent: str | None
    proposed_plan_count: int
    proposed_plan_action: str | None
    session_id: str | None
    ok: bool


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def _json_request(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = HTTP_TIMEOUT,
) -> HttpResponse:
    data = None
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    context = ssl._create_unverified_context() if url.startswith("https://") else None

    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            raw = response.read().decode("utf-8", "replace")
            body = json.loads(raw) if raw else None
            return HttpResponse(status=response.getcode(), body=body)
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", "replace")
        try:
            body = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            body = {"raw": raw}
        return HttpResponse(status=error.code, body=body)


def _query_request(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: int = HTTP_TIMEOUT,
) -> HttpResponse:
    request = urllib.request.Request(url, headers=headers or {}, method="GET")
    context = ssl._create_unverified_context() if url.startswith("https://") else None

    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            raw = response.read().decode("utf-8", "replace")
            body = json.loads(raw) if raw else None
            return HttpResponse(status=response.getcode(), body=body)
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", "replace")
        try:
            body = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            body = {"raw": raw}
        return HttpResponse(status=error.code, body=body)


def auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "ngrok-skip-browser-warning": "true",
    }


def create_test_user() -> tuple[str, dict[str, Any]]:
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    login_id = f"intent_test_{stamp}"
    password = "CapstoneTest!123"
    nickname = f"intent-{stamp[-6:]}"
    email = f"{login_id}@example.com"

    signup_res = _json_request(
        "POST",
        f"{BACKEND_BASE_URL}/api/v1/auth/signup",
        {
            "login_id": login_id,
            "password": password,
            "nickname": nickname,
            "email": email,
        },
    )
    if signup_res.status != 201:
        raise RuntimeError(f"signup failed: status={signup_res.status} body={signup_res.body}")

    login_res = _json_request(
        "POST",
        f"{BACKEND_BASE_URL}/api/v1/auth/login",
        {"login_id": login_id, "password": password},
    )
    if login_res.status != 200:
        raise RuntimeError(f"login failed: status={login_res.status} body={login_res.body}")

    return login_res.body["token"], login_res.body["user"]


def save_profile(token: str) -> None:
    response = _json_request(
        "POST",
        f"{BACKEND_BASE_URL}/api/v1/users/profile",
        {
            "mbti": "ISTJ",
            "gender": "male",
            "age": 25,
            "height": 175,
            "weight": 72,
            "goal": "fat_loss",
            "activity_level": "moderate",
            "medical_history": [],
            "allergies": [],
            "diet_type": "balanced",
            "injury_history": [],
        },
        headers=auth_headers(token),
    )
    if response.status != 200:
        raise RuntimeError(f"profile save failed: status={response.status} body={response.body}")


def get_calendar(token: str, start_date: str, end_date: str) -> dict[str, Any]:
    query = urllib.parse.urlencode({"start_date": start_date, "end_date": end_date})
    response = _query_request(
        f"{BACKEND_BASE_URL}/api/v1/users/calendar?{query}",
        headers=auth_headers(token),
    )
    if response.status != 200:
        raise RuntimeError(f"calendar load failed: status={response.status} body={response.body}")
    return response.body or {}


def normalize_calendar(calendar: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for date_key in sorted(calendar.keys()):
        payload = calendar.get(date_key) or {}
        exercises = payload.get("exercises") or []
        meals = payload.get("meals") or []
        normalized[date_key] = {
            "exercise_count": len(exercises),
            "meal_count": len(meals),
            "exercise_names": sorted(
                [
                    ",".join(
                        item.get("exercise_name")
                        for item in (plan.get("exercise_items") or [])
                        if item.get("exercise_name")
                    )
                    or str(plan.get("exercise_type") or "")
                    for plan in exercises
                ]
            ),
            "meal_names": sorted(str(meal.get("food_name") or "") for meal in meals),
        }
    return normalized


def calendar_signature(calendar: dict[str, Any]) -> str:
    return json.dumps(normalize_calendar(calendar), ensure_ascii=False, sort_keys=True)


def chat(token: str, message: str, session_id: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"user_message": message}
    if session_id:
        payload["session_id"] = session_id

    response = _json_request(
        "POST",
        f"{BACKEND_BASE_URL}/api/v1/chat",
        payload,
        headers=auth_headers(token),
        timeout=HTTP_TIMEOUT,
    )
    if response.status != 200:
        raise RuntimeError(f"chat failed: status={response.status} body={response.body}")
    return response.body


def list_traces(limit: int = 200) -> list[dict[str, Any]]:
    response = _query_request(f"{AI_DEBUG_BASE_URL}/debug/api/traces?limit={limit}", timeout=HTTP_TIMEOUT)
    if response.status != 200:
        raise RuntimeError(f"trace list failed: status={response.status} body={response.body}")
    return response.body or []


def get_trace(trace_id: str) -> dict[str, Any]:
    response = _query_request(f"{AI_DEBUG_BASE_URL}/debug/api/traces/{trace_id}", timeout=HTTP_TIMEOUT)
    if response.status != 200:
        raise RuntimeError(f"trace detail failed: status={response.status} body={response.body}")
    return response.body or {}


def find_trace(user_id: str, session_id: str, message: str) -> dict[str, Any] | None:
    deadline = time.time() + TRACE_POLL_TIMEOUT
    while time.time() < deadline:
        for trace in list_traces():
            if (
                trace.get("user_id") == user_id
                and trace.get("session_id") == session_id
                and trace.get("message") == message
            ):
                return get_trace(trace["trace_id"])
        time.sleep(1.0)
    return None


def wait_for_calendar_change(
    token: str,
    start_date: str,
    end_date: str,
    baseline_signature: str,
) -> tuple[bool, dict[str, Any]]:
    deadline = time.time() + PLAN_POLL_TIMEOUT
    last_calendar: dict[str, Any] = {}
    while time.time() < deadline:
        current = get_calendar(token, start_date, end_date)
        last_calendar = current
        if calendar_signature(current) != baseline_signature:
            return True, current
        time.sleep(1.5)
    return False, last_calendar


def run_chat_case(
    token: str,
    user_id: str,
    message: str,
    expected_intent: str,
    session_id: str | None = None,
) -> ChatTraceResult:
    response = chat(token, message, session_id=session_id)
    resolved_session_id = response.get("session_id")
    trace = find_trace(user_id, resolved_session_id, message) if resolved_session_id else None
    trace_intent = (trace or {}).get("state_summary", {}).get("intent")
    proposed_plan_count = int((trace or {}).get("state_summary", {}).get("proposed_plan_count") or 0)
    proposed_plan_action = (trace or {}).get("state_summary", {}).get("proposed_plan_action")
    actual_intent = response.get("intent") or trace_intent

    return ChatTraceResult(
        message=message,
        expected_intent=expected_intent,
        actual_intent=actual_intent,
        response_text=str(response.get("response") or ""),
        trace_intent=trace_intent,
        proposed_plan_count=proposed_plan_count,
        proposed_plan_action=proposed_plan_action,
        session_id=resolved_session_id,
        ok=actual_intent == expected_intent,
    )


def print_group_result(title: str, results: list[ChatTraceResult]) -> None:
    passed = sum(1 for item in results if item.ok)
    print(f"\n[{title}] {passed}/{len(results)} passed")
    for item in results:
        status = "OK" if item.ok else "FAIL"
        print(
            f"- {status} expected={item.expected_intent} actual={item.actual_intent} "
            f"trace={item.trace_intent} proposed={item.proposed_plan_count} "
            f"action={item.proposed_plan_action} session={item.session_id} msg={item.message}"
        )


def run_simple_intent_groups(token: str, user_id: str) -> dict[str, list[ChatTraceResult]]:
    grouped_results: dict[str, list[ChatTraceResult]] = {}
    for expected_intent, messages in INTENT_CASES.items():
        results: list[ChatTraceResult] = []
        for message in messages:
            results.append(
                run_chat_case(
                    token=token,
                    user_id=user_id,
                    message=message,
                    expected_intent=expected_intent,
                    session_id=str(uuid.uuid4()),
                )
            )
        grouped_results[expected_intent] = results
        print_group_result(expected_intent, results)
    return grouped_results


def run_approval_group(token: str, user_id: str) -> list[ChatTraceResult]:
    results: list[ChatTraceResult] = []
    for seed_message, approval_message in APPROVAL_CASES:
        session_id = str(uuid.uuid4())
        seed_expected = "수정" if "수정" in seed_message else "계획"
        seed = run_chat_case(
            token=token,
            user_id=user_id,
            message=seed_message,
            expected_intent=seed_expected,
            session_id=session_id,
        )
        print(
            f"\n[approval-seed] expected={seed.expected_intent} actual={seed.actual_intent} "
            f"proposed={seed.proposed_plan_count} action={seed.proposed_plan_action} "
            f"session={seed.session_id} msg={seed.message}"
        )
        results.append(
            run_chat_case(
                token=token,
                user_id=user_id,
                message=approval_message,
                expected_intent="계획_승인",
                session_id=session_id,
            )
        )
        time.sleep(2.0)
    print_group_result("계획_승인", results)
    return results


def run_plan_state_checks(token: str, user_id: str) -> dict[str, Any]:
    year = str(datetime.now().year)
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    initial_calendar = get_calendar(token, start_date, end_date)
    initial_signature = calendar_signature(initial_calendar)

    empty_session_id = str(uuid.uuid4())
    empty_plan_prompt = run_chat_case(
        token=token,
        user_id=user_id,
        message="이번 주 주 3회 운동 계획을 구체적으로 짜줘.",
        expected_intent="계획",
        session_id=empty_session_id,
    )
    calendar_after_prompt = get_calendar(token, start_date, end_date)
    empty_state_still_empty = calendar_signature(calendar_after_prompt) == initial_signature

    empty_approval = run_chat_case(
        token=token,
        user_id=user_id,
        message="좋아, 그 계획으로 진행해줘.",
        expected_intent="계획_승인",
        session_id=empty_session_id,
    )
    create_changed, calendar_after_create = wait_for_calendar_change(
        token,
        start_date,
        end_date,
        initial_signature,
    )

    existing_signature = calendar_signature(calendar_after_create)
    update_session_id = str(uuid.uuid4())
    modify_prompt = run_chat_case(
        token=token,
        user_id=user_id,
        message="이번 주 운동 계획 강도를 조금 낮춰서 다시 조정해줘.",
        expected_intent="수정",
        session_id=update_session_id,
    )
    modify_approval = run_chat_case(
        token=token,
        user_id=user_id,
        message="응, 이대로 반영해줘.",
        expected_intent="계획_승인",
        session_id=update_session_id,
    )
    update_changed, calendar_after_update = wait_for_calendar_change(
        token,
        start_date,
        end_date,
        existing_signature,
    )

    result = {
        "initial_calendar": normalize_calendar(initial_calendar),
        "empty_plan_prompt": asdict(empty_plan_prompt),
        "empty_state_still_empty_after_prompt": empty_state_still_empty,
        "empty_state_approval": asdict(empty_approval),
        "empty_state_create_changed_calendar": create_changed,
        "calendar_after_create": normalize_calendar(calendar_after_create),
        "existing_plan_modify_prompt": asdict(modify_prompt),
        "existing_plan_modify_approval": asdict(modify_approval),
        "existing_state_update_changed_calendar": update_changed,
        "calendar_after_update": normalize_calendar(calendar_after_update),
    }

    print("\n[plan-state-check]")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def build_summary(
    user: dict[str, Any],
    plan_state_result: dict[str, Any],
    simple_results: dict[str, list[ChatTraceResult]],
    approval_results: list[ChatTraceResult],
) -> dict[str, Any]:
    return {
        "user_id": user["user_id"],
        "login_id": user["login_id"],
        "plan_state": plan_state_result,
        "intents": {
            intent: {
                "passed": sum(1 for item in results if item.ok),
                "total": len(results),
                "results": [asdict(item) for item in results],
            }
            for intent, results in simple_results.items()
        },
        "approval": {
            "passed": sum(1 for item in approval_results if item.ok),
            "total": len(approval_results),
            "results": [asdict(item) for item in approval_results],
        },
    }


def main() -> int:
    configure_stdout()

    token, user = create_test_user()
    user_id = user["user_id"]
    save_profile(token)

    print(f"[user] user_id={user_id} login_id={user['login_id']} nickname={user.get('nickname')}")

    plan_state_result = run_plan_state_checks(token, user_id)
    simple_results = run_simple_intent_groups(token, user_id)
    approval_results = run_approval_group(token, user_id)

    summary = build_summary(user, plan_state_result, simple_results, approval_results)
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n[summary-json]")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n[summary-file] {SUMMARY_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
