const axios = require('axios');
const prisma = require('../config/db');

// @route   GET /api/v1/ai/plans
// @desc    특정 기간의 AI 운동/식단 플랜 조회
// @access  Private
exports.getPlans = async (req, res) => {
  try {
    // 예: /api/v1/ai/plans?startDate=2026-03-18&endDate=2026-03-24
    const { startDate, endDate } = req.query;
    if (!startDate || !endDate) return res.status(400).json({ error: 'startDate와 endDate가 필요합니다.' });

    const plans = await prisma.dailyPlan.findMany({
      where: {
        userId: req.user.id,
        date: {
          gte: new Date(startDate),
          lte: new Date(endDate)
        }
      },
      orderBy: { date: 'asc' }
    });

    // 만약 DB에 없다면 백엔드에서 AI 서버로 생성 요청 방식을 쓸 수도 있지만, 일단 DB에서 내려주는 것으로 구현
    res.json(plans);
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   POST /api/v1/ai/diet-analyze
// @desc    음식 텍스트를 AI로 전송하여 실시간 칼로리 및 피드백 분석
// @access  Private
exports.analyzeDiet = async (req, res) => {
  try {
    const { food } = req.body;
    if (!food) return res.status(400).json({ error: '음식 이름(food)을 입력해주세요.' });

    // AI 서버 주소 (환경변수 또는 로컬)
    const AI_URL = process.env.AI_SERVER_URL || 'http://localhost:8000';

    try {
      // 프론트엔드가 요청한 방식을 맞추기 위해 AI 서버에 POST 요청
      const response = await axios.post(`${AI_URL}/api/v1/analyze-diet`, { food });

      // AI 서버가 {"calories": 550, "feedback": "...", "suggestedExercise": "..."} 형태로 응답한다고 가정
      return res.json(response.data);
    } catch (aiError) {
      console.error('AI 서버 통신 실패:', aiError.message);
      // AI 서버가 다운되어 있을 때 데모용 더미 데이터 반환
      return res.json({
        calories: 550,
        feedback: `${food}는 맛있지만 나트륨이 높을 수 있어요. 식후에 가벼운 산책을 추천합니다.`,
        suggestedExercise: "가벼운 산책 20분"
      });
    }

  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};
