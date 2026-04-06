# Oracle Cloud Docker 배포 가이드

이 문서는 `ai-model/v2`를 Oracle Cloud VM에 Docker로 배포할 때의 최소 절차를 정리한 문서입니다.

## 1. 배포 대상

- 앱: FastAPI + LangGraph 기반 `v2`
- 진입점: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- 기본 상태 확인: `GET /health`

## 2. 배포 전 준비

필수 준비 항목:

- Oracle Cloud VM에 Docker / Docker Compose 설치
- `v2/.env` 준비
- 외부 연동 확인
  - Gemini API
  - Pinecone
  - WAS
- VM 방화벽 또는 OCI 보안 규칙에서 `8000` 포트 허용

권장 확인 항목:

- `APP_ENV=production`
- `CHECKPOINT_DB_PATH=/app/data/checkpoints.sqlite`
- `./data` 볼륨 마운트로 세션 checkpoint 영속화

## 3. 포함된 배포 파일

- `Dockerfile`
- `.dockerignore`
- `docker-compose.yml`

`docker-compose.yml` 기준 기본 동작:

- 컨테이너 이름: `ai-hub-v2`
- 포트 매핑: `8000:8000`
- `.env` 주입
- `/app/data` 볼륨 마운트
- `GET /health` 기반 healthcheck

## 4. Oracle Cloud 배포 순서

### 4.1 서버 접속

```bash
ssh ubuntu@<oracle-vm-ip>
```

### 4.2 코드 업로드 또는 pull

예시:

```bash
cd /srv
git clone <repo-url>
cd capstone_2team/develop/ai-model/v2
```

또는 이미 받아둔 레포라면 최신 코드로 갱신합니다.

### 4.3 환경변수 파일 준비

`.env`에 아래 계열 값이 들어 있어야 합니다.

- `GEMINI_API_KEY`
- `GEMINI_MODEL_NAME`
- `ROUTER_API_KEY`
- `ROUTER_MODEL_NAME`
- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME`
- `WAS_BASE_URL`
- `WAS_TIMEOUT`
- `LANGCHAIN_*` 계열 값

운영 권장값:

- `APP_ENV=production`
- `LOG_LEVEL=INFO`

## 5. 컨테이너 실행

### 5.1 빌드 및 실행

```bash
docker compose up -d --build
```

### 5.2 상태 확인

```bash
docker compose ps
docker compose logs -f ai-hub-v2
```

### 5.3 헬스체크 확인

```bash
curl http://localhost:8000/health
```

정상 예시:

```json
{
  "status": "ok",
  "env": "production",
  "version": "v2"
}
```

## 6. v1 -> v2 전환 체크

전환 전에 확인할 것:

- 클라이언트가 호출하는 메인 API가 여전히 `POST /chat`인지
- WAS가 v2 서버의 `/internal/events/profile-updated`를 호출하도록 바뀌었는지
- `selected_ai_persona`가 WAS profile 응답에 포함되는지
- reverse proxy 또는 도메인이 새 컨테이너를 바라보는지

주의:

- `v1`과 `v2`의 checkpoint/session은 그대로 이어지지 않을 수 있으니 새 세션으로 보는 편이 안전합니다.
- `debug` 엔드포인트는 개발용이므로 운영에서는 외부 노출 범위를 제한하는 것이 좋습니다.

## 7. 운영 중 자주 쓰는 명령

재시작:

```bash
docker compose restart ai-hub-v2
```

중지:

```bash
docker compose down
```

이미지 재빌드 포함 재실행:

```bash
docker compose up -d --build
```

로그 확인:

```bash
docker compose logs -f ai-hub-v2
```

## 8. 첫 배포 후 최소 점검

- `/health` 응답 확인
- `/chat` 1회 스모크 테스트
- WAS profile fetch 성공 확인
- persona 반영 확인
- 계획 승인 후 WAS write 성공 확인
- profile-updated 이벤트 후 다음 턴 refresh 확인
