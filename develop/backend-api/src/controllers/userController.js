const supabase = require('../config/db');

// @route   GET /api/v1/users/profile
// @desc    건강 프로필 조회
// @access  Public (프로토타입)
exports.getProfile = async (req, res) => {
  try {
    const userId = req.query.user_id;
    if (!userId) return res.status(400).json({ error: 'user_id가 필요합니다.' });

    const { data: profile, error } = await supabase
      .from('user_health_profiles')
      .select('*')
      .eq('user_id', userId)
      .single();

    res.json(profile || {});
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   POST /api/v1/users/profile
// @desc    건강 프로필 생성 및 수정 (Upsert)
// @access  Public (프로토타입)
exports.saveProfile = async (req, res) => {
  try {
    const { user_id, mbti, gender, age, height, weight, bmi, goal, activity_level, medical_history, allergies, user_instruction } = req.body;
    if (!user_id) return res.status(400).json({ error: 'user_id가 필요합니다.' });

    const profileData = {
      user_id, mbti, gender, age, height, weight, bmi,
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
// @access  Public (프로토타입)
exports.getExercises = async (req, res) => {
  try {
    const userId = req.query.user_id;
    if (!userId) return res.status(400).json({ error: 'user_id가 필요합니다.' });

    const targetDate = req.query.date || new Date().toISOString().split('T')[0];

    const { data: exercises, error } = await supabase
      .from('user_exercise_plans')
      .select('*')
      .eq('user_id', userId)
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
// @access  Public (프로토타입)
exports.addExercise = async (req, res) => {
  try {
    const { user_id, exercise_name, sets_reps, burn_calories, target_date } = req.body;
    if (!user_id || !exercise_name || burn_calories == null) {
      return res.status(400).json({ error: 'user_id, 운동 이름, 소모 칼로리를 입력해주세요.' });
    }

    const { data: exercise, error } = await supabase
      .from('user_exercise_plans')
      .insert({
        user_id,
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
// @access  Public (프로토타입)
exports.updateExercise = async (req, res) => {
  try {
    const exerciseId = parseInt(req.params.id);
    const { is_completed } = req.body;

    const { data: exercise, error } = await supabase
      .from('user_exercise_plans')
      .update({ is_completed })
      .eq('exercise_id', exerciseId)
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
// @access  Public (프로토타입)
exports.deleteExercise = async (req, res) => {
  try {
    const exerciseId = parseInt(req.params.id);

    const { error } = await supabase
      .from('user_exercise_plans')
      .delete()
      .eq('exercise_id', exerciseId);

    if (error) throw error;
    res.json({ message: '삭제 완료' });
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   GET /api/v1/users/meals
// @desc    특정 날짜의 식단 플랜 조회
// @access  Public (프로토타입)
exports.getMeals = async (req, res) => {
  try {
    const userId = req.query.user_id;
    if (!userId) return res.status(400).json({ error: 'user_id가 필요합니다.' });

    const targetDate = req.query.date || new Date().toISOString().split('T')[0];

    const { data: meals, error } = await supabase
      .from('user_meal_plans')
      .select('*')
      .eq('user_id', userId)
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
// @access  Public (프로토타입)
exports.addMeal = async (req, res) => {
  try {
    const { user_id, food_name, meal_type, calories, target_date } = req.body;
    if (!user_id || !food_name || !meal_type || calories == null) {
      return res.status(400).json({ error: 'user_id, 음식 이름, 식사 타입, 칼로리를 입력해주세요.' });
    }

    const { data: meal, error } = await supabase
      .from('user_meal_plans')
      .insert({
        user_id,
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
// @access  Public (프로토타입)
exports.deleteMeal = async (req, res) => {
  try {
    const mealId = parseInt(req.params.id);

    const { error } = await supabase
      .from('user_meal_plans')
      .delete()
      .eq('meal_id', mealId);

    if (error) throw error;
    res.json({ message: '삭제 완료' });
  } catch (err) {
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   POST /api/v1/users/confirm-recommendation
// @desc    추천 항목 확정 (좋아요) → 캘린더에 등록 (DataFormat_2)
// @access  Public (프로토타입)
exports.confirmRecommendation = async (req, res) => {
  try {
    const { user_id, item_type, item_details } = req.body;

    if (!user_id || !item_type || !item_details) {
      return res.status(400).json({ error: 'user_id, item_type, item_details가 필요합니다.' });
    }

    const { name, calories, date, time_slot } = item_details;

    if (!name || calories == null || !date) {
      return res.status(400).json({ error: 'item_details에 name, calories, date가 필요합니다.' });
    }

    let entry = null;

    if (item_type === 'exercise') {
      // 운동 추천 확정 → user_exercise_plans에 저장
      const { data, error } = await supabase
        .from('user_exercise_plans')
        .insert({
          user_id,
          exercise_name: name,
          burn_calories: calories,
          target_date: date
        })
        .select()
        .single();

      if (error) throw error;
      entry = data;

    } else if (item_type === 'meal') {
      // 식단 추천 확정 → user_meal_plans에 저장
      const { data, error } = await supabase
        .from('user_meal_plans')
        .insert({
          user_id,
          food_name: name,
          meal_type: time_slot || '기타',
          calories,
          target_date: date
        })
        .select()
        .single();

      if (error) throw error;
      entry = data;

    } else {
      return res.status(400).json({ error: 'item_type은 "exercise" 또는 "meal"이어야 합니다.' });
    }

    // DataFormat_2 응답 규격
    res.status(201).json({
      status: 'success',
      message: '성공적으로 저장되었습니다.',
      data: {
        entry_id: String(entry.exercise_id || entry.meal_id)
      }
    });

  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

