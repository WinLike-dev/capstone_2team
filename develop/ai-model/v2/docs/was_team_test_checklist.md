# WAS Team Test Checklist

이 문서는 `/debug` 없이 `curl`로 `FastAPI /chat`과 `FastAPI /internal/events/profile-updated`를 호출하는 기준으로 정리한 WAS 팀용 체크리스트입니다.

관련 문서:
- [was_api_contract.md](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_api_contract.md)
- [was_test_scenarios.md](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_test_scenarios.md)
- [was_team_curl_guide.md](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_team_curl_guide.md)

## 1. 현재 구조 먼저 이해하기

현재 구조는 아래와 같습니다.

1. 사용자 메시지는 `FastAPI /chat`으로 들어갑니다.
2. FastAPI가 필요할 때 WAS에서 프로필/플랜을 읽습니다.
3. FastAPI가 필요할 때 WAS에 프로필/플랜을 저장합니다.
4. WAS가 프로필 변경 사실을 FastAPI에 알려야 할 때는 `POST /internal/events/profile-updated`를 보냅니다.

즉, WAS 팀 테스트에서 중요한 호출은 아래 2가지입니다.
- `POST /chat`
- `POST /internal/events/profile-updated`

## 2. WAS 팀이 먼저 준비해야 하는 것

### 테스트 유저
- `user_id` 1개 이상
- 예: `test-user-1`

### 프로필 데이터
- `weight`
- `height`
- `age`
- `gender`
- `goal`
- `activity_level`
- `diet_type`
- `allergies`
- `injury_history`
- `selected_ai_persona`

### 오늘 플랜 데이터
- `GET /api/plan/today/{user_id}`에서 최소 1개 item
- 각 item에 `id`, `name`, `detail`, `day`, `completed`가 들어 있는 것이 좋습니다

### 전체 운동/식단 플랜 데이터
- `GET /api/workout-plan/full/{user_id}`
- `GET /api/diet-plan/full/{user_id}`
- 수정 테스트를 위해 실제로 읽을 수 있는 데이터가 있어야 합니다

## 3. 테스트 전에 반드시 맞춰야 할 계약

아래 네 가지는 먼저 합의하고 시작하는 것이 좋습니다.

1. `GET /api/user/profile/{user_id}` 응답에 `selected_ai_persona`가 포함되는가
2. `GET /api/plan/today/{user_id}` 응답에 `id`가 있는가
3. `PUT /api/plan/update/{user_id}`가 전체 계획 교체형인가
4. `POST /internal/events/profile-updated`를 WAS에서 보낼 수 있는가

## 4. curl 테스트 기본 준비

리눅스나 WSL 기준으로 아래 변수를 먼저 잡고 시작하면 편합니다.

```bash
export FASTAPI_BASE="http://158.179.165.73:8000"
export USER_ID="test-user-1"
export SESSION_ID="was-test-session-01"
```

세션을 새로 시작하고 싶으면 `SESSION_ID`만 바꾸면 됩니다.

```bash
export SESSION_ID="was-test-session-02"
```

## 5. WAS 팀이 직접 하는 기본 호출

### 5-1. 첫 메시지 보내기

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"안녕\"
  }"
```

확인할 것:
- FastAPI 응답이 정상으로 오는지
- 이 첫 턴에서 FastAPI가 WAS의 프로필과 오늘 플랜을 읽을 수 있는지

### 5-2. 프로필 수정 메시지 보내기

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"체중 71.8로 바꿔줘\"
  }"
```

확인할 것:
- 응답이 먼저 오는지
- 이후 WAS DB 또는 `GET /api/user/profile/{user_id}` 재조회 시 체중이 바뀌는지

### 5-3. 오늘 플랜 완료 메시지 보내기

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"오늘 운동 완료했어\"
  }"
```

확인할 것:
- `PUT /api/plan/check/{user_id}`가 호출되는지
- `today_plan` 재조회 시 해당 item의 `completed`가 바뀌는지

### 5-4. 계획 생성 제안 받기

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"운동 계획 짜줘\"
  }"
```

확인할 것:
- 이 단계에서는 WAS 저장이 없어야 합니다
- 응답에 승인 질문이 붙는지 봅니다

### 5-5. 생성안 승인하기

중요: 바로 직전과 같은 `SESSION_ID`를 계속 써야 합니다.

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"좋아, 이대로 진행해줘\"
  }"
```

확인할 것:
- `POST /api/plan/create/{user_id}`가 WAS 쪽에서 정상 처리되는지
- 생성안 승인 전에는 저장이 없고, 승인 후에만 저장되는지

### 5-6. 계획 수정 제안 받기

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"운동 계획 조금 수정해줘\"
  }"
```

확인할 것:
- `GET /api/workout-plan/full/{user_id}` 또는 `GET /api/diet-plan/full/{user_id}`가 먼저 가능해야 합니다
- 이 단계에서도 바로 저장되면 안 됩니다

### 5-7. 수정안 승인하기

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"수정안으로 반영해줘\"
  }"
```

확인할 것:
- `PUT /api/plan/update/{user_id}`가 정상 처리되는지
- 전체 계획이 기대한 형태로 바뀌는지

## 6. profile-updated 이벤트 테스트

WAS가 프로필을 직접 수정한 뒤, FastAPI에 변경 사실만 알려주는 테스트입니다.

```bash
curl -X POST "$FASTAPI_BASE/internal/events/profile-updated" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"changed_fields\": [\"selected_ai_persona\"],
    \"profile_version\": 2
  }"
```

그 다음 같은 사용자가 다음 메시지를 보냅니다.

```bash
curl -X POST "$FASTAPI_BASE/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"user_message\": \"안녕\"
  }"
```

확인할 것:
- 이벤트 직후 바로 바뀌는 것이 아니라, 다음 턴에 최신 프로필이 다시 읽히는지
- persona가 실제로 새 값으로 반영되는지

## 7. WAS 팀이 시나리오별로 확인해야 할 핵심

### 읽기 중심 시나리오
- 첫 메시지 초기 로드
- 계획 수정 시 full plan 조회

확인 포인트:
- 필요한 WAS API가 실제로 호출 가능한지
- 응답 shape가 문서와 맞는지

### 쓰기 중심 시나리오
- 프로필 수정
- 오늘 플랜 체크
- 계획 생성 승인
- 계획 수정 승인

확인 포인트:
- 응답이 먼저 오고 저장은 뒤에서 되는지
- 저장 후 DB 값이 실제로 바뀌는지

### 이벤트 중심 시나리오
- `profile-updated`

확인 포인트:
- FastAPI가 이벤트를 받고 다음 턴에서 최신 프로필을 다시 읽는지

## 8. 가장 먼저 해보면 좋은 테스트 5개

시간이 부족하면 아래 다섯 개부터 보면 됩니다.

1. 첫 메시지 초기 로드
2. 프로필 수정
3. 오늘 플랜 체크 완료
4. 계획 수정 제안 -> 승인
5. profile-updated -> 다음 턴 반영

## 9. 테스트 중 문제 생기면 먼저 볼 것

1. `user_id`가 실제로 WAS DB에 있는지
2. `SESSION_ID`를 승인 전후에 같은 값으로 유지했는지
3. `today_plan`에 실제 `id`가 있는지
4. full workout/diet plan 조회 API가 실제로 열려 있는지
5. `selected_ai_persona`가 profile 응답에 실제로 들어오는지

## 10. 다음에 함께 보면 좋은 문서

- [was_team_curl_guide.md](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/was_team_curl_guide.md)
  - 시나리오 11개를 curl 예시 기준으로 하나씩 정리한 실행 가이드
