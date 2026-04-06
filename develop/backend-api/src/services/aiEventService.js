/**
 * AI 이벤트 서비스
 * WAS → FastAPI 이벤트 Push 로직
 * 
 * was_api_contract.md 섹션 4.1 기준
 * POST /internal/events/profile-updated
 */
const axios = require('axios');
const logger = require('../utils/logger');

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';
const AI_TIMEOUT = parseInt(process.env.AI_REQUEST_TIMEOUT) || 30000;

/**
 * 프로필 변경 이벤트를 FastAPI에 push
 * fire-and-forget: 실패해도 사용자 요청은 성공 처리
 * 
 * @param {string} userId - 변경된 사용자 ID
 * @param {string[]} changedFields - 변경된 필드 목록
 * @param {number|null} profileVersion - WAS가 관리하는 profile version (선택)
 */
exports.notifyProfileUpdated = async (userId, changedFields = [], profileVersion = null) => {
    try {
        const payload = {
            user_id: userId,
            changed_fields: changedFields
        };

        if (profileVersion !== null) {
            payload.profile_version = profileVersion;
        }

        const response = await axios.post(
            `${FASTAPI_URL}/internal/events/profile-updated`,
            payload,
            { timeout: AI_TIMEOUT }
        );

        logger.info(`프로필 변경 이벤트 push 성공: user_id=${userId}, fields=${changedFields.join(',')}`);
        return response.data;
    } catch (err) {
        // fire-and-forget: 로그만 남기고 에러를 throw하지 않음
        logger.error(`프로필 변경 이벤트 push 실패: user_id=${userId}, error=${err.message}`);
        return null;
    }
};
