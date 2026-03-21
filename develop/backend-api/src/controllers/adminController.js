const supabase = require('../config/db');

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
      { count: totalUsers },
      { count: totalProfiles },
      { count: totalChatMessages },
      { data: recentUsers }
    ] = await Promise.all([
      supabase.from('users').select('*', { count: 'exact', head: true }),
      supabase.from('user_health_profiles').select('*', { count: 'exact', head: true }),
      supabase.from('chat_history').select('*', { count: 'exact', head: true }),
      supabase.from('users')
        .select('id, email, name, created_at')
        .order('created_at', { ascending: false })
        .limit(5)
    ]);

    // 3. 통계 결과 응답
    res.json({
      overview: {
        totalUsers: totalUsers || 0,
        totalProfiles: totalProfiles || 0,
        totalChatMessages: totalChatMessages || 0
      },
      recentSignups: recentUsers || []
    });
    
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};
