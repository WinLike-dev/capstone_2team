const axios = require('axios');
const prisma = require('../config/db');

// @route   POST /api/v1/chat
// @desc    채팅 메시지 전송 및 AI 서버 중계
// @access  Private
exports.sendMessage = async (req, res) => {
  try {
    const { message } = req.body;

    if (!message) {
      return res.status(400).json({ error: '메시지를 입력해주세요.' });
    }

    // 1. 유저의 최근 건강 데이터를 가져와서 Context로 구성 (선택사항, AI 서버 요구에 따라)
    const recentHealth = await prisma.healthData.findFirst({
      where: { userId: req.user.id },
      orderBy: { createdAt: 'desc' }
    });

    const context = {
      userId: req.user.id,
      healthData: recentHealth || null,
      message: message
    };

    // 2. AI 서버(FastAPI)로 요청 전달
    let aiResponseText = '';
    let uiComponents = null;

    try {
      // AI_SERVER_URL은 .env에 "http://localhost:8000" 등으로 세팅
      const aiServerUrl = process.env.AI_SERVER_URL || 'http://localhost:8000';
      
      const response = await axios.post(`${aiServerUrl}/api/v1/generate`, context);
      
      // AI 서버 응답 구조 가정: { text: "답변", ui_components: { theme: "rainy" } }
      aiResponseText = response.data.text || JSON.stringify(response.data);
      uiComponents = response.data.ui_components || null;

    } catch (aiError) {
      console.error('AI 서버 통신 실패:', aiError.message);
      // Fallback 응답 처리 (AI 서버가 죽었을 때)
      aiResponseText = "현재 AI 서버와 통신할 수 없습니다. 잠시 후 다시 시도해주세요.";
    }

    // 3. 채팅 이력 DB 저장
    const chatHistory = await prisma.chatHistory.create({
      data: {
        userId: req.user.id,
        userMessage: message,
        aiResponse: aiResponseText, // JSON 텍스트 또는 일반 텍스트
      }
    });

    // 4. 프론트엔드로 응답 반환
    res.json({
      chat: chatHistory,
      ui_components: uiComponents
    });

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
    const history = await prisma.chatHistory.findMany({
      where: { userId: req.user.id },
      orderBy: { createdAt: 'desc' },
      take: 50 // 최근 50개만
    });

    res.json(history);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};
