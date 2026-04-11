# WAS Team Curl Guide

이 문서는 WAS 팀이 `/debug` 없이 `curl`만으로 FastAPI 연동을 테스트하는 가이드입니다.

관련 문서:
- [was_team_test_checklist.md](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_team_test_checklist.md)
- [was_test_scenarios.md](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_test_scenarios.md)

## 1. 공통 변수

```bash
export FASTAPI_BASE="http://158.179.165.73:8000"
export USER_ID="test-user-1"
export SESSION_ID="was-test-session-01"
```

새로운 세션 테스트가 필요하면 `SESSION_ID`만 바꿉니다.

```bash
export SESSION_ID="was-test-session-02"
```

## 2. 시나리오별 curl 예시

### 시나리오 01. 첫 메시지 초기 로드

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"안녕\"
  }"
```

WAS 팀 확인:
- `GET /api/user/profile/{user_id}` 호출 준비가 되어 있어야 합니다
- `GET /api/plan/today/{user_id}` 호출 준비가 되어 있어야 합니다

### 시나리오 02. 캐주얼 또는 fallback

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"고마워\"
  }"
```

WAS 팀 확인:
- 활성 세션이면 추가 저장이 없어야 합니다

### 시나리오 03. 정보 질문

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"단백질은 하루에 얼마나 먹어야 해?\"
  }"
```

WAS 팀 확인:
- 일반적으로 저장은 없어야 합니다

### 시나리오 04. 공감/케어

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"오늘 너무 지쳐서 운동하기 싫어\"
  }"
```

WAS 팀 확인:
- 저장은 없어야 합니다

### 시나리오 05. 프로필 변경

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"앞으로 warm로 말해줘\"
  }"
```

또는

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"체중 71.8로 바꿔줘\"
  }"
```

WAS 팀 확인:
- `PUT /api/user/profile/{user_id}` 후 DB 값이 바뀌는지

### 시나리오 06. 오늘 플랜 체크 완료

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"오늘 운동 완료했어\"
  }"
```

WAS 팀 확인:
- `PUT /api/plan/check/{user_id}` 후 해당 item이 완료 처리되는지

### 시나리오 07. 계획 생성 제안

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"운동 계획 짜줘\"
  }"
```

WAS 팀 확인:
- 이 단계에서는 저장이 없어야 합니다

### 시나리오 08. 계획 수정 제안

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"운동 계획 조금 수정해줘\"
  }"
```

WAS 팀 확인:
- `GET /api/workout-plan/full/{user_id}` 또는 `GET /api/diet-plan/full/{user_id}`가 정상이어야 합니다
- 이 단계에서도 저장은 없어야 합니다

### 시나리오 09. 생성안 승인

시나리오 07 바로 다음에 같은 `SESSION_ID`로 실행합니다.

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"좋아, 이대로 진행해줘\"
  }"
```

WAS 팀 확인:
- `POST /api/plan/create/{user_id}`가 실제 저장되는지

### 시나리오 10. 수정안 승인

시나리오 08 바로 다음에 같은 `SESSION_ID`로 실행합니다.

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"수정안으로 반영해줘\"
  }"
```

WAS 팀 확인:
- `PUT /api/plan/update/{user_id}`가 실제 저장되는지

### 시나리오 11. profile-updated 이벤트 후 다음 턴 반영

먼저 WAS가 이벤트를 보냅니다.

```bash
curl -X POST "$FASTAPI_BASE/internal/events/profile-updated" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"changed_fields\": [\"selected_ai_persona\"],
    \"profile_version\": 2
  }"
```

그 다음 사용자의 다음 턴을 보냅니다.

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"안녕\"
  }"
```

WAS 팀 확인:
- 다음 턴에서 최신 프로필이 다시 읽히는지

## 3. 가장 실수하기 쉬운 부분

### 승인 테스트에서는 `SESSION_ID`를 바꾸면 안 됩니다

예:
- 시나리오 07과 시나리오 09는 같은 세션이어야 합니다
- 시나리오 08과 시나리오 10도 같은 세션이어야 합니다

### 오늘 플랜 체크는 `today_plan`에 `id`가 있어야 합니다

`PUT /api/plan/check/{user_id}`는 item 식별이 필요하므로, `GET /api/plan/today/{user_id}` 데이터에 `id`가 있어야 합니다.

### profile-updated는 즉시 반영이 아니라 다음 턴 반영입니다

이벤트를 보낸 직후 바로 바뀌는 것이 아니라, 다음 `/chat`에서 최신 프로필을 다시 읽습니다.
