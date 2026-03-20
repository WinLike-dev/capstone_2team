const prisma = require('../config/db');

// @route   GET /api/v1/users/me
// @desc    내 기본 정보 조회
// @access  Private
exports.getMe = async (req, res) => {
  try {
    const user = await prisma.user.findUnique({
      where: { id: req.user.id },
      select: { id: true, email: true, name: true, role: true }
    });
    if (!user) return res.status(404).json({ error: '사용자를 찾을 수 없습니다.' });
    res.json(user);
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   GET /api/v1/users/profile
// @desc    내 상세 프로필(온보딩 데이터) 조회
// @access  Private
exports.getProfile = async (req, res) => {
  try {
    const profile = await prisma.userProfile.findUnique({
      where: { userId: req.user.id }
    });
    res.json(profile || {});
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   POST /api/v1/users/profile
// @desc    내 상세 프로필(온보딩) 생성 및 수정 (Upsert)
// @access  Private
exports.saveProfile = async (req, res) => {
  try {
    const { goal, activityLevel, diseases, allergies, height, weight, age, gender } = req.body;

    const profile = await prisma.userProfile.upsert({
      where: { userId: req.user.id },
      update: { goal, activityLevel, diseases, allergies, height, weight, age, gender },
      create: { 
        userId: req.user.id, 
        goal, activityLevel, diseases, allergies, height, weight, age, gender 
      }
    });
    res.json({ message: '프로필 저장 성공', profile });
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   GET /api/v1/users/dashboard
// @desc    특정 날짜의 대시보드 스탯 조회
// @access  Private
exports.getDashboard = async (req, res) => {
  try {
    const queryDate = req.query.date ? new Date(req.query.date) : new Date();
    
    const record = await prisma.dailyRecord.findUnique({
      where: { userId_date: { userId: req.user.id, date: queryDate } }
    });
    res.json(record || { steps: 0, calories: 0, water: 0, sleep: null });
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   POST /api/v1/users/dashboard
// @desc    특정 날짜의 대시보드 스탯 저장/업데이트
// @access  Private
exports.saveDashboard = async (req, res) => {
  try {
    const { date, steps, calories, sleep, water } = req.body;
    const targetDate = date ? new Date(date) : new Date();

    const record = await prisma.dailyRecord.upsert({
      where: { userId_date: { userId: req.user.id, date: targetDate } },
      update: { steps, calories, sleep, water },
      create: { userId: req.user.id, date: targetDate, steps, calories, sleep, water }
    });
    res.json({ message: '대시보드 저장 성공', record });
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   GET /api/v1/users/todos
// @desc    특정 날짜의 할 일 목록 조회
// @access  Private
exports.getTodos = async (req, res) => {
  try {
    const targetDate = req.query.date ? new Date(req.query.date) : new Date();
    const todos = await prisma.todo.findMany({
      where: { userId: req.user.id, date: targetDate },
      orderBy: { createdAt: 'asc' }
    });
    res.json(todos);
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   POST /api/v1/users/todos
// @desc    새로운 할 일 생성
// @access  Private
exports.addTodo = async (req, res) => {
  try {
    const { date, content } = req.body;
    const targetDate = date ? new Date(date) : new Date();
    
    if (!content) return res.status(400).json({ error: '내용을 입력해주세요.' });

    const todo = await prisma.todo.create({
      data: { userId: req.user.id, date: targetDate, content }
    });
    res.status(201).json(todo);
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   PUT /api/v1/users/todos/:id
// @desc    할 일 상태 변경 (완료 처리 등)
// @access  Private
exports.updateTodo = async (req, res) => {
  try {
    const todoId = parseInt(req.params.id);
    const { isCompleted } = req.body;

    const todo = await prisma.todo.update({
      where: { id: todoId },
      data: { isCompleted }
    });
    res.json(todo);
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   DELETE /api/v1/users/todos/:id
// @desc    할 일 삭제
// @access  Private
exports.deleteTodo = async (req, res) => {
  try {
    const todoId = parseInt(req.params.id);
    await prisma.todo.delete({ where: { id: todoId } });
    res.json({ message: '삭제 완료' });
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};
