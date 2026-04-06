/**
 * 서버 간 인증 미들웨어
 * FastAPI(AI) → WAS 호출 시 x-api-key 헤더로 인증
 */
const logger = require('../utils/logger');

const INTERNAL_API_KEY = process.env.INTERNAL_API_KEY;

const internalAuth = (req, res, next) => {
    // INTERNAL_API_KEY가 .env에 설정되지 않았으면 인증 건너뛰기 (개발 편의)
    if (!INTERNAL_API_KEY) {
        logger.warn('INTERNAL_API_KEY가 설정되지 않았습니다. 서버 간 인증을 건너뜁니다.');
        return next();
    }

    const apiKey = req.headers['x-api-key'];

    if (!apiKey || apiKey !== INTERNAL_API_KEY) {
        logger.warn(`Internal API 인증 실패: ${req.method} ${req.path}`);
        return res.status(403).json({ error: 'Forbidden: Invalid API Key' });
    }

    next();
};

module.exports = internalAuth;
