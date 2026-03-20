const prisma = require('../config/db');

// @route   GET /api/v1/admin/stats
// @desc    전체 이용 통계 조회 (관리자 전용)
// @access  Private/Admin
exports.getStats = async (req, res) => {
  try {
    // 1. 관리자 권한 확인 (authMiddleware 이후 동작)
    if (req.user.role !== 'ADMIN') {
      return res.status(403).json({ error: '관리자 권한이 필요합니다.' });
    }

    // 2. 통계 집계 병렬 처리
    const [
      totalUsers,
      totalHealthData,
      totalChatMessages,
      recentUsers
    ] = await Promise.all([
      prisma.user.count(),
      prisma.healthData.count(),
      prisma.chatHistory.count(),
      prisma.user.findMany({
        orderBy: { createdAt: 'desc' },
        take: 5,
        select: { id: true, email: true, name: true, createdAt: true }
      })
    ]);

    // 3. 통계 결과 응답
    res.json({
      overview: {
        totalUsers,
        totalHealthData,
        totalChatMessages
      },
      recentSignups: recentUsers
    });
    
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};
