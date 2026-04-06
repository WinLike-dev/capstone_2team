# Profile Sync Flow

이 문서는 WAS 프로필 변경이 FastAPI / LangGraph 세션에 반영되는 방식을 설명합니다.

## 목표

- 프로필의 source of truth는 WAS가 가진다.
- FastAPI는 프로필을 캐시하지만, WAS 변경 이벤트를 받으면 다음 사용자 턴에서 최신 프로필을 다시 읽는다.
- 현재 응답 생성 중인 턴을 중간에 뒤집지 않는다.

## 현재 방식

1. WAS에서 사용자 프로필이 수정된다.
2. WAS는 FastAPI 내부 엔드포인트 `POST /internal/events/profile-updated` 로 이벤트를 보낸다.
3. FastAPI는 `ProfileSyncTracker`에 `user_id -> profile_sync_version` 을 기록한다.
4. 사용자가 다음 `/chat` 요청을 보낸다.
5. `preprocess` 노드는 현재 세션이 가진 `profile_sync_version` 과 tracker의 최신 버전을 비교한다.
6. tracker 버전이 더 크면, WAS에서 `get_user_profile()` 을 다시 호출해 state를 갱신한다.
7. 그 턴부터 최신 `selected_ai_persona` 와 기타 프로필 필드가 적용된다.

## 왜 next-turn refresh 인가

- 현재 생성 중인 응답을 중간에 바꾸지 않아도 된다.
- 활성 세션 전체를 즉시 mutate 하지 않아도 된다.
- 여러 세션이 동시에 열려 있어도 각 세션이 자기 턴에 안전하게 최신값으로 따라온다.
- FastAPI 인스턴스 내부 구현이 단순하다.

## 핵심 코드 위치

- 이벤트 수신: `app/routers/profile_events.py`
- 버전 추적: `app/core/profile_sync.py`
- 세션 refresh 판단: `app/graph/nodes/preprocess.py`
- 초기 state와 debug 노출: `app/routers/chat.py`

## 이벤트 예시

```json
{
  "user_id": "user-123",
  "changed_fields": ["selected_ai_persona"],
  "profile_version": 7
}
```

`profile_version` 은 선택값입니다.
- WAS가 monotonic version을 제공하면 그대로 전달합니다.
- 제공하지 않으면 FastAPI가 내부 카운터를 1씩 증가시킵니다.

## 주의사항

- 현재 구조는 in-memory tracker를 사용합니다.
- 즉, 프로세스 재시작 시 tracker 버전은 초기화됩니다.
- 하지만 source of truth는 WAS이므로, 다음 refresh 때 다시 정상 상태로 복구됩니다.
