# Node Prompt Layout

이 디렉터리는 `intent`, `search`, `generate` 노드의 시스템 지시사항을 코드 밖으로 분리한 곳입니다.

구조:
- `intent/system.md`: 의도 분류 규칙
- `search/eval.md`: 검색 결과 품질 평가 규칙
- `search/query_regen.md`: 검색 쿼리 재작성 규칙
- `generate/draft_common.md`: Draft 공통 원칙
- `generate/draft_*.md`: 의도별 Draft 보강 규칙
- `generate/self_eval.md`: 자기 평가 규칙

운영 원칙:
- 사실/근거 선택은 `generate`가 담당합니다.
- 말투/세계관/캐릭터 표현은 `personas/`가 담당합니다.
- persona 프롬프트는 Draft의 사실을 바꾸면 안 됩니다.

새 프롬프트를 추가할 때:
1. 먼저 이 디렉터리에 텍스트 파일을 추가합니다.
2. 해당 노드의 매핑 코드에서 새 파일을 연결합니다.
3. 필요하면 관련 문서와 debug 경로를 함께 갱신합니다.
