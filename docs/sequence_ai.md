# AI Sequence Diagrams

이 문서는 WAS와 FastAPI 간의 상호작용을 Mermaid 시퀀스 다이어그램으로 시각화한 문서입니다.

## 1. 전역 AI 통신 구조 (Overall Flow)

전체적인 대화 및 추천 프로세스 흐름은 아래와 같습니다.

```mermaid
sequenceDiagram
    participant FE as Front-end (Next.js)
    participant BE as WAS (Node.js)
    participant AI as AI Server (FastAPI)
    participant VDB as Vector DB (Pinecone)
    participant LLM as Gemini Flash

    Note over FE, LLM: [Production] 대화 및 추천 흐름

    FE->>BE: 1. 유저 요청 전송
    BE->>AI: 2. 컨텍스트와 함께 요청 (POST /ai-chat, /process-meal, /recommend)
    
    rect rgb(240, 248, 255)
        Note right of AI: AI 내부 처리 및 정보 확보
        
        AI-->>VDB: 3a. 이전 대화 기록 검색 (Search)
        
        alt Mode 3 (플랜 수정) 또는 Mode 5 (식단 수정)
            AI->>BE: 3b. 현재 리스트 조회 (GET /api/exercise-list 또는 /meal-list)
            BE-->>AI: 리스트 데이터 반환
        end
    end

    AI->>LLM: 4. 최종 프롬프트 전달
    LLM-->>AI: 5. 정형화된 JSON 응답
    
    AI->>BE: 6. 정제된 데이터 반환
    BE->>FE: 7. 최종 응답 및 UI 업데이트
    
    par Background Task
        AI->>VDB: 8. 대화 요약 및 컨텍스트 저장 (Upsert)
    end
```

## 2. 상세 시퀀스 다이어그램 목록

각 시퀀스별 상세 내용은 아래 개별 문서에서 확인할 수 있습니다.

- [Sequence_0: MBTI 설정](sequence_0.md)
- [Sequence_1: 전역 흐름](sequence_1.md)
- [Sequence_1_ai: 식단/추천 상세](sequence_1_ai.md)
- [Sequence_2_ai: 상세 AI 통신](sequence_2_ai.md)
