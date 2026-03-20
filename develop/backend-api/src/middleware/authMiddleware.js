const jwt = require('jsonwebtoken');

module.exports = function(req, res, next) {
  // 1. 헤더에서 토큰 가져오기
  const authHeader = req.header('Authorization');

  // 2. 토큰 존재 확인
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: '인증 토큰이 없습니다. 접근이 거부되었습니다.' });
  }

  const token = authHeader.split(' ')[1];

  // 3. 토큰 검증
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    
    // 검증된 유저 정보를 req 객체에 저장 (다음 미들웨어나 라우트에서 사용)
    req.user = decoded.user;
    next();
  } catch (err) {
    res.status(401).json({ error: '유효하지 않은 토큰입니다.' });
  }
};
