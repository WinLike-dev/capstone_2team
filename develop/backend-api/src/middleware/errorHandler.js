const logger = require('../utils/logger');

/**
 * 전역 에러 핸들러 미들웨어
 * express-validator 오류 및 일반 서버 오류를 통합 처리합니다.
 */
const errorHandler = (err, req, res, next) => {
  const statusCode = err.statusCode || 500;
  const message = err.message || '서버 내부 오류가 발생했습니다.';

  logger.error(`[${req.method}] ${req.path} >> StatusCode:: ${statusCode}, Message:: ${message}`, err);

  res.status(statusCode).json({
    success: false,
    statusCode,
    message,
    // 개발 환경에서만 스택 트레이스 노출
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack }),
  });
};

/**
 * 정의되지 않은 라우트 처리 (404)
 */
const notFoundHandler = (req, res, next) => {
  const error = new Error(`요청한 경로를 찾을 수 없습니다: ${req.originalUrl}`);
  error.statusCode = 404;
  next(error);
};

module.exports = { errorHandler, notFoundHandler };
