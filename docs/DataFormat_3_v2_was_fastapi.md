# [Specification] v2 WAS <-> FastAPI DataFormat

이 문서는 `develop/ai-model/v2` 기준으로 WAS와 FastAPI 사이의 API 데이터 포맷을 JSON 예시 중심으로 정리한 문서입니다.

범위:
- WAS -> FastAPI
- FastAPI -> WAS
- 요청 / 응답 JSON 예시
- 실제 런타임 기준 주의사항

## 1. 공통 규칙

### 1.1 GET 응답 래퍼 규칙

FastAPI의 WAS 클라이언트는 아래 두 형식을 모두 허용합니다.

형식 A: raw JSON

```json
{
  "user_id": "user-123"
}
```

형식 B: `data` 래퍼 포함

```json
{
  "status": "success",
  "data": {
    "user_id": "user-123"
  }
}
```

단, `GET /api/plan/today/{user_id}` 는 `data` 안쪽도 반드시 배열이어야 합니다.

정상 예시:

```json
{
  "status": "success",
  "data": [
    {
      "id": "plan-item-1",
      "name": "하체 운동",
      "detail": "스쿼트 4세트",
      "day": "monday",
      "completed": false
    }
  ]
}
```

비권장 예시:

```json
{
  "status": "success",
  "data": {
    "items": []
  }
}
```

위 형식은 현재 런타임에서 `today_plan` 배열로 바로 쓰기 어렵기 때문에 피하는 것이 좋습니다.

### 1.2 쓰기 API 성공 응답 규칙

FastAPI는 WAS 쓰기 API의 응답 body를 직접 사용하지 않습니다. 따라서 아래 둘 중 하나면 충분합니다.

- `200` 또는 `201` + JSON 응답
- `204 No Content`

권장 예시:

```json
{
  "status": "success"
}
```

### 1.3 FastAPI 공통 에러 응답 형식

FastAPI 쪽 에러는 아래 JSON 형식을 사용합니다.

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "에러 메시지"
  }
}
```

## 2. WAS -> FastAPI API

## 2.1 채팅 요청

- Method: `POST`
- Path: `/chat`
- 설명:
  - 사용자 메시지를 FastAPI에 보내고, 최종 응답을 받는 메인 API입니다.

### Request JSON

```json
{
  "user_id": "user-123",
  "user_message": "이번 주 주 4회 운동 계획 짜줘",
  "session_id": "a3d8f5d3-7b43-4d83-8ac4-4a3d2b91a201",
  "user_profile_override": {
    "selected_ai_persona": "warm",
    "goal": "fat_loss",
    "activity_level": "moderate"
  }
}
```

### 필드 설명

- `user_id`: 필수
- `user_message`: 필수
- `session_id`: 선택
- `user_profile_override`: 선택, 개발/디버그용

### Response JSON

```json
{
  "status": "success",
  "session_id": "a3d8f5d3-7b43-4d83-8ac4-4a3d2b91a201",
  "response": "이번 주는 주 4회 기준으로 상체/하체 분할로 가면 좋겠습니다. 이 방향으로 계획 제안할까요?",
  "intent": "계획",
  "emotion": {
    "label": "중립",
    "intensity": 0.2
  },
  "draft_response": "이번 주는 주 4회 분할이 적절하다.",
  "debug_state": {
    "search_results_count": 3,
    "search_quality": "ok",
    "draft_components": {
      "core_message": "이번 주는 주 4회 분할이 적절하다.",
      "reason_points": [
        "회복일을 포함하면 지속 가능성이 높다.",
        "분할 훈련으로 부위별 볼륨을 배분하기 쉽다."
      ],
      "suggested_action": "상체/하체 기준의 주 4회 루틴을 제안한다.",
      "safety_notes": [],
      "approval_question": "이 방향으로 계획 제안할까요?",
      "search_grounding_summary": "검색 결과 중 핵심 근거만 요약했다."
    },
    "proposed_plan_count": 4,
    "selected_ai_persona": "warm",
    "resolved_persona_id": "warm",
    "profile_sync_version": 2,
    "intimacy_level": 1
  }
}
```

## 2.2 헬스체크

- Method: `GET`
- Path: `/health`
- 설명:
  - 서버 상태 확인용 API입니다.

### Response JSON

```json
{
  "status": "ok",
  "env": "development",
  "version": "v2"
}
```

## 2.3 프로필 변경 이벤트

- Method: `POST`
- Path: `/internal/events/profile-updated`
- 설명:
  - WAS에서 프로필 변경 후 FastAPI에 다음 턴 refresh를 요청하는 내부 이벤트입니다.

### Request JSON

```json
{
  "user_id": "user-123",
  "changed_fields": [
    "selected_ai_persona",
    "goal"
  ],
  "profile_version": 7
}
```

### Response JSON

```json
{
  "status": "success",
  "user_id": "user-123",
  "tracked_version": 7
}
```

## 2.4 디버그 UI

- Method: `GET`
- Path: `/debug`
- 설명:
  - 이 엔드포인트는 JSON이 아니라 HTML 페이지를 반환합니다.
  - 따라서 본 DataFormat 문서에서는 별도 JSON 스펙을 정의하지 않습니다.

## 3. FastAPI -> WAS API

## 3.1 사용자 프로필 조회

- Method: `GET`
- Path: `/api/user/profile/{user_id}`
- 설명:
  - 세션 첫 턴 로딩
  - 프로필 변경 이벤트 후 다음 턴 refresh

### Response JSON

raw 형식:

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
  "selected_ai_persona": "warm",
  "mbti": "INTJ"
}
```

`data` 래퍼 형식:

```json
{
  "status": "success",
  "data": {
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
    "selected_ai_persona": "warm",
    "mbti": "INTJ"
  }
}
```

### 필수 권장 필드

- `user_id`
- `selected_ai_persona`
- `goal`
- `activity_level`

### 있으면 좋은 필드

- `weight`
- `height`
- `age`
- `gender`
- `diet_type`
- `allergies`
- `injury_history`
- `mbti`

## 3.2 오늘 플랜 조회

- Method: `GET`
- Path: `/api/plan/today/{user_id}`
- 설명:
  - 현재 턴에서 체크 가능한 오늘 플랜 목록을 내려줍니다.

### Response JSON

raw 형식:

```json
[
  {
    "id": "plan-item-1",
    "name": "하체 운동",
    "detail": "스쿼트 4세트",
    "day": "monday",
    "completed": false
  },
  {
    "id": "plan-item-2",
    "name": "유산소",
    "detail": "트레드밀 20분",
    "day": "monday",
    "completed": true
  }
]
```

`data` 래퍼 형식:

```json
{
  "status": "success",
  "data": [
    {
      "id": "plan-item-1",
      "name": "하체 운동",
      "detail": "스쿼트 4세트",
      "day": "monday",
      "completed": false
    }
  ]
}
```

### 필수 권장 필드

- `id`
- `name`
- `completed`

### 있으면 좋은 필드

- `detail`
- `day`

### 주의

- 현재 런타임 기준으로 `today_plan`은 배열이어야 합니다.
- `id`가 없으면 `plan_check` 처리에 문제가 생길 수 있습니다.

## 3.3 운동 전체 플랜 조회

- Method: `GET`
- Path: `/api/workout-plan/full/{user_id}`
- 설명:
  - `수정` intent에서 기존 운동 전체 플랜을 읽습니다.

### Response JSON

```json
{
  "plan_type": "workout",
  "items": [
    {
      "id": "workout-1",
      "name": "벤치프레스",
      "detail": "4세트 x 8회",
      "day": "monday",
      "completed": false
    },
    {
      "id": "workout-2",
      "name": "스쿼트",
      "detail": "4세트 x 10회",
      "day": "wednesday",
      "completed": false
    }
  ]
}
```

### 주의

- 이 응답은 LLM에 수정 컨텍스트로 전달됩니다.
- `items` 배열 중심 구조로 유지하는 것이 가장 안전합니다.

## 3.4 식단 전체 플랜 조회

- Method: `GET`
- Path: `/api/diet-plan/full/{user_id}`
- 설명:
  - `수정` intent에서 기존 식단 전체 플랜을 읽습니다.

### Response JSON

```json
{
  "plan_type": "diet",
  "items": [
    {
      "id": "diet-1",
      "name": "닭가슴살 샐러드",
      "detail": "점심 / 450kcal",
      "day": "monday",
      "completed": false
    },
    {
      "id": "diet-2",
      "name": "오트밀 + 바나나",
      "detail": "아침 / 320kcal",
      "day": "tuesday",
      "completed": false
    }
  ]
}
```

## 3.5 사용자 프로필 수정

- Method: `PUT`
- Path: `/api/user/profile/{user_id}`
- 설명:
  - 기록/프로필 수정 intent에서 partial update를 보냅니다.

### Request JSON

```json
{
  "weight": 71.8,
  "goal": "muscle_gain",
  "selected_ai_persona": "spartan",
  "mbti": "ENTJ"
}
```

### 필드 규칙

- partial update만 전송됩니다.
- 변경된 필드만 포함하면 됩니다.

### 백엔드가 허용하면 좋은 필드

- `weight`
- `height`
- `age`
- `gender`
- `diet_type`
- `allergies`
- `injury_history`
- `goal`
- `activity_level`
- `selected_ai_persona`
- `mbti`

### 주의

- 코드상 `mbti`도 변경 필드로 들어올 수 있으므로, 백엔드는 `mbti`를 허용하거나 무시 가능하게 구현하는 것이 안전합니다.

### Success Response JSON

```json
{
  "status": "success"
}
```

## 3.6 오늘 플랜 체크 완료

- Method: `PUT`
- Path: `/api/plan/check/{user_id}`
- 설명:
  - 오늘 플랜 항목 완료 체크를 반영합니다.

### Request JSON

```json
{
  "item_id": "plan-item-1"
}
```

### Success Response JSON

```json
{
  "status": "success"
}
```

## 3.7 새 플랜 생성

- Method: `POST`
- Path: `/api/plan/create/{user_id}`
- 설명:
  - 사용자가 승인한 새 운동/식단 계획을 저장합니다.

### Request JSON

현재 실제 런타임 payload:

```json
{
  "has_plan": true,
  "plan_type": "workout",
  "items": [
    {
      "name": "상체 운동",
      "detail": "벤치프레스 4세트",
      "day": "monday"
    },
    {
      "name": "하체 운동",
      "detail": "스쿼트 4세트",
      "day": "wednesday"
    }
  ]
}
```

### 필드 설명

- `has_plan`: 현재 코드상 포함될 수 있음. 백엔드는 허용 또는 무시 가능하게 처리 권장
- `plan_type`: `workout` 또는 `diet`
- `items`: 실제 저장할 계획 항목 배열

### 각 item 필드

- `name`: 필수
- `detail`: 선택
- `day`: 선택

### Success Response JSON

```json
{
  "status": "success"
}
```

## 3.8 기존 플랜 수정

- Method: `PUT`
- Path: `/api/plan/update/{user_id}`
- 설명:
  - 사용자가 승인한 수정안을 기존 플랜에 반영합니다.

### Request JSON

현재 실제 런타임 payload:

```json
{
  "has_plan": true,
  "plan_type": "diet",
  "items": [
    {
      "name": "닭가슴살 샐러드",
      "detail": "점심 / 450kcal",
      "day": "monday"
    },
    {
      "name": "두부 샐러드",
      "detail": "저녁 / 380kcal",
      "day": "monday"
    }
  ]
}
```

### 주의

- `POST /api/plan/create/{user_id}` 와 거의 동일한 body 형식을 씁니다.
- 구분은 HTTP Method와 path로 합니다.

### Success Response JSON

```json
{
  "status": "success"
}
```

## 4. 실제 런타임 기준 중요 메모

### 4.1 source of truth

- persona 선택값의 source of truth는 WAS 프로필의 `selected_ai_persona` 입니다.

### 4.2 오늘 플랜 응답 형식

- `GET /api/plan/today/{user_id}` 는 반드시 배열 형식으로 내려주는 것이 안전합니다.

### 4.3 플랜 생성/수정의 `has_plan`

- 현재 FastAPI 실제 코드에서는 `plan create/update` 요청 body에 `has_plan: true`가 포함될 수 있습니다.
- 백엔드는 이 필드를 허용하거나 무시할 수 있게 구현하는 것이 좋습니다.

### 4.4 추가 필드 허용

- 읽기 응답(`GET profile`, `GET full plan`)은 extra field가 있어도 비교적 안전합니다.
- 단, 필수 핵심 필드는 빠지지 않게 유지하는 것이 좋습니다.

## 5. 관련 기준 파일

- `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\clients\was.py`
- `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\schemas\was.py`
- `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\schemas\chat.py`
- `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\schemas\profile_events.py`
- `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\docs\was_api_contract.md`
- `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\docs\api_specification.md`
