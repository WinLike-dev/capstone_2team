const axios = require('axios');
const supabase = require('../config/db');

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';
const AI_TIMEOUT = parseInt(process.env.AI_REQUEST_TIMEOUT) || 30000;

// @route   POST /api/v1/chat
// @desc    AI 채팅 메시지 전송 및 FastAPI 중계 (DataFormat_3_ai)
// @access  Public (프로토타입 — 인증 미들웨어 없음)
exports.sendMessage = async (req, res) => {
    try {
        const { user_id, message } = req.body;

        if (!user_id) {
            return res.status(400).json({ error: 'user_id가 필요합니다.' });
        }
        if (!message) {
            return res.status(400).json({ error: '메시지를 입력해주세요.' });
        }

        // 1. 유저 건강 프로필 조회 (AI 요청에 포함할 컨텍스트)
        const { data: profile } = await supabase
            .from('user_health_profiles')
            .select('*')
            .eq('user_id', user_id)
            .single();

        // 2. DataFormat_3_ai 규격에 맞게 AI 서버로 요청 (POST /ai-chat)
        const payload = {
            user_id,
            user_profile: profile ? {
                gender: profile.gender,
                age: profile.age,
                bmi: profile.bmi,
                goal: profile.goal
            } : {},
            user_message: message
        };

        let aiResponseData = null;

        try {
            const response = await axios.post(`${FASTAPI_URL}/ai-chat`, payload, { timeout: AI_TIMEOUT });
            aiResponseData = response.data;
        } catch (aiError) {
            console.error('AI 서버 통신 실패:', aiError.message);
            aiResponseData = {
                status: 'fallback',
                mode: 1,
                data: {
                    message: '현재 AI 서버와 통신할 수 없습니다. 잠시 후 다시 시도해주세요.'
                }
            };
        }

        // 4. 프론트엔드로 응답 반환
        // (채팅 이력 저장은 AI팀이 Vector DB에서 처리)
        res.json(aiResponseData);

    } catch (err) {
        console.error(err);
        res.status(500).json({ error: '서버 에러가 발생했습니다.' });
    }
};