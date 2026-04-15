# v2 Context / State Refactor Notes

이 문서는 `develop/ai-model/v2`에서 진행한 `context 이해`, `state 오염 완화`, `intent 계약 정리`, `proposal 메모리`, `plan 응답 가시화` 논의를 정리한 작업 메모다.

기준 시점:
- 2026-04-16

관련 문서:
- [v2_model_analysis.md](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/v2_model_analysis.md)
- [api_specification.md](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/docs/api_specification.md)

## 1. 배경 문제

기존 v2 구조의 핵심 문제는 `state 개수` 자체보다 아래 4가지였다.

- 수명이 다른 값이 하나의 flat state에 섞여 있었다.
- checkpoint 복구 시 이전 turn의 임시 값이 거의 통째로 살아났다.
- `messages`, `last_assistant_message`, `proposed_plan*`, `awaiting_plan_confirmation` 같은 값이 중복되거나 오래 남아 stale context를 만들었다.
- intent 라우팅은 비교적 맞더라도, `"그거"`, `"아까 말한 거"`, `"방금 준 계획"` 같은 후속 발화의 맥락 복원이 약했다.

실제 증상은 아래와 같았다.

- 생성 이후 unrelated 대화가 와도 예전 plan confirmation 문맥이 남아 있었다.
- 수정/생성/정보/공감_케어가 섞인 follow-up에서 현재 요청보다 이전 턴이 더 강하게 작동했다.
- proposal은 state에 있지만 최종 사용자 응답에는 plan 자체가 잘 드러나지 않았다.

## 2. 우선순위 합의

이번 리팩터링의 우선순위는 아래 순서로 정했다.

1. 평가 점수
2. 속도
3. 구조 단순화

추가 제약:

- `생성`, `수정`, `정보`, `기록`, `승인`, `안전`, `공감_케어`의 경계는 최대한 유지한다.
- `persona` 기능은 반드시 유지한다.
- 큰 리팩터링은 허용하지만 기존 동작을 한 번에 깨는 전면 교체는 피한다.

## 3. 설계 합의

### 3.1 Intent 계약

메인 intent는 아래 7개로 정리했다.

```text
create | modify | info | record | approval | casual | safety
```

도메인은 아래 4개 축으로 정리했다.

```text
workout | diet | profile | general
```

정서 지원 성격은 main intent와 분리했다.

```text
support_mode = care | normal
```

핵심 원칙:

- `care`는 main intent가 아니라 overlay 성격으로 본다.
- `"무릎이 아파서 오늘 운동 좀 약하게 바꿔줘"`는 `modify + workout + care`처럼 처리한다.

### 3.2 Context Resolver

Intent Router 앞에 `Context Resolver`를 둔다.

역할:

- `"그거"`, `"아까 말한 거"`, `"방금 준 계획"` 같은 생략 표현을 복원한다.
- intent를 직접 최종 결정하지 않는다.

출력 계약:

```json
{
  "resolved_reference": "none | active_proposal | today_plan | previous_answer | recent_chat | user_memory",
  "resolved_domain": "none | workout | diet | profile | general",
  "resolved_text": "생략 표현을 풀어쓴 문장",
  "confidence": 0.0,
  "ambiguous": false
}
```

### 3.3 Clarify

확신이 낮거나 참조 대상이 불명확하면 억지로 처리하지 않고 확인 질문으로 보낸다.

예:

- `"그거 바꿔줘"`인데 proposal도 없고 대상도 불명확한 경우
- `"그대로 해"`인데 승인 대상이 없는 경우

### 3.4 State 계층

State는 아래 5분류 기준으로 보기로 했다.

- `meta`
  실행/식별/동기화용 값
- `persistent`
  세션 동안 계속 유효한 사실
- `bounded persistent`
  짧게만 유지해야 하는 cross-turn anchor
- `turn`
  현재 턴의 해석 결과
- `scratch`
  생성/검색/수정 중간산물

판정 원리:

- 언제까지 필요하냐
- 그 시점을 넘기면 오염되냐

### 3.5 Active Proposal

`active_proposal`은 proposal history가 아니라 다음 1~2턴용 참조 anchor로 본다.

최소 스키마:

```json
{
  "domain": "workout | diet",
  "write_mode": "create | update",
  "items": [],
  "summary": "",
  "last_used_turn": 0
}
```

규칙:

- referenced면 keep
- new proposal generated면 replace
- approved/cancelled면 clear
- unrelated 2턴이면 clear

### 3.6 Recent Dialogue

`recent_dialogue`는 최근 4턴만 유지하는 압축형 대화 메모리다.

스키마:

```json
{
  "recent_turns": [
    {
      "turn_id": 12,
      "user_text": "",
      "assistant_text": "",
      "user_summary": "",
      "assistant_summary": "",
      "action_intent": "create | modify | info | record | approval | casual | safety",
      "domain": "workout | diet | profile | general",
      "support_mode": "care | normal",
      "referenced_object": "none | active_proposal | today_plan | previous_answer | recent_chat",
      "state_effect": "none | proposal_created | proposal_updated | proposal_approved | profile_recorded | plan_checked | clarification_requested"
    }
  ]
}
```

운영 규칙:

- turn 종료 시 1회만 append
- 최근 4턴만 유지
- `active_proposal`과는 별도 관리

### 3.7 RAG 정책 합의

RAG는 한 갈래가 아니라 역할별로 나눈다.

- `policy KB`
  운동/식단/가이드라인/행동방침
- `user memory`
  장기 기억/사용자 경험
- `web`
  최신성 필요한 정보

합의한 사용 원칙:

- `create/modify`는 policy KB 우선
- `info/latest`는 policy + 필요시 web
- 최근 맥락으로 의도/참조 대상이 안 풀릴 때만 user memory 사용
- 알레르기, 부상, 질환, 약물 등은 hard constraint로 본다

## 4. 실제 적용된 변경

### 4.1 새 상태 구조 추가

적용 파일:

- [app/schemas/state.py](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/app/schemas/state.py)

추가된 필드:

- `action_intent`
- `domain`
- `support_mode`
- `ambiguous`
- `context_resolution`
- `active_proposal`
- `recent_dialogue`
- `DraftComponents.plan_preview`

주의:

- 기존 `intent`, `proposed_plan*`, `awaiting_plan_confirmation`는 호환을 위해 당분간 유지한다.

### 4.2 bounded state helper 추가

적용 파일:

- [app/core/conversation_state.py](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/app/core/conversation_state.py)

역할:

- `empty_context_resolution`
- `empty_recent_dialogue`
- `infer_domain`
- `build_active_proposal`
- `sync_proposal_fields`
- `evolve_active_proposal`
- `build_recent_turn`
- `append_recent_turn`

### 4.3 Context Resolver 노드 추가

적용 파일:

- [app/graph/nodes/context_resolver.py](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/app/graph/nodes/context_resolver.py)
- [app/graph/builder.py](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/app/graph/builder.py)

변경:

- 그래프 흐름을 `preprocess -> context_resolver -> analyze_intent`로 조정
- `active_proposal`, `recent_dialogue`, referential marker를 기반으로 `resolved_text` 생성

### 4.4 Intent 노드 재정리

적용 파일:

- [app/graph/nodes/intent.py](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/app/graph/nodes/intent.py)

변경:

- `routing_message = resolved_text or user_message` 방식 추가
- legacy intent를 유지하면서도 `action_intent/domain/support_mode/ambiguous`를 같이 기록
- `recent_dialogue`, `context_resolution`, `active_proposal`을 context로 사용
- `home_recommendation`도 새 계약으로 매핑

### 4.5 turn/scratch 초기화 강화

적용 파일:

- [app/graph/nodes/preprocess.py](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/app/graph/nodes/preprocess.py)

변경:

- turn 시작 시 `action_intent/domain/support_mode/context_resolution` 초기화
- `search_*`, `draft_*`, `response`, `self_eval_*`, `modify_plan_context` 초기화

### 4.6 modify 경로에서 active_proposal 참조

적용 파일:

- [app/graph/nodes/modify.py](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/app/graph/nodes/modify.py)

변경:

- explicit target, proposed_plan_type 외에 `active_proposal.domain`도 수정 대상 후보로 사용

### 4.7 chat router에서 bounded state persist

적용 파일:

- [app/routers/chat.py](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/app/routers/chat.py)

변경:

- initial/resumed state에 새 필드 추가
- 예전 checkpoint 복구 시 `active_proposal`을 legacy `proposed_plan*`에서 hydrate
- 응답 직후 `recent_dialogue` append
- `active_proposal` keep/replace/clear 적용
- 승인 write 성공 시 `active_proposal`도 같이 clear

### 4.8 home router에도 새 state 추가

적용 파일:

- [app/routers/home.py](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/app/routers/home.py)

변경:

- home recommendation state에도 새 turn/bounded 필드 추가

### 4.9 plan preview 노출

적용 파일:

- [app/core/draft_contract.py](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/app/core/draft_contract.py)
- [app/graph/nodes/generate.py](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/app/graph/nodes/generate.py)
- [app/graph/nodes/persona.py](/C:/Users/ksh00/anti_projects/capstone_2team/develop/ai-model/v2/app/graph/nodes/persona.py)

변경:

- `proposed_plan`에서 사람이 읽을 `plan_preview`를 생성
- draft preview에 `계획:` 블록 추가
- persona가 `plan_preview`를 받아 최종 응답에서도 plan 구조를 유지하도록 가드레일 추가

효과:

- 사용자가 제안된 운동 플랜/식단 플랜을 응답 텍스트에서 직접 볼 수 있게 됨

## 5. 현재 상태에서 아직 남은 보완점

### 5.1 높은 우선순위

- `search`가 아직 `resolved_text`를 직접 쓰지 않는다.
- `generate`가 아직 `recent_dialogue` 대신 legacy `messages` 중심으로 대화 문맥을 읽는다.
- policy KB retrieval이 metadata-gated retrieval로 아직 바뀌지 않았다.
- `support_mode=care`가 fully independent classifier로 아직 분리되지 않았다.

### 5.2 구조적으로 아직 덜 끝난 부분

- `turn/scratch`가 checkpoint에 완전히 제외되지는 않았다.
- `messages`와 `recent_dialogue`가 동시에 존재하는 과도기 상태다.
- `intent`는 아직 legacy string과 새 계약이 병행된다.

## 6. 다음 작업 권장 순서

1. `search/generate`가 `resolved_text`와 `recent_dialogue`를 우선 사용하도록 변경
2. `policy KB`를 `category/use_case/population/evidence_type` 필터 기반 retrieval로 변경
3. `support_mode=care`를 main intent와 독립적으로 분류
4. checkpoint 저장 대상을 `meta + persistent + bounded persistent` 위주로 정리
5. 회귀 테스트 세트 작성

추천 회귀 테스트:

- 생성 -> 수정 -> 승인
- 생성 -> unrelated care
- 정보 질문 -> 후속 referential question
- 프로필 기록 -> 생성
- `"그거"`, `"아까"`, `"방금 준 거"` follow-up

## 7. 검증 메모

현재까지 확인한 내용:

- `python -m compileall develop/ai-model/v2/app` 통과
- `active_proposal` 생성/유지/만료 smoke check 통과
- 예전 checkpoint 복구 시 `active_proposal` hydrate smoke check 통과
- `plan_preview`가 draft preview에 포함되는 smoke check 통과

주의:

- 실제 `/chat` end-to-end 회귀 테스트는 아직 별도로 정리되지 않았다.
- 따라서 다음 단계에서 intent confusion 케이스와 proposal follow-up 케이스를 꼭 고정 테스트로 만들어야 한다.
