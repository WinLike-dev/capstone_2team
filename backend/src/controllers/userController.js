const prisma = require('../config/db');

// @route   GET /api/v1/users/me
// @desc    내 프로필 정보 조회
// @access  Private
exports.getMe = async (req, res) => {
  try {
    const user = await prisma.user.findUnique({
      where: { id: req.user.id },
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
        createdAt: true,
      }
    });

    if (!user) {
      return res.status(404).json({ error: '사용자를 찾을 수 없습니다.' });
    }

    res.json(user);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   PUT /api/v1/users/me
// @desc    내 프로필 정보 수정
// @access  Private
exports.updateMe = async (req, res) => {
  try {
    const { name } = req.body;

    const user = await prisma.user.update({
      where: { id: req.user.id },
      data: { name },
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
      }
    });

    res.json({ message: '프로필이 업데이트되었습니다.', user });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   GET /api/v1/users/me/health
// @desc    내 건강 데이터 최신 조회
// @access  Private
exports.getHealthData = async (req, res) => {
  try {
    const healthDataList = await prisma.healthData.findMany({
      where: { userId: req.user.id },
      orderBy: { createdAt: 'desc' },
      take: 5 // 최근 5개만 가져오기
    });

    res.json(healthDataList);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   POST /api/v1/users/me/health
// @desc    내 건강 데이터 저장
// @access  Private
exports.saveHealthData = async (req, res) => {
  try {
    const { height, weight, bloodPressure, stressLevel } = req.body;

    const healthData = await prisma.healthData.create({
      data: {
        userId: req.user.id,
        height: height ? parseFloat(height) : null,
        weight: weight ? parseFloat(weight) : null,
        bloodPressure: bloodPressure || null,
        stressLevel: stressLevel ? parseInt(stressLevel) : null,
      }
    });

    res.status(201).json({ message: '건강 정보가 저장되었습니다.', healthData });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};
