const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
require('dotenv').config();
const { errorHandler, notFoundHandler } = require('./middleware/errorHandler');
const logger = require('./utils/logger');

const app = express();

// ─── 보안 및 기본 미들웨어 ────────────────────────────────────────────
app.use(helmet()); // HTTP 보안 헤더 자동 설정

// CORS: 허용할 프론트엔드 Origin을 환경변수로 관리
app.use(
  cors({
    // 로컬과 Vercel 모두 접근 가능하도록 모든 출처 허용 (개발/프로토타입 단계)
    origin: function (origin, callback) {
      callback(null, true);
    },
    credentials: true, // 쿠키/인증 헤더 허용
  })
);

// 요청 본문(Body) 파싱
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// ─── HTTP 요청 로깅 (morgan) ──────────────────────────────────────────
// 개발: 컬러 상세 로그, 프로덕션: 간결한 combined 포맷
const morganFormat = process.env.NODE_ENV === 'production' ? 'combined' : 'dev';
app.use(
  morgan(morganFormat, {
    stream: {
      // morgan 로그를 winston logger로 전달
      write: (message) => logger.http(message.trim()),
    },
  })
);

// ─── 헬스 체크 엔드포인트 ─────────────────────────────────────────────
app.get('/api/health', (req, res) => {
  res.status(200).json({
    success: true,
    message: '서버가 정상 동작 중입니다.',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development',
  });
});

// ─── API 라우터 (프론트엔드용) ────────────────────────────────────────
app.use('/api/v1/auth', require('./routes/auth'));
app.use('/api/v1/users', require('./routes/users'));
app.use('/api/v1/ai', require('./routes/ai'));
app.use('/api/v1/admin', require('./routes/admin'));
app.use('/api/v1/chat', require('./routes/chat'));

// ─── Internal API 라우터 (FastAPI/AI 서버용) ──────────────────────────
// was_api_contract.md 기준: /api/user/profile/:user_id 등
app.use('/api', require('./routes/internal'));

// ─── 에러 핸들러 (라우터 이후에 위치해야 함) ─────────────────────────
app.use(notFoundHandler);
app.use(errorHandler);

module.exports = app;
