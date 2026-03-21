const supabase = require('../config/db');

// @route   GET /api/v1/users/me
// @desc    내 기본 정보 조회
// @access  Private
exports.getMe = async (req, res) => {
  try {
    const { data: user, error } = await supabase
      .from('users')
      .select('id, email, name, role')
      .eq('id', req.user.id)
      .single();

    if (error || !user) return res.status(404).json({ error: '사용자를 찾을 수 없습니다.' });
    res.json(user);
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   GET /api/v1/users/profile
// @desc    내 상세 프로필(건강 정보) 조회
// @access  Private
exports.getProfile = async (req, res) => {
  try {
    const { data: profile, error } = await supabase
      .from('user_health_profiles')
      .select('*')
      .eq('user_id', req.user.id)
      .single();

    res.json(profile || {});
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   POST /api/v1/users/profile
// @desc    내 상세 프로필(건강 정보) 생성 및 수정 (Upsert)
// @access  Private
exports.saveProfile = async (req, res) => {
  try {
    const { mbti, gender, age, height, weight, bmi, goal, activity_level, medical_history, allergies, user_instruction } = req.body;

    const profileData = {
      user_id: req.user.id,
      mbti, gender, age, height, weight, bmi,
      goal, activity_level, medical_history, allergies, user_instruction
    };

    const { data: profile, error } = await supabase
      .from('user_health_profiles')
      .upsert(profileData, { onConflict: 'user_id' })
      .select()
      .single();

    if (error) throw error;
    res.json({ message: '프로필 저장 성공', profile });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   GET /api/v1/users/exercises
// @desc    특정 날짜의 운동 플랜 조회
// @access  Private
exports.getExercises = async (req, res) => {
  try {
    const targetDate = req.query.date || new Date().toISOString().split('T')[0];

    const { data: exercises, error } = await supabase
      .from('user_exercise_plans')
      .select('*')
      .eq('user_id', req.user.id)
      .eq('target_date', targetDate)
      .order('created_at', { ascending: true });

    if (error) throw error;
    res.json(exercises || []);
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   POST /api/v1/users/exercises
// @desc    운동 플랜 추가 (추천 확정)
// @access  Private
exports.addExercise = async (req, res) => {
  try {
    const { exercise_name, sets_reps, burn_calories, target_date } = req.body;

    if (!exercise_name || burn_calories == null) {
      return res.status(400).json({ error: '운동 이름과 소모 칼로리를 입력해주세요.' });
    }

    const { data: exercise, error } = await supabase
      .from('user_exercise_plans')
      .insert({
        user_id: req.user.id,
        exercise_name,
        sets_reps,
        burn_calories,
        target_date: target_date || new Date().toISOString().split('T')[0]
      })
      .select()
      .single();

    if (error) throw error;
    res.status(201).json(exercise);
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   PUT /api/v1/users/exercises/:id
// @desc    운동 플랜 완료 상태 변경
// @access  Private
exports.updateExercise = async (req, res) => {
  try {
    const exerciseId = parseInt(req.params.id);
    const { is_completed } = req.body;

    const { data: exercise, error } = await supabase
      .from('user_exercise_plans')
      .update({ is_completed })
      .eq('exercise_id', exerciseId)
      .eq('user_id', req.user.id)
      .select()
      .single();

    if (error) throw error;
    res.json(exercise);
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   DELETE /api/v1/users/exercises/:id
// @desc    운동 플랜 삭제
// @access  Private
exports.deleteExercise = async (req, res) => {
  try {
    const exerciseId = parseInt(req.params.id);

    const { error } = await supabase
      .from('user_exercise_plans')
      .delete()
      .eq('exercise_id', exerciseId)
      .eq('user_id', req.user.id);

    if (error) throw error;
    res.json({ message: '삭제 완료' });
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   GET /api/v1/users/meals
// @desc    특정 날짜의 식단 플랜 조회
// @access  Private
exports.getMeals = async (req, res) => {
  try {
    const targetDate = req.query.date || new Date().toISOString().split('T')[0];

    const { data: meals, error } = await supabase
      .from('user_meal_plans')
      .select('*')
      .eq('user_id', req.user.id)
      .eq('target_date', targetDate)
      .order('created_at', { ascending: true });

    if (error) throw error;
    res.json(meals || []);
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   POST /api/v1/users/meals
// @desc    식단 플랜 추가 (추천 확정)
// @access  Private
exports.addMeal = async (req, res) => {
  try {
    const { food_name, meal_type, calories, target_date } = req.body;

    if (!food_name || !meal_type || calories == null) {
      return res.status(400).json({ error: '음식 이름, 식사 타입, 칼로리를 입력해주세요.' });
    }

    const { data: meal, error } = await supabase
      .from('user_meal_plans')
      .insert({
        user_id: req.user.id,
        food_name,
        meal_type,
        calories,
        target_date: target_date || new Date().toISOString().split('T')[0]
      })
      .select()
      .single();

    if (error) throw error;
    res.status(201).json(meal);
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   DELETE /api/v1/users/meals/:id
// @desc    식단 플랜 삭제
// @access  Private
exports.deleteMeal = async (req, res) => {
  try {
    const mealId = parseInt(req.params.id);

    const { error } = await supabase
      .from('user_meal_plans')
      .delete()
      .eq('meal_id', mealId)
      .eq('user_id', req.user.id);

    if (error) throw error;
    res.json({ message: '삭제 완료' });
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};
