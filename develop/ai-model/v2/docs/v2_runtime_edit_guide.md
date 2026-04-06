# v2 Runtime Edit Guide

이 문서는 `develop/ai-model/v2` 기준으로,
- 운영자(관리자)가 직접 수정 가능한 파일
- 프론트엔드 / 백엔드 / AI 개발자가 같이 알아야 할 연결 지점
- 각 파일이 어떤 노드의 시스템 지시사항인지
를 한 번에 정리한 문서입니다.

## 1. 먼저 알아둘 핵심

- `v2` 런타임이 실제로 읽는 프롬프트 파일들은 `develop/ai-model/v2/app/prompts/` 아래에 있습니다.
- persona 설정의 기준 파일은 `persona.json`이 아니라 `registry.json`입니다.
- persona의 공식 source of truth는 WAS 프로필의 `selected_ai_persona` 입니다.
- 루트 `docs/router_system_instruction.txt`, `docs/worker_system_instruction.txt`, `docs/ai_io_instruction.txt` 는 현재 `v2` 런타임이 직접 읽는 파일이 아니라 참고 문서에 가깝습니다.

## 2. 공통 구조

### 2.1 프롬프트 로더

- 파일명: `prompt_loader.py`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\core\prompt_loader.py`
- 역할:
  - `app/prompts/` 아래 텍스트 파일을 실제 런타임에서 읽는 공통 로더입니다.
  - `v2`가 어떤 프롬프트를 쓰는지 확인할 때 가장 먼저 봐야 하는 파일입니다.

### 2.2 노드 프롬프트 폴더

- 폴더명: `app/prompts/nodes`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\prompts\nodes`
- 역할:
  - `intent`, `search`, `generate` 노드의 시스템 지시사항이 들어 있습니다.
  - 각 노드가 어떤 규칙으로 판단하고 응답 초안을 만드는지 정의합니다.

### 2.3 persona 프롬프트 폴더

- 폴더명: `app/prompts/personas`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\prompts\personas`
- 역할:
  - 최종 응답의 말투, 분위기, 캐릭터 표현을 담당하는 Persona 노드용 프롬프트가 들어 있습니다.
  - Draft의 사실을 바꾸지 않고 말투만 바꾸는 레이어입니다.

## 3. 운영자가 직접 수정 가능한 런타임 파일

### 3.1 Intent 노드 시스템 지시사항

- 파일명: `system.md`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\prompts\nodes\intent\system.md`
- 연결 코드: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\graph\nodes\intent.py`
- 어떤 노드의 지시사항인가:
  - `analyze_intent` 노드의 시스템 지시사항입니다.
- 구체적 역할:
  - 사용자의 메시지를 어떤 intent로 분류할지 정합니다.
  - 예: `casual`, `계획`, `정보`, `수정`, `공감_케어`, `안전경고`, `fallback`
- 수정 시 영향:
  - 이후 어떤 노드로 라우팅되는지가 바뀝니다.
  - 즉, 전체 대화 흐름의 첫 관문입니다.

### 3.2 Search 노드 시스템 지시사항

#### A. 검색 품질 평가 규칙

- 파일명: `eval.md`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\prompts\nodes\search\eval.md`
- 연결 코드: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\graph\nodes\search.py`
- 어떤 노드의 지시사항인가:
  - `search` 노드의 검색 결과 품질 평가용 시스템 지시사항입니다.
- 구체적 역할:
  - 검색 결과가 질문에 충분히 맞는지 점수화합니다.
  - 점수가 낮으면 재시도하거나 `degraded`로 내려갑니다.

#### B. 검색어 재작성 규칙

- 파일명: `query_regen.md`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\prompts\nodes\search\query_regen.md`
- 연결 코드: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\graph\nodes\search.py`
- 어떤 노드의 지시사항인가:
  - `search` 노드의 검색어 재작성용 시스템 지시사항입니다.
- 구체적 역할:
  - 검색이 부실했을 때 더 나은 검색어를 다시 만듭니다.

### 3.3 Generate 노드 시스템 지시사항

#### A. Draft 공통 원칙

- 파일명: `draft_common.md`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\prompts\nodes\generate\draft_common.md`
- 연결 코드: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\graph\nodes\generate.py`
- 어떤 노드의 지시사항인가:
  - `generate` 노드의 공통 시스템 지시사항입니다.
- 구체적 역할:
  - 모든 Draft 응답에 공통으로 적용되는 기본 규칙입니다.
  - `core_message`, `reason_points`, `suggested_action`, `approval_question` 같은 구조의 기본 기준을 만듭니다.

#### B. 기본 Draft 규칙

- 파일명: `draft_default.md`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\prompts\nodes\generate\draft_default.md`
- 연결 코드: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\graph\nodes\generate.py`
- 어떤 노드의 지시사항인가:
  - `generate` 노드에서 기본 fallback 성격의 Draft를 만들 때 쓰는 시스템 지시사항입니다.

#### C. 계획 제안 Draft 규칙

- 파일명: `draft_plan.md`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\prompts\nodes\generate\draft_plan.md`
- 연결 코드: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\graph\nodes\generate.py`
- 어떤 노드의 지시사항인가:
  - `generate` 노드에서 `계획` intent 처리 시 사용하는 시스템 지시사항입니다.
- 구체적 역할:
  - 운동/식단 계획 초안을 어떻게 제안할지 정합니다.

#### D. 수정 Draft 규칙

- 파일명: `draft_modify.md`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\prompts\nodes\generate\draft_modify.md`
- 연결 코드: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\graph\nodes\generate.py`
- 어떤 노드의 지시사항인가:
  - `generate` 노드에서 `수정` intent 처리 시 사용하는 시스템 지시사항입니다.
- 구체적 역할:
  - 기존 플랜을 어떻게 고쳐서 제안할지 정합니다.

#### E. 정보성 Draft 규칙

- 파일명: `draft_info.md`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\prompts\nodes\generate\draft_info.md`
- 연결 코드: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\graph\nodes\generate.py`
- 어떤 노드의 지시사항인가:
  - `generate` 노드에서 `정보` intent 처리 시 사용하는 시스템 지시사항입니다.
- 구체적 역할:
  - 설명형, 안내형 답변의 Draft 구조를 정합니다.

#### F. 공감/케어 Draft 규칙

- 파일명: `draft_care.md`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\prompts\nodes\generate\draft_care.md`
- 연결 코드: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\graph\nodes\generate.py`
- 어떤 노드의 지시사항인가:
  - `generate` 노드에서 `공감_케어` intent 처리 시 사용하는 시스템 지시사항입니다.
- 구체적 역할:
  - 정서적 배려가 필요한 응답의 Draft 기준을 정합니다.

#### G. 안전 응답 Draft 규칙

- 파일명: `draft_safety.md`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\prompts\nodes\generate\draft_safety.md`
- 연결 코드: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\graph\nodes\generate.py`
- 어떤 노드의 지시사항인가:
  - `generate` 노드에서 `안전경고` intent 처리 시 사용하는 시스템 지시사항입니다.
- 구체적 역할:
  - 위험 신호가 있을 때 안전 우선 메시지를 어떻게 구성할지 정합니다.

#### H. 자기 평가 규칙

- 파일명: `self_eval.md`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\prompts\nodes\generate\self_eval.md`
- 연결 코드: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\graph\nodes\generate.py`
- 어떤 노드의 지시사항인가:
  - `generate` 노드가 만든 Draft를 다시 검사하는 자기 평가용 시스템 지시사항입니다.
- 구체적 역할:
  - care/safety 응답이 기준을 충족하는지 판단하고, 필요 시 재시도하게 합니다.

### 3.4 Persona 노드 설정 파일

#### A. persona registry

- 파일명: `registry.json`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\prompts\personas\registry.json`
- 연결 코드:
  - `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\core\persona_registry.py`
  - `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\graph\nodes\persona.py`
- 어떤 노드의 지시사항인가:
  - `persona` 노드가 어떤 persona 프롬프트 파일을 쓸지 정하는 설정 파일입니다.
- 구체적 역할:
  - 기본 persona 지정
  - persona id 목록 관리
  - 각 persona의 `label`, `prompt_file`, `active`, `fallback` 관리
- 중요:
  - 현재 `v2`에는 `persona.json`이 없고, 실제 기준은 이 `registry.json`입니다.

#### B. Persona 노드 프롬프트 파일들

- 파일명: `default.md`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\prompts\personas\default.md`
- 역할:
  - `persona` 노드의 기본 코치 톤 시스템 지시사항입니다.

- 파일명: `warm.md`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\prompts\personas\warm.md`
- 역할:
  - `persona` 노드의 따뜻하고 배려 있는 코치 톤 시스템 지시사항입니다.

- 파일명: `spartan.md`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\prompts\personas\spartan.md`
- 역할:
  - `persona` 노드의 단호하고 간결한 코치 톤 시스템 지시사항입니다.

- 파일명: `evidence.md`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\prompts\personas\evidence.md`
- 역할:
  - `persona` 노드의 근거 중심 설명형 코치 톤 시스템 지시사항입니다.

- 파일명: `buddy.md`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\prompts\personas\buddy.md`
- 역할:
  - `persona` 노드의 친근한 친구형 코치 톤 시스템 지시사항입니다.

- 공통 설명:
  - 이 파일들은 모두 `persona` 노드에서 읽습니다.
  - 역할은 Draft의 사실을 바꾸는 것이 아니라, 최종 응답의 말투와 분위기를 바꾸는 것입니다.

## 4. 프론트엔드 개발자에게 설명할 포인트

- 프론트가 알아야 하는 핵심 파일
  - `api_specification.md`
  - 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\docs\api_specification.md`
  - 설명:
    - `/chat`, `/debug`, `/health` 요청/응답 구조를 설명하는 문서입니다.

- 프론트가 반드시 맞춰야 하는 값
  - `selected_ai_persona`
  - 설명:
    - 사용자 persona 선택값은 결국 이 필드명으로 저장되고 전달되어야 합니다.
    - 드롭다운이나 선택 UI에서 쓰는 persona id는 `registry.json`의 키와 정확히 일치해야 합니다.

- 프론트가 주의할 점
  - `user_profile_override`는 개발/디버그용입니다.
  - 운영 기능으로 persona를 바꿀 때는 백엔드의 실제 프로필 저장 API를 통해 `selected_ai_persona`를 바꿔야 합니다.

## 5. 백엔드 개발자에게 설명할 포인트

- 백엔드가 알아야 하는 핵심 문서
  - 파일명: `was_api_contract.md`
  - 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\docs\was_api_contract.md`
  - 설명:
    - WAS와 AI 모델 서버 간 계약 문서입니다.
    - `selected_ai_persona`가 어떤 필드명으로 오고 가는지 명확히 적혀 있습니다.

- 백엔드가 맞춰야 하는 코드 기준
  - 파일명: `was.py`
  - 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\schemas\was.py`
  - 설명:
    - AI 서버가 기대하는 프로필 응답/업데이트 스키마가 정의되어 있습니다.
    - `selected_ai_persona` 필드가 포함되어야 합니다.

- 백엔드가 실제 호출 경로를 확인할 파일
  - 파일명: `was.py`
  - 주소: `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\clients\was.py`
  - 설명:
    - `GET /api/user/profile/{user_id}`
    - `PUT /api/user/profile/{user_id}`
    - `POST /api/plan/create/{user_id}`
    - `PUT /api/plan/update/{user_id}`
    - `PUT /api/plan/check/{user_id}`
    - 같은 실제 호출 경로를 확인할 수 있습니다.

- 백엔드가 꼭 알아야 하는 규칙
  - persona의 source of truth는 WAS 프로필의 `selected_ai_persona`
  - 프로필 변경 후에는 `POST /internal/events/profile-updated` 로 AI 서버에 이벤트를 보내야 함
  - 변경은 현재 턴이 아니라 다음 `/chat` 턴에서 반영됨

## 6. AI 개발자에게 설명할 포인트

- AI 개발자가 가장 먼저 봐야 하는 파일
  - `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\graph\nodes\intent.py`
  - `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\graph\nodes\search.py`
  - `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\graph\nodes\generate.py`
  - `C:\Users\ksh00\anti_projects\capstone_2team\develop\ai-model\v2\app\graph\nodes\persona.py`

- 각 노드와 수정 파일의 관계
  - `intent.py`
    - `app/prompts/nodes/intent/system.md` 를 읽음
    - 의도 분류 규칙 변경 시 같이 확인해야 함
  - `search.py`
    - `app/prompts/nodes/search/eval.md`
    - `app/prompts/nodes/search/query_regen.md`
    - 를 읽음
  - `generate.py`
    - `app/prompts/nodes/generate/*.md`
    - 를 읽음
    - 초안 구조, 계획 제안, 안전 응답, self-eval 흐름과 연결됨
  - `persona.py`
    - `app/prompts/personas/registry.json`
    - `app/prompts/personas/*.md`
    - 를 읽음
    - 최종 말투/스타일을 담당함

- AI 개발자가 주의할 점
  - Draft와 Persona의 책임을 섞으면 안 됩니다.
  - 사실, 근거, 계획은 `generate`가 담당합니다.
  - 말투, 분위기, 캐릭터성은 `persona`가 담당합니다.
  - 새 persona를 추가할 때는 `md 파일 추가 + registry.json 등록`이 필요합니다.

## 7. 운영자가 바꿔도 비교적 안전한 항목

- `registry.json`의 `label`
- `registry.json`의 `active`
- `registry.json`의 `default_persona`
- 각 persona `*.md` 파일의 말투와 표현 방식
- `intent/system.md` 의 분류 기준 문구
- `generate/*.md` 의 응답 작성 원칙
- `search/*.md` 의 검색 평가 및 재작성 기준

## 8. 운영자가 바꿀 때 특히 조심해야 하는 항목

- `selected_ai_persona` 필드명 변경
- `registry.json` 안 persona id 이름 변경
- `prompt_file` 파일명 변경 후 실제 파일을 같이 바꾸지 않는 경우
- API 계약 문서와 실제 구현 스키마를 다르게 바꾸는 경우
- Persona 프롬프트에서 Draft의 사실을 바꾸도록 유도하는 경우

## 9. 참고 문서이지만 v2 런타임이 직접 읽지 않는 파일

- 파일명: `router_system_instruction.txt`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\docs\router_system_instruction.txt`
- 설명:
  - 예전 구조나 팀 논의용 참고 자료입니다.

- 파일명: `worker_system_instruction.txt`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\docs\worker_system_instruction.txt`
- 설명:
  - 예전 워커 기반 구조 설명용 참고 자료입니다.

- 파일명: `ai_io_instruction.txt`
- 주소: `C:\Users\ksh00\anti_projects\capstone_2team\docs\ai_io_instruction.txt`
- 설명:
  - 전체 I/O 구조 설명 참고 자료입니다.

- 주의:
  - 이 파일들은 지금 `v2` 런타임이 직접 읽는 프롬프트 파일이 아닙니다.
  - 실제 운영 반영은 `develop/ai-model/v2/app/prompts/` 아래 파일을 수정해야 합니다.

## 10. 팀에 바로 공유할 짧은 문장

`운영자가 실제로 수정하는 런타임 파일은 develop/ai-model/v2/app/prompts/nodes/* 와 develop/ai-model/v2/app/prompts/personas/* 이고, persona 설정 파일은 persona.json이 아니라 registry.json입니다. 프론트와 백엔드는 selected_ai_persona 필드명을 기준으로 맞추고, AI 개발자는 각 노드가 어떤 prompt 파일을 읽는지 함께 확인해야 합니다.`
