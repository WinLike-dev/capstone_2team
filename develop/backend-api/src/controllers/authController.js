const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const supabase = require('../config/db');

// @route   POST /api/v1/auth/register
// @desc    유저 회원가입
// @access  Public
exports.register = async (req, res) => {
  try {
    const { email, password, name } = req.body;

    // 1. 필수 값 확인
    if (!email || !password || !name) {
      return res.status(400).json({ error: '모든 필드를 입력해주세요.' });
    }

    // 2. 이미 존재하는 이메일인지 확인
    const { data: existingUser } = await supabase
      .from('users')
      .select('id')
      .eq('email', email)
      .single();

    if (existingUser) {
      return res.status(400).json({ error: '이미 사용 중인 이메일입니다.' });
    }

    // 3. 비밀번호 암호화 (Salt + Hash)
    const salt = await bcrypt.genSalt(10);
    const passwordHash = await bcrypt.hash(password, salt);

    // 4. DB에 유저 생성
    const { data: user, error } = await supabase
      .from('users')
      .insert({ email, password_hash: passwordHash, name })
      .select('id, email, name, role, created_at')
      .single();

    if (error) throw error;

    res.status(201).json({ message: '회원가입이 완료되었습니다.', user });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   POST /api/v1/auth/login
// @desc    유저 로그인 및 JWT 토큰 발급
// @access  Public
exports.login = async (req, res) => {
  try {
    const { email, password } = req.body;

    // 1. 필수 값 확인
    if (!email || !password) {
      return res.status(400).json({ error: '이메일과 비밀번호를 입력해주세요.' });
    }

    // 2. 유저 존재 확인
    const { data: user, error } = await supabase
      .from('users')
      .select('*')
      .eq('email', email)
      .single();

    if (error || !user) {
      return res.status(401).json({ error: '이메일 또는 비밀번호가 올바르지 않습니다.' });
    }

    // 3. 비밀번호 일치 확인
    const isMatch = await bcrypt.compare(password, user.password_hash);

    if (!isMatch) {
      return res.status(401).json({ error: '이메일 또는 비밀번호가 올바르지 않습니다.' });
    }

    // 4. JWT 페이로드 및 토큰 생성
    const payload = {
      user: {
        id: user.id,
        role: user.role
      }
    };

    // JWT_SECRET 환경변수를 사용하여 서명 (만료시간: 24시간)
    jwt.sign(
      payload,
      process.env.JWT_SECRET,
      { expiresIn: '24h' },
      (err, token) => {
        if (err) throw err;
        res.json({ 
          message: '로그인 성공',
          token,
          user: {
            id: user.id,
            email: user.email,
            name: user.name,
            role: user.role
          } 
        });
      }
    );
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   POST /api/v1/auth/logout
// @desc    유저 로그아웃 (토큰 기반이므로 클라이언트측 삭제 권장)
// @access  Public
exports.logout = (req, res) => {
  // JWT는 상태를 저장하지 않으므로, 서버에서 강제 폐기하려면 Redis 같은 세션 저장소가 필요함.
  // 현재 구조에서는 프론트엔드에서 로컬스토리지/쿠키의 토큰을 지우는 것으로 처리.
  res.json({ message: '로그아웃 되었습니다. 클라이언트에서 토큰을 삭제해주세요.' });
};
