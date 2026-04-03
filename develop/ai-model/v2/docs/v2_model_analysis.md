# v2 AI 모델 아키텍처 분석

## 한줄 요약

**헬스 AI 챗봇 백엔드** — LangGraph StateGraph 기반으로 `의도 분석 → 검색 → 응답 생성` 파이프라인을 구현하며, WAS(RDB)와 Pinecone(VDB)를 통해 사용자 데이터와 지식을 관리하는 시스템.

---

## 1. 기술 스택

| 계층 | 기술 | 역할 |
|------|------|------|
| API 서버 | **FastAPI** | REST 엔드포인트 (`POST /chat`, `GET /health`) |
| 파이프라인 | **LangGraph** (StateGraph) | 멀티 노드 조건부 라우팅 그래프 |
| 세션 관리 | **MemorySaver** (인메모리 체크포인터) | thread_id 기반 대화 State 영속 |
| LLM (응답) | **Gemini 2.5 Flash** | 응답 생성 + 자기 평가 |
| LLM (라우팅) | **Gemini 2.5 Flash-Lite** | 의도 분석 + 검색 결과 평가 |
| 임베딩 | **gemini-embedding-001** | VDB 검색용 벡터 생성 |
| 벡터 DB | **Pinecone** (3 namespace) | 에피소드·팩트·외부지식 저장 |
| RDB 접근 | **WAS API** (httpx 비동기) | 프로필·플랜 CRUD |
| 설정 | **pydantic-settings** | 환경변수 관리 |

---

## 2. 메인 파이프라인 플로우 (Layer 1)

```
START → preprocess → analyze_intent
  ├─ casual          → generate → END
  ├─ 안전경고         → safety → END
  ├─ fallback        → fallback → (재추론: analyze_intent | clarification: END)
  ├─ 공감_케어        → care → (requires_past_memory? → search | generate) → END
  ├─ 기록            → record → generate → END
  ├─ 계획 / 정보      → search → generate → END
  └─ 수정            → modify_load → search → generate → END
```

> [!IMPORTANT]
> - `generate` 노드 내부에 **자기 평가 루프** (max=2) 존재 — 톤·할루시네이션 체크 후 재생성
> - `search` 노드 내부에 **재시도 루프** (max=3) 존재 — 스코어 기반 쿼리 재생성 or 재검색

---

## 3. 의도 분류 체계 (Layer 2)

### 3.1. 2단계 분류 구조

| 단계 | 방식 | 설명 |
|------|------|------|
| **1단계** | 규칙 기반 사전 필터 | 금칙어 매칭 → `안전경고`, 인사 패턴 → `casual` (단, previous_intent가 공감_케어면 스킵) |
| **2단계** | Flash-Lite LLM 정밀 분석 | 현재 메시지 + previous_intent + previous_emotion + rule_hints 입력 |

### 3.2. 의도 목록 및 라우팅

| 의도 | 다음 노드 | 핵심 동작 |
|------|-----------|-----------|
| `casual` | generate | 인사·잡담 바로 응답 |
| `공감_케어` | care → (search \| generate) | 감정 표현 시 과거 기억 검색 여부 판단 |
| `기록` | record → generate | 운동 완료 체크 / 프로필 변경 |
| `계획` | search → generate | 운동·식단 계획 생성 |
| `수정` | modify_load → search → generate | 기존 플랜 WAS 조회 후 수정 |
| `정보` | search → generate | 운동·영양 정보 질의 |
| `안전경고` | safety → END | 자해·극단 행동 즉시 차단 |
| `fallback` | fallback → (재추론 \| END) | 맥락 있으면 재추론, 없으면 Clarification |

### 3.3. 의도 분석 출력 속성

- **공통**: `intent`, `confidence` (0~1), `emotion` (label+intensity)
- **판단 기반**: `has_fact_change`, `requires_past_memory`
- **조건부**: `record_type` (기록), `profile_changes` (기록), `modify_target` (수정), `search_targets` (계획·정보·수정)

---

## 4. 노드별 상세 동작 (Layer 3)

### 4.1. 전처리 (`preprocess.py`)
1. **턴별 State 초기화** — search_results, profile_changes 등 null로 리셋
2. **pending_writes 재시도** — 이전 턴 WAS 쓰기 실패 건 재시도
3. **세션 첫 턴** → WAS API 동기 호출 (프로필 + 오늘 플랜) → State 캐싱
4. **대화 요약** — `SUMMARY_TURN_INTERVAL` 배수 턴마다 오래된 메시지 압축 → vdb_user_important 저장

### 4.2. 검색 파이프라인 (`search.py`)
1. `search_targets` 기반 VDB 선택
2. **병렬 검색** — vdb_memory, vdb_user_important, vdb_external, Web
3. 결과 **병합** — 중복 제거 + 우선순위 정렬 + 출처 태깅
4. Flash-Lite **평가** — score 산출
   - `> 0.7` → 그대로 사용
   - `0.4~0.7` → 재검색
   - `< 0.4` → 쿼리 재생성 후 재시도
5. **Graceful Degradation** — 재시도 초과 시 공감_케어는 즉각 위로, 나머지는 부분 결과로 degraded 응답

### 4.3. 응답 생성 (`generate.py`)
- **입력 참조**: emotion(톤 조절), profile_changes, today_plan, modify_plan_context, search_quality, 출처 태그
- **자기 평가 루프** (max=2): 톤·할루시네이션·제약사항 체크, 실패 시 failure_reason과 함께 재생성
- 초과 시 **부분 패치**로 종료

### 4.4. 기록 (`record.py`)
- **profile 변경**: RDB 스키마 검증 → 통과 시 State.profile_changes 기록, 캐시 갱신
- **plan_check**: is_today 검증 → today_plan 리스트 항목 검증 → 통과 시 완료 체크

### 4.5. 수정 (`modify.py`)
- `modify_target` (workout/diet) 기반으로 WAS에서 전체 플랜 동기 조회
- 결과를 실행 컨텍스트(`modify_plan_context`)에 보관 → search + generate에 전달

### 4.6. 비동기 WAS 쓰기 (`was_write.py`)
- 응답 반환 후 FastAPI `BackgroundTasks`로 실행
- 대상: profile 변경, plan_check 완료, plan_create, plan_update
- 실패 시 `pending_writes`에 기록 → 다음 턴 전처리에서 재시도
- 성공 시 `today_plan` 캐시 갱신 (오늘 포함 조건 체크)

### 4.7. 피드백 루프 (`feedback.py`)
- 반응 분석 (친밀도·페르소나 진화)
- `should_save_episode = true`이면 vdb_memory에 에피소드 저장 (날짜·감정·핵심 사건 요약)
- 감정 이력 누적

---

## 5. 데이터 흐름 (Layer 4)

### 5.1. 외부 시스템

```
┌──────────────────┐     ┌──────────────────────────┐
│    WAS (API)     │     │  Pinecone VDB (직접접근)  │
│  ┌─────────────┐ │     │  ┌────────────────────┐  │
│  │ 읽기 API    │ │     │  │ vdb_memory         │  │
│  │ 쓰기 API    │ │     │  │ vdb_user_important │  │
│  └──────┬──────┘ │     │  │ vdb_external       │  │
│         │        │     │  └────────────────────┘  │
│    ┌────▼────┐   │     │  ┌────────────────────┐  │
│    │   RDB   │   │     │  │ Checkpointer DB    │  │
│    └─────────┘   │     │  │ (MemorySaver)      │  │
└──────────────────┘     │  └────────────────────┘  │
                         └──────────────────────────┘
```

### 5.2. VDB 네임스페이스 설계

| VDB | 네임스페이스 패턴 | 용도 | 접근 시점 |
|-----|:--:|------|------|
| `vdb_memory` | `{user_id}-memory` | 에피소드·추억 (per user) | 공감_케어 검색 / 피드백 저장 |
| `vdb_user_important` | `{user_id}-important` | 핵심 팩트 요약 (per user) | 계획 검색 / 요약 저장 |
| `vdb_external` | `external` | 외부 운동·영양 지식 (공유) | 정보·계획·수정 검색 |

### 5.3. 의도별 검색 대상 매핑

| 의도 | 검색 대상 |
|------|-----------|
| 공감_케어 | vdb_memory 우선 |
| 계획 | vdb_external + vdb_user_important |
| 수정 | 전체 플랜(WAS 조회) + vdb_external |
| 정보 | vdb_external 우선 |

### 5.4. State 캐시 갱신 트리거

- `user_profile` ← 기록(profile) 처리 후
- `today_plan` ← plan_check 완료 / 새 플랜 저장(오늘 포함) / 수정(오늘 포함)
- `pending_writes` ← WAS 쓰기 실패 추가 / 재시도 성공 삭제

---

## 6. 의존성 주입 구조

모든 노드는 `NodeDeps` 데이터클래스를 통해 클라이언트를 주입받음:

```python
@dataclass
class NodeDeps:
    gemini: GeminiClient      # Flash — 응답 생성
    router: GeminiClient      # Flash-Lite — 의도 분석 · 검색 평가
    was: WASClient            # RDB CRUD
    pinecone: PineconeClient  # VDB 검색/저장
    embed: EmbeddingClient    # 벡터 임베딩
```

각 노드는 `make_xxx_node(deps)` 팩토리 패턴으로 생성 → 테스트 시 mock 교체 용이.

---

## 7. API 엔드포인트

### `POST /chat`
```json
// Request
{
  "user_id": "user123",
  "user_message": "오늘 운동 다 했어!",
  "session_id": "optional-uuid"   // 생략 시 자동 생성
}

// Response
{
  "session_id": "...",
  "response": "...",
  "intent": "기록",
  "emotion": { "label": "기쁨", "intensity": 0.8 }
}
```

### 처리 흐름
1. session_id 기반 checkpointer 조회 → 첫 턴이면 전체 초기 State, 이후 턴이면 checkpoint 복원
2. `graph.ainvoke()` → 파이프라인 실행
3. 응답 즉시 반환
4. **BackgroundTasks**로 WAS 쓰기 + 피드백 루프 비동기 실행

---

## 8. 제약사항 및 플레이스홀더

> [!WARNING]
> 현재 미구현(플레이스홀더) 항목:

| 항목 | 위치 | 상태 |
|------|------|------|
| `MemorySaver` → 영속 체크포인터 | `builder.py` | 인메모리, 서버 재시작 시 소멸 |
| `_extract_plan_from_results()` | `was_write.py` | 응답→구조화 플랜 파싱 미구현 |
| `_web_search_stub()` | `search.py` | Web 검색 API 미연동 |
| `vdb_external` 데이터 적재 | 관리자 수동 | 적재 파이프라인 없음 |

---

## 9. 전체 아키텍처 개념도

```
사용자 ──▶ FastAPI (POST /chat)
              │
              ▼
        ┌─────────────────────────────────────────┐
        │         LangGraph StateGraph            │
        │                                         │
        │  preprocess ─▶ intent ─▶ [라우팅] ─▶    │
        │    ┌─ care ─▶ (search?) ─▶ generate    │
        │    ├─ record ─────────────▶ generate    │
        │    ├─ modify ─▶ search ──▶ generate    │
        │    ├─ search ────────────▶ generate    │
        │    ├─ safety ─────────────▶ END        │
        │    └─ fallback ─▶ (재추론 | END)       │
        │                                         │
        │  Gemini Flash: 응답 생성 + 자기 평가     │
        │  Gemini Flash-Lite: 의도 분석 + 평가    │
        └──────────────┬──────────────────────────┘
                       │
            ┌──────────┼──────────┐
            ▼          ▼          ▼
       WAS (RDB)   Pinecone   Checkpointer
       프로필/플랜   VDB 3종    세션 State
```
