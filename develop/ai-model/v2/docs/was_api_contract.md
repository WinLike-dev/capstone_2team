# WAS Integration / API Contract

이 문서는 `ai-model/v2`와 WAS 사이의 실제 통신 계약을 정리한 문서입니다.

현재 기준 역할은 이렇게 나눕니다.

- 클라이언트는 **WAS**에 메시지를 보냅니다.
- WAS는 필요하면 `session_id`를 관리하고, FastAPI `POST /chat`을 호출합니다.
- FastAPI는 추론과 상태 관리를 담당합니다.
- FastAPI는 필요할 때 WAS에서 프로필/플랜을 읽고, 저장도 다시 WAS에 반영합니다.
- WAS는 프로필이 바뀌면 `POST /internal/events/profile-updated`로 FastAPI에 알려줍니다.

## 1. 통신 방향 요약

### Client -> WAS
- 사용자 메시지 입력
- WAS가 `session_id`를 생성하거나 기존 값을 재사용

### WAS -> FastAPI
- `POST /chat`
- `POST /internal/events/profile-updated`

### FastAPI -> WAS
- 사용자 프로필 조회
- 오늘 플랜 조회
- 전체 운동/식단 플랜 조회
- 프로필 수정 반영
- 플랜 생성
- 플랜 수정
- 플랜 체크 완료 반영

## 2. 권장 흐름

### 2.1 채팅 요청 흐름

1. 클라이언트가 WAS의 채팅 엔드포인트를 호출합니다.
2. WAS가 `session_id`를 확인합니다.
3. 세션이 없으면:
   - WAS가 새 `session_id`를 직접 만들거나
   - FastAPI에 `session_id` 없이 보내고, 응답으로 받은 `session_id`를 저장합니다.
4. WAS가 FastAPI `POST /chat`을 호출합니다.
5. FastAPI가 응답을 반환합니다.
6. WAS가 이 응답을 클라이언트에 다시 전달합니다.

### 2.2 프로필 변경 후 다음 턴 반영

1. WAS가 자체 DB의 프로필을 수정합니다.
2. WAS가 FastAPI 내부 엔드포인트 `POST /internal/events/profile-updated`를 호출합니다.
3. FastAPI는 변경 사실만 기록합니다.
4. 사용자의 다음 채팅 턴이 들어오면 FastAPI가 최신 프로필을 다시 읽습니다.

### 2.3 계획 승인 저장

1. 사용자가 계획 생성 또는 수정 제안을 받습니다.
2. 사용자가 승인 메시지를 보냅니다.
3. WAS가 같은 `session_id`로 FastAPI `POST /chat`을 호출합니다.
4. FastAPI는 background task에서 WAS 저장 API를 호출합니다.
5. 저장 성공 시에만 제안 플랜이 세션에서 정리됩니다.

## 3. WAS가 호출하는 FastAPI API

## 3.1 `POST /chat`

WAS가 사용자 메시지를 전달하는 메인 엔드포인트입니다.

### Request Body

| 필드 | 타입 | 필수 | 설명 |
|---|---|---:|---|
| `user_id` | `string` | O | 사용자 ID |
| `user_message` | `string` | O | 사용자 메시지 |
| `session_id` | `string` | X | 세션 ID. 없으면 FastAPI가 생성 |
| `user_profile_override` | `object` | X | 개발/디버그용 override |

### Request Example

```json
{
  "user_id": "user-123",
  "user_message": "운동 계획 짜줘",
  "session_id": "chat-session-001"
}
```

또는 첫 요청이라면:

```json
{
  "user_id": "user-123",
  "user_message": "안녕"
}
```

### Response Body

| 필드 | 타입 | 설명 |
|---|---|---|
| `status` | `string` | 기본값 `success` |
| `session_id` | `string` | 현재 세션 ID |
| `response` | `string` | 사용자에게 보여줄 응답 |
| `intent` | `string \| null` | 분류된 intent |
| `emotion` | `object \| null` | 감정 분석 결과 |
| `draft_response` | `string \| null` | Draft preview |
| `debug_state` | `object \| null` | 개발 환경 또는 override 요청에서만 노출 |

### Response Example

```json
{
  "status": "success",
  "session_id": "chat-session-001",
  "response": "이번 주는 주 4회 기준으로 전신/하체 분할로 가면 좋겠습니다. 이 방향으로 계획 제안할까요?",
  "intent": "계획",
  "emotion": {
    "label": "중립",
    "intensity": 0.2
  }
}
```

### session_id 규칙

- `session_id`를 WAS가 직접 관리해도 됩니다.
- `session_id` 없이 보내도 FastAPI가 자동 생성합니다.
- FastAPI가 생성한 경우, 응답의 `session_id`를 WAS가 저장하고 다음 턴부터 같은 값을 보내는 것을 권장합니다.

## 3.2 `POST /internal/events/profile-updated`

WAS가 프로필 변경 사실을 FastAPI에 push하는 내부 엔드포인트입니다.

### Request Body

| 필드 | 타입 | 필수 | 설명 |
|---|---|---:|---|
| `user_id` | `string` | O | 변경된 사용자 ID |
| `changed_fields` | `string[]` | X | 변경된 필드 목록 |
| `profile_version` | `int` | X | WAS가 관리하는 프로필 버전 |

### Request Example

```json
{
  "user_id": "user-123",
  "changed_fields": ["selected_ai_persona"],
  "profile_version": 7
}
```

### Response Example

```json
{
  "status": "success",
  "user_id": "user-123",
  "tracked_version": 7
}
```

## 4. FastAPI가 호출하는 WAS API

## 4.1 `GET /api/user/profile/{user_id}`

용도:
- 첫 세션 로드
- profile-updated 이후 다음 턴 refresh

예시 shape:

```json
{
  "user_id": "user-123",
  "weight": 72.5,
  "height": 175,
  "age": 25,
  "gender": "male",
  "diet_type": "balanced",
  "allergies": ["milk"],
  "injury_history": ["knee"],
  "goal": "fat_loss",
  "activity_level": "moderate",
  "selected_ai_persona": "warm"
}
```

## 4.2 `GET /api/plan/today/{user_id}`

용도:
- 첫 세션 로드
- 오늘 플랜 체크 처리

예시 shape:

```json
[
  {
    "id": "plan-item-1",
    "name": "하체 운동",
    "detail": "스쿼트 4세트",
    "day": "2026-04-11",
    "completed": false
  }
]
```

## 4.3 `GET /api/workout-plan/full/{user_id}`

용도:
- 운동 계획 수정 시 원본 전체 플랜 조회

## 4.4 `GET /api/diet-plan/full/{user_id}`

용도:
- 식단 계획 수정 시 원본 전체 플랜 조회

## 4.5 `PUT /api/user/profile/{user_id}`

용도:
- 체중, 목표, persona 등 프로필 변경 반영

## 4.6 `PUT /api/plan/check/{user_id}`

용도:
- 오늘 플랜 item 완료 체크 반영

요청 예시:

```json
{
  "item_id": "plan-item-1"
}
```

## 4.7 `POST /api/plan/create/{user_id}`

용도:
- 새 계획 승인 후 저장

요청 예시:

```json
{
  "plan_type": "workout",
  "items": [
    {
      "name": "전신 운동",
      "detail": "벤치프레스 4세트",
      "day": "2026-04-12",
      "ex_list": [
        {
          "exercise_name": "벤치프레스",
          "sets": 4
        }
      ]
    }
  ]
}
```

## 4.8 `PUT /api/plan/update/{user_id}`

용도:
- 기존 계획 수정 승인 후 저장

현재 v2는 **전체 계획 교체형 payload**를 보내는 것을 기준으로 합니다.

## 5. next-turn refresh 정책

현재 구조는 **push event + next-turn refresh**입니다.

의미:
- WAS는 프로필 변경 사실을 즉시 FastAPI에 알립니다.
- FastAPI는 현재 생성 중인 응답을 중간에 뒤집지 않습니다.
- 다음 `/chat` 요청이 들어왔을 때 최신 프로필을 다시 읽습니다.

이 정책의 이유:
- 현재 응답 생성 중 state를 강제로 바꾸지 않기 위해
- 구현을 단순하게 유지하기 위해

## 6. 실제 구현 파일

- FastAPI 채팅 라우터: [chat.py](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/app/routers/chat.py)
- 채팅 요청 스키마: [chat.py](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/app/schemas/chat.py)
- WAS 클라이언트: [was.py](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/app/clients/was.py)
- 프로필 이벤트 라우터: [profile_events.py](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/app/routers/profile_events.py)
- 프로필 sync tracker: [profile_sync.py](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/app/core/profile_sync.py)
- 다음 턴 refresh 로직: [preprocess.py](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/app/graph/nodes/preprocess.py)
