# WAS 연동 / API 통신 문서

이 문서는 `ai-model/v2` 와 WAS 사이의 실제 통신 계약을 정리한 문서입니다.
현재 기준 source of truth는 WAS이고, FastAPI 모델 서버는 프로필/플랜을 읽고 반영하거나, 승인된 변경을 WAS에 다시 기록합니다.

## 1. 통신 방향 요약

### WAS -> FastAPI
- 프로필 변경 이벤트 전달
- 목적: 다음 채팅 턴에서 최신 프로필을 다시 읽게 만들기

### FastAPI -> WAS
- 사용자 프로필 조회
- 오늘 플랜 조회
- 프로필 수정 반영
- 플랜 생성
- 플랜 수정
- 플랜 체크 완료 반영

## 2. 호출 흐름

### 세션 첫 턴
1. 클라이언트가 `POST /chat` 호출
2. FastAPI `preprocess` 노드가 WAS에서 아래를 읽음
   - `GET /api/user/profile/{user_id}`
   - `GET /api/plan/today/{user_id}`
3. 읽어온 프로필과 오늘 플랜을 state에 적재
4. 이후 LangGraph가 intent -> search -> generate -> persona 흐름 실행

### 프로필 변경 후 다음 턴
1. WAS에서 프로필 DB 수정 완료
2. WAS가 FastAPI 내부 엔드포인트 `POST /internal/events/profile-updated` 호출
3. FastAPI는 해당 `user_id`의 `profile_sync_version`을 증가 또는 갱신
4. 사용자가 다음 `/chat` 요청을 보냄
5. `preprocess` 노드가 세션이 가진 `profile_sync_version`과 최신 tracker 버전을 비교
6. 최신 버전이 더 크면 `GET /api/user/profile/{user_id}`를 다시 호출
7. 새 프로필이 해당 턴부터 적용됨

### 계획 승인 턴
1. 사용자 메시지가 `계획_승인`으로 분류됨
2. Draft/Persona는 승인 문구만 생성
3. 응답 반환 후 BackgroundTasks에서 WAS 쓰기 실행
4. 승인된 `proposed_plan`을 아래 중 하나로 반영
   - `POST /api/plan/create/{user_id}`
   - `PUT /api/plan/update/{user_id}`

## 3. FastAPI가 호출하는 WAS API

### 3.1 프로필 조회
`GET /api/user/profile/{user_id}`

용도:
- 세션 첫 턴 로딩
- profile-updated 이벤트 이후 다음 턴 refresh

현재 모델 서버가 기대하는 필드:
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

비고:
- `selected_ai_persona`는 현재 persona 선택의 공식 source 값입니다.
- 추가 필드는 허용됩니다. FastAPI는 정의되지 않은 extra field를 무시합니다.

### 3.2 오늘 플랜 조회
`GET /api/plan/today/{user_id}`

용도:
- 세션 첫 턴에서 오늘 체크 대상과 컨텍스트 확보

예시:
```json
[
  {
    "id": "plan-item-1",
    "name": "하체 운동",
    "detail": "스쿼트 4세트",
    "day": "monday",
    "completed": false
  }
]
```

### 3.3 프로필 수정
`PUT /api/user/profile/{user_id}`

용도:
- 기록/프로필 수정 intent에서 확정된 변경 반영

요청 body:
```json
{
  "weight": 71.8,
  "goal": "muscle_gain",
  "selected_ai_persona": "spartan"
}
```

규칙:
- partial update만 보냅니다
- 정의된 필드만 허용합니다

### 3.4 플랜 생성
`POST /api/plan/create/{user_id}`

용도:
- 승인된 새 계획 저장

요청 body:
```json
{
  "plan_type": "workout",
  "items": [
    {
      "name": "상체 운동",
      "detail": "벤치프레스 4세트",
      "day": "monday"
    }
  ]
}
```

### 3.5 플랜 수정
`PUT /api/plan/update/{user_id}`

용도:
- 승인된 수정안 저장

요청 body 형식은 create와 동일합니다.

### 3.6 플랜 체크 완료
`PUT /api/plan/check/{user_id}`

용도:
- 오늘 플랜 항목 완료 처리

요청 body:
```json
{
  "item_id": "plan-item-1"
}
```

## 4. WAS가 호출하는 FastAPI 내부 이벤트 API

### 4.1 프로필 변경 이벤트
`POST /internal/events/profile-updated`

용도:
- WAS에서 프로필 변경이 일어났음을 FastAPI에 즉시 알림
- FastAPI는 현재 턴을 끊지 않고, 다음 사용자 턴에서 최신 프로필을 refresh

요청 body:
```json
{
  "user_id": "user-123",
  "changed_fields": ["selected_ai_persona"],
  "profile_version": 7
}
```

필드 설명:
- `user_id`: 변경된 사용자
- `changed_fields`: 변경된 필드 목록
- `profile_version`: 선택값. WAS가 monotonic version을 관리하면 전달

응답 body:
```json
{
  "status": "success",
  "user_id": "user-123",
  "tracked_version": 7
}
```

## 5. next-turn refresh 정책

현재 구조는 **push event + next-turn refresh** 입니다.

의미:
- WAS는 변경 사실을 즉시 FastAPI에 알려줍니다
- FastAPI는 현재 생성 중인 응답을 중간에 바꾸지 않습니다
- 사용자의 다음 `/chat` 요청이 들어올 때 최신 프로필을 다시 읽습니다

이 정책을 쓰는 이유:
- 현재 응답 생성 중인 state를 강제로 mutate하지 않아도 됨
- 구현이 단순함
- 캡스톤 규모에서 충분히 안정적임

## 6. FastAPI 내부 반영 위치

- WAS 클라이언트: `app/clients/was.py`
- 이벤트 수신: `app/routers/profile_events.py`
- 버전 추적: `app/core/profile_sync.py`
- 다음 턴 refresh 판단: `app/graph/nodes/preprocess.py`
- 초기 state 및 debug 노출: `app/routers/chat.py`

## 7. 주의사항

- 현재 `ProfileSyncTracker`는 메모리 기반입니다
- 따라서 단일 프로세스/단일 인스턴스 환경에 가장 잘 맞습니다
- 캡스톤 수준에서는 충분하지만, 멀티 인스턴스로 확장하면 Redis 같은 공유 저장소가 필요합니다
