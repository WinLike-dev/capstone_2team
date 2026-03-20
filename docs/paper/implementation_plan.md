# AI 헬스케어 백엔드 서버 구축 계획

Node.js + Express 기반의 헬스케어 백엔드 API 서버를 구축합니다. 프론트엔드(Next.js)와 AI 서버(FastAPI) 사이에서 API Gateway 역할을 수행하며, JWT 인증, PostgreSQL DB 연동, 채팅 중계 API를 포함합니다.

## 제안된 변경사항

### Backend 폴더 구조

```
capstone_2team/
└── backend/
    ├── src/
    │   ├── config/          # DB, 환경변수 설정
    │   ├── middleware/      # 인증, 에러 핸들러
    │   ├── routes/          # API 라우터 정의
    │   ├── controllers/     # 비즈니스 로직
    │   ├── models/          # Sequelize ORM 모델
    │   ├── services/        # AI 서버 연동 등 서비스 레이어
    │   ├── utils/           # 로거 등 유틸리티
    │   ├── app.js           # Express 앱 설정
    │   └── server.js        # 서버 엔트리포인트
    ├── prisma/
    │   └── schema.prisma    # DB 스키마 (User, HealthData, ChatHistory)
    ├── .env.example         # 환경변수 템플릿
    ├── .gitignore
    └── package.json
```

---

### 패키지 구성

#### 프로덕션 의존성
| 패키지 | 역할 |
|--------|------|
| `express` | 웹 프레임워크 |
| `@prisma/client` | DB ORM 클라이언트 |
| `prisma` | DB 스키마 및 마이그레이션 |
| `jsonwebtoken` | JWT 토큰 생성/검증 |
| `bcryptjs` | 비밀번호 해싱 |
| `cors` | CORS 허용 |
| `dotenv` | 환경변수 로드 |
| `morgan` | HTTP 요청 로깅 |
| `winston` | 서버 로깅 |
| `axios` | AI 서버(FastAPI) HTTP 요청 |
| `express-validator` | 요청 데이터 유효성 검사 |
| `helmet` | 보안 헤더 설정 |

#### 개발 의존성
| 패키지 | 역할 |
|--------|------|
| `nodemon` | 핫 리로드 |
| `eslint` | 코드 품질 |

---

### API 엔드포인트 설계

#### 인증 (`/api/v1/auth`)
| Method | Path | 설명 |
|--------|------|------|
| POST | `/register` | 회원가입 |
| POST | `/login` | 로그인 (JWT 발급) |
| POST | `/logout` | 로그아웃 |

#### 사용자 (`/api/v1/users`)
| Method | Path | 설명 | 인증 필요 |
|--------|------|------|-----------|
| GET | `/me` | 내 정보 조회 | ✅ |
| PUT | `/me` | 내 정보 수정 | ✅ |
| GET | `/me/health` | 건강 데이터 조회 | ✅ |
| POST | `/me/health` | 건강 데이터 저장 | ✅ |

#### AI 채팅 (`/api/v1/chat`)
| Method | Path | 설명 | 인증 필요 |
|--------|------|------|-----------|
| POST | `/` | 채팅 메시지 전송 → AI 서버 중계 | ✅ |
| GET | `/history` | 채팅 이력 조회 | ✅ |

#### 관리자 (`/api/v1/admin`)
| Method | Path | 설명 | 인증 필요 |
|--------|------|------|-----------|
| GET | `/stats` | 전체 통계 (가입자 수, AI 요청 수 등) | ✅ (Admin) |

---

### DB 스키마 (Prisma)

- **User**: id, email, passwordHash, name, role(USER/ADMIN), createdAt
- **HealthData**: id, userId, height, weight, bloodPressure, stressLevel, createdAt
- **ChatHistory**: id, userId, userMessage, aiResponse, createdAt

---

## 검증 계획

### 자동화 테스트
```bash
# 서버 실행 확인
cd backend
npm run dev
```

### API 수동 테스트 (curl)
```bash
# 회원가입
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"1234","name":"테스터"}'

# 로그인
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"1234"}'

# 내 정보 조회 (토큰 필요)
curl http://localhost:5000/api/v1/users/me \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

> [!IMPORTANT]
> PostgreSQL DB 연결을 위해 나중에 `.env` 파일에 `DATABASE_URL`을 직접 입력해야 합니다. DB 설정 전까지 서버는 실행되지만 DB 관련 API는 동작하지 않습니다.
