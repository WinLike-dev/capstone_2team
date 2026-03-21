const axios = require('axios');
const supabase = require('../config/db');

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';
const AI_TIMEOUT = parseInt(process.env.AI_REQUEST_TIMEOUT) || 30000;

// @route   POST /api/v1/chat
// @desc    AI 채팅 메시지 전송 및 FastAPI 중계 (DataFormat_3_ai)
// @access  Private
exports.sendMessage = async (req, res) => {
  try {
    const { message } = req.body;

    if (!message) {
      return res.status(400).json({ error: '메시지를 입력해주세요.' });
    }

    // 1. 유저 건강 프로필 조회 (AI 요청에 포함할 컨텍스트)
    const { data: profile } = await supabase
      .from('user_health_profiles')
      .select('*')
      .eq('user_id', req.user.id)
      .single();

    // 2. DataFormat_3_ai 규격에 맞게 AI 서버로 요청
    const payload = {
      user_id: req.user.id,
      user_profile: profile ? {
        gender: profile.gender,
        age: profile.age,
        bmi: profile.bmi,
        goal: profile.goal
      } : {},
      user_instruction: profile?.user_instruction || '',
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

    // 3. 채팅 이력 DB 저장
    const { data: chatRecord, error } = await supabase
      .from('chat_history')
      .insert({
        user_id: req.user.id,
        user_message: message,
        ai_response: JSON.stringify(aiResponseData)
      })
      .select()
      .single();

    if (error) {
      console.error('채팅 이력 저장 실패:', error.message);
    }

    // 4. 모드 6 (DB 수정) 처리 — AI가 user_health_profiles 필드 수정을 요청한 경우
    if (aiResponseData?.mode === 6 && aiResponseData?.data?.db_update) {
      const { field, new_value } = aiResponseData.data.db_update;
      const { error: updateErr } = await supabase
        .from('user_health_profiles')
        .update({ [field]: new_value })
        .eq('user_id', req.user.id);

      if (updateErr) console.error('DB 수정 실패:', updateErr.message);
    }

    // 5. 프론트엔드로 응답 반환
    res.json(aiResponseData);

  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   GET /api/v1/chat/history
// @desc    내 채팅 이력 조회
// @access  Private
exports.getHistory = async (req, res) => {
  try {
    const { data: history, error } = await supabase
      .from('chat_history')
      .select('*')
      .eq('user_id', req.user.id)
      .order('created_at', { ascending: false })
      .limit(50);

    if (error) throw error;
    res.json(history || []);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};
