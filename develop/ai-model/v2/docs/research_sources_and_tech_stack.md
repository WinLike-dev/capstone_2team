# 사용 논문/가이드 및 기술 스택

이 문서는 `ai-model/v2`가 현재 어떤 기술 스택으로 구성되어 있고, 외부 지식 적재 기준으로 어떤 논문/가이드를 사용하고 있는지 빠르게 파악하기 위한 문서입니다.

기준 파일:
- `requirements.txt`
- `scripts/build_external_knowledge.py`
- `data/external_knowledge.json`

## 1. 기술 스택

### API / 애플리케이션 레이어
- `FastAPI`
  - 메인 HTTP API 서버
  - 주요 엔드포인트: `/chat`, `/health`, `/internal/events/profile-updated`
- `Uvicorn`
  - FastAPI 실행 서버

### 상태 오케스트레이션
- `LangGraph`
  - 대화 그래프 실행 엔진
  - 주요 흐름: `preprocess -> intent -> search/record/modify/care -> generate -> persona`
- `langgraph-checkpoint`
  - 세션별 state checkpoint 인터페이스
- `langgraph-checkpoint-sqlite`
  - SQLite 기반 checkpoint 저장

### 데이터 검증 / 설정
- `Pydantic v2`
  - 요청/응답/LLM 구조화 출력 스키마 검증
- `pydantic-settings`
  - `.env` 기반 설정 로딩

### LLM / 임베딩
- `google-genai`
  - Gemini 호출 및 임베딩 생성
  - 구조화 출력, grounding 검색, embedding 생성에 사용
- `GeminiClient`
  - 프로젝트 내부 래퍼
  - `deps.gemini`, `deps.router` 두 클라이언트 설정을 분리해 사용

### 벡터 검색 / 외부 지식
- `Pinecone (asyncio)`
  - `memory`, `important`, `external` namespace 사용
  - 외부 지식 검색과 사용자 기억 검색에 사용

### HTTP / 외부 연동
- `httpx`
  - WAS API 통신
- `WASClient`
  - 사용자 프로필, 오늘 플랜, 승인된 계획 반영 호출 담당

### 저장 / 로컬 영속성
- `SQLite`
  - LangGraph checkpointer 저장소
- `aiosqlite`
  - 비동기 SQLite 연결

### 안정성 / 운영 보조
- `tenacity`
  - LLM 재시도 처리
- `python-dotenv`
  - 개발 환경 변수 로딩
- `langsmith`
  - 추적/관찰용 의존성

## 2. 현재 외부 지식 적재 기준

현재 외부 지식 문서는 `scripts/build_external_knowledge.py`에서 주제별 청크로 생성되고, Pinecone `external` namespace로 적재됩니다.

카테고리 축:
- `workout_resistance_guidelines`
- `workout_technique`
- `workout_program_design`
- `hypertrophy_volume`
- `hypertrophy_frequency`
- `cardio_guidelines`
- `hiit_programming`
- `hiit_fat_loss`
- `mobility_pnf`
- `stretching_performance`
- `nutrition_kdri`
- `nutrition_protein`
- `nutrition_timing`
- `nutrition_allergy`
- `supplement_creatine`
- `supplement_omega3`
- `physique_cutting`

## 3. 사용 중인 논문 / 가이드 목록

아래 목록은 현재 `build_external_knowledge.py`에 실제로 반영된 source 기준입니다.

### 운동 기술 / 계획
- `ACSM Resistance Training Position Stand (2026)`
  - 저항운동 처방 원칙, 초보자/고급자 기준, 강도/볼륨/빈도/진행 원칙
- `NSCA Exercise Technique Manual for Resistance Training, 4th ed`
  - 종목별 자세, 관절 정렬, spotting, 흔한 오류와 교정 포인트
- `NSCA Essentials of Strength Training and Conditioning, 5th ed`
  - 주기화, 디로딩, 피로관리, 훈련 로그, 프로그램 설계
- `Schoenfeld et al. (2017) Volume Meta-analysis`
  - 근비대 볼륨 관련 메타분석
- `Schoenfeld et al. (2016) Frequency Meta-analysis`
  - 근비대 빈도 관련 메타분석

### 유산소 / 컨디셔닝
- `ACSM Guidelines for Exercise Testing and Prescription, 12th ed`
  - FITT, 심박수, 위험도, 유산소 처방 기본축
- `Buchheit & Laursen (2013) HIIT Programming Puzzle Part I/II`
  - HIIT 구조와 생리학적 적응 원리
- `Sultana et al. (2019) Low-volume HIIT Review`
  - 저용량 HIIT의 시간 효율성과 체성분 적용

### 유연성 / 부상 예방
- `Hindle et al. (2012) PNF Stretching Review`
  - PNF 스트레칭 원리와 적용 방식
- `Behm et al. (2016) Stretching and Performance Review`
  - 스트레칭과 퍼포먼스 관계 해석

### 영양 / 식단
- `2025 한국인 영양소 섭취기준`
  - 한국 사용자 대상 기본 영양 기준
- `ISSN Position Stand: Protein and Exercise (2017)`
  - 총 단백질, 분배, 감량기/근비대 적용
- `ISSN Position Stand: Nutrient Timing (2017)`
  - 운동 전/중/후 영양 타이밍
- `EAACI Food Allergy Management (2024/2023)`
  - 식품 알레르기 회피, 대체식, 라벨 확인, 교차반응 주의

### 보충제 / 옵션
- `ISSN Position Stand: Creatine Supplementation and Exercise (2017)`
  - 크레아틴 로딩, 유지, 기대효과, 안전성
- `Omega-3 and Exercise Recovery Review (2025)`
  - 오메가-3와 운동 회복 관련 리뷰
- `Helms et al. (2014) Contest Preparation`
  - 피지크/감량기 특화 가이드

## 4. 이 문서를 읽을 때 주의할 점

- 위 source들은 현재 `v2`의 외부 지식 청크 생성 기준입니다.
- 즉, 모델이 직접 논문 PDF를 실시간 조회하는 구조는 아닙니다.
- 실제 응답은 이 source들을 바탕으로 사전 생성된 요약 청크를 Pinecone에서 검색해 사용합니다.
- 따라서 source 자체와 retrieval 청크 품질은 구분해서 봐야 합니다.

## 5. 관련 파일

- `requirements.txt`
- `scripts/build_external_knowledge.py`
- `data/external_knowledge.json`
- `app/clients/pinecone.py`
- `app/graph/nodes/search.py`
- `docs/v2_model_analysis.md`
