const supabase = require('../config/db');
const calculator = require('../utils/calculator');

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
// @desc    건강 프로필 생성 및 수정 (Upsert) - 목표 칼로리/단탄지 자동계산 포함
// @access  Public (프로토타입)
exports.saveProfile = async (req, res) => {
  try {
    // 문진표 정보만 받음 (target_*는 백엔드에서만 계산함)
    const { 
      user_id, mbti, gender, age, height, weight, bmi, 
      goal, activity_level, medical_history, allergies
    } = req.body;
    
    if (!user_id) return res.status(400).json({ error: 'user_id가 필요합니다.' });

    let targets = {};

    // 백엔드에서 전적으로 자동 계산
    if (gender && age && height && weight) {
      const calculated = calculator.calculateTargets(gender, age, height, weight, activity_level, goal);
      if (calculated) {
        targets = calculated;
      }
    }

    const profileData = {
      user_id, mbti, gender, age, height, weight, bmi,
      goal, activity_level, medical_history, allergies, ...targets
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

// @route   PUT /api/v1/users/targets
// @desc    목표 섭취 칼로리 / 단탄지 수동 저장 (버튼 클릭 시)
// @access  Public (프로토타입)
exports.updateTargets = async (req, res) => {
  try {
    const { user_id, target_calories, target_carbs, target_protein, target_fat } = req.body;
    if (!user_id) return res.status(400).json({ error: 'user_id가 필요합니다.' });

    const { data: profile, error } = await supabase
      .from('user_health_profiles')
      .update({ target_calories, target_carbs, target_protein, target_fat })
      .eq('user_id', user_id)
      .select()
      .single();

    if (error) throw error;
    res.json({ message: '목표 수정 성공', profile });
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
      .select('*, exercise_items(*)')
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
// @desc    운동 플랜 (세션 생성 및 아이템 생성)
// @access  Public (프로토타입)
exports.addExercise = async (req, res) => {
  try {
    const { user_id, exercise_type, target_date, total_calories, items } = req.body;
    
    if (!user_id || !exercise_type) {
      return res.status(400).json({ error: 'user_id, exercise_type을 입력해주세요.' });
    }

    // 1. 부모 (user_exercise_plans) 세션 생성
    const { data: parent, error: parentErr } = await supabase
      .from('user_exercise_plans')
      .insert({
        user_id,
        exercise_type,
        total_calories: total_calories || 0,
        status: 0, // 기본값: 실패/미완
        target_date: target_date || new Date().toISOString().split('T')[0]
      })
      .select()
      .single();

    if (parentErr) throw parentErr;

    // 2. 자식 (exercise_items) 여러 개 생성
    if (items && Array.isArray(items) && items.length > 0) {
      const itemsToInsert = items.map(i => ({
        exercise_id: parent.exercise_id,
        exercise_name: i.name,
        calories: i.calories || 0,
        is_completed: false
      }));

      const { error: itemsErr } = await supabase
        .from('exercise_items')
        .insert(itemsToInsert);

      if (itemsErr) throw itemsErr;
    }

    res.status(201).json({ message: '운동 계획 생성 완료', exercise_id: parent.exercise_id });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   PUT /api/v1/users/exercises/items/:item_id
// @desc    개별 운동 항목 완료(체크) 토글 및 부모 상태(0,1,2) 자동 계산
// @access  Public (프로토타입)
exports.updateExerciseItem = async (req, res) => {
  try {
    const itemId = parseInt(req.params.item_id);
    const { is_completed } = req.body;

    // 1. 자식 (exercise_items) 상태 단건 업데이트
    const { data: updatedItem, error: itemErr } = await supabase
      .from('exercise_items')
      .update({ is_completed })
      .eq('item_id', itemId)
      .select()
      .single();

    if (itemErr) throw itemErr;

    const parentId = updatedItem.exercise_id;

    // 2. 같은 부모를 공유하는 전체 자식 항목 조회
    const { data: siblings, error: sibErr } = await supabase
      .from('exercise_items')
      .select('is_completed')
      .eq('exercise_id', parentId);

    if (sibErr) throw sibErr;

    // 3. 상태(status) 규칙에 따라 값 계산
    // 0: 전부 안함(실패/미완), 1: 성공(전부 true), 2: 부분성공(일부 true)
    const total = siblings.length;
    const completedCount = siblings.filter(s => s.is_completed).length;

    let newStatus = 0; // 초기값 (실패/미완)
    if (completedCount === total && total > 0) newStatus = 1;      // 전체 완료
    else if (completedCount > 0 && completedCount < total) newStatus = 2; // 일부 완료

    // 4. 계산된 상태값을 부모(user_exercise_plans)에 반영
    const { error: parentErr } = await supabase
      .from('user_exercise_plans')
      .update({ status: newStatus })
      .eq('exercise_id', parentId);

    if (parentErr) throw parentErr;

    res.json({ 
      message: '항목 상태 업데이트 성공', 
      item: updatedItem, 
      parent_status: newStatus 
    });
  } catch (err) {
    console.error(err);
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

