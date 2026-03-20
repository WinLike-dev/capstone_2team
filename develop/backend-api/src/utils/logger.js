const { createLogger, format, transports } = require('winston');
const path = require('path');

const { combine, timestamp, printf, colorize, errors } = format;

// 로그 출력 포맷 정의
const logFormat = printf(({ level, message, timestamp, stack }) => {
  return `${timestamp} [${level}]: ${stack || message}`;
});

const logger = createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: combine(
    timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    errors({ stack: true }), // 에러 스택 트레이스 포함
    logFormat
  ),
  transports: [
    // 에러 로그 파일 저장
    new transports.File({
      filename: path.join('logs', 'error.log'),
      level: 'error',
    }),
    // 전체 로그 파일 저장
    new transports.File({
      filename: path.join('logs', 'combined.log'),
    }),
  ],
});

// 개발 환경에서는 컬러 콘솔 출력 추가
if (process.env.NODE_ENV !== 'production') {
  logger.add(
    new transports.Console({
      format: combine(
        colorize({ all: true }),
        timestamp({ format: 'HH:mm:ss' }),
        logFormat
      ),
    })
  );
}

module.exports = logger;
