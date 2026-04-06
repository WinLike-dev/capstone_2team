const supabase = require('../config/db');
const aiEventService = require('../services/aiEventService');

// @route   GET /api/v1/users/profile
// @desc    건강 프로필 조회
// @access  Public (프로토타입)
exports.getProfile = async (req, res) => {
  try {
    const userId = req.user.user_id;

    const { data: profile, error } = await supabase
      .from('user_health_profiles')
      .select('*, users(nickname)')
      .eq('user_id', userId)
      .single();

    if (profile && profile.users) {
      profile.nickname = profile.users.nickname;
      delete profile.users;
    }

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
    const userId = req.user.user_id;
    // 범용 정보만 받음 (목표 칼로리는 사용하지 않음)
    const {
      mbti, gender, age, height, weight,
      goal, activity_level, medical_history, allergies
    } = req.body;

    let calculatedBmi = null;

    // BMI 자동 계산
    if (height && weight) {
      const heightInMeters = height / 100;
      calculatedBmi = parseFloat((weight / (heightInMeters * heightInMeters)).toFixed(1));
    }

    const profileData = {
      user_id: userId, mbti, gender, age, height, weight, bmi: calculatedBmi,
      goal, activity_level, medical_history, allergies
    };

    const { data: profile, error } = await supabase
      .from('user_health_profiles')
      .upsert(profileData, { onConflict: 'user_id' })
      .select()
      .single();

    if (error) throw error;

    // AI 서버에 프로필 변경 이벤트 push (fire-and-forget)
    const changedFields = Object.keys(profileData).filter(k => k !== 'user_id');
    aiEventService.notifyProfileUpdated(userId, changedFields);

    res.json({ message: '프로필 저장 성공', profile });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   PUT /api/v1/users/profile
// @desc    마이페이지 등에서 건강/목표 부분 수정 시 자동 재계산 업데이트
// @access  Public (프로토타입)
exports.updateProfile = async (req, res) => {
  try {
    const userId = req.user.user_id;
    // user_id는 body에서 받지 않지만, 만약 섞여 들어왔다면 제외 (updateFields 방어)
    const { user_id, ...updateFields } = req.body;

    // 만약 넘어온 데이터 중에 닉네임이 있다면 users 테이블 먼저 업데이트 수행
    if (updateFields.nickname) {
      const { error: nickErr } = await supabase
        .from('users')
        .update({ nickname: updateFields.nickname })
        .eq('user_id', userId);

      if (nickErr) throw nickErr;
      
      // user_health_profiles 테이블에는 nickname 컬럼이 없으므로 객체에서 지워줌
      delete updateFields.nickname;  
    }

    // 1. 기존 정보 조회
    const { data: existingProfile, error: fetchErr } = await supabase
      .from('user_health_profiles')
      .select('*')
      .eq('user_id', userId)
      .single();

    if (fetchErr) throw fetchErr;

    // 2. 수정값과 기존 데이터 병합
    const mergedProfile = { ...existingProfile, ...updateFields };

    // 3. 재계산 로직 수행 (BMI)

    // BMI 재계산
    let calculatedBmi = mergedProfile.bmi;
    if (mergedProfile.height && mergedProfile.weight) {
      const heightInMeters = mergedProfile.height / 100;
      calculatedBmi = parseFloat((mergedProfile.weight / (heightInMeters * heightInMeters)).toFixed(1));
    }

    // 4. 재계산(BMI) 데이터를 합쳐서 최종 업데이트
    const finalData = { ...updateFields, bmi: calculatedBmi };

    const { data: updatedProfile, error: updateErr } = await supabase
      .from('user_health_profiles')
      .update(finalData)
      .eq('user_id', userId)
      .select()
      .single();

    if (updateErr) throw updateErr;

    // AI 서버에 프로필 변경 이벤트 push (fire-and-forget)
    const changedFields = Object.keys(finalData);
    aiEventService.notifyProfileUpdated(userId, changedFields);

    res.json({ message: '프로필 업데이트 및 타겟 수치 조율 성공', profile: updatedProfile });
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

// @route   PUT /api/v1/users/meals/:id
// @desc    식단 플랜 완료 상태(is_completed) 변경
// @access  Public (프로토타입)
exports.updateMealStatus = async (req, res) => {
  try {
    const mealId = parseInt(req.params.id);
    const { is_completed } = req.body;

    const { data: updatedMeal, error } = await supabase
      .from('user_meal_plans')
      .update({ is_completed })
      .eq('meal_id', mealId)
      .select()
      .single();

    if (error) throw error;
    res.json({ message: '식단 완료 상태 업데이트 성공', meal: updatedMeal });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   POST /api/v1/users/exercises/recommend-add
// @desc    홈 추천 운동 추가 (AI 거치지 않고 직접 추가, 타입별 부모 할당)
// @access  Public (프로토타입)
exports.addRecommendedExercise = async (req, res) => {
  try {
    const userId = req.user.user_id;
    const { target_date, exercise_type, exercise_name, calories } = req.body;
    if (!target_date || !exercise_type || !exercise_name) {
      return res.status(400).json({ error: '필수 파라미터가 누락되었습니다.' });
    }

    // 1. 해당 유저의 해당 날짜, 해당 타입의 부모(user_exercise_plans)가 있는지 확인
    const { data: parentPlan, error: parentErr } = await supabase
      .from('user_exercise_plans')
      .select('*')
      .eq('user_id', userId)
      .eq('target_date', target_date)
      .eq('exercise_type', exercise_type)
      .single();

    let exerciseId;
    let finalParentPlan;

    if (parentPlan) {
      exerciseId = parentPlan.exercise_id;
      // 기존 부모 칼로리 업데이트
      const newTotal = (parentPlan.total_calories || 0) + (calories || 0);
      const { data: updatedParent } = await supabase
        .from('user_exercise_plans')
        .update({ total_calories: newTotal })
        .eq('exercise_id', exerciseId)
        .select()
        .single();
      finalParentPlan = updatedParent;
    } else {
      // 부모가 없으면 새로 생성
      const { data: newPlan, error: insertErr } = await supabase
        .from('user_exercise_plans')
        .insert({
          user_id: userId,
          exercise_type,
          total_calories: calories || 0,
          status: 0,
          target_date
        })
        .select()
        .single();

      if (insertErr) throw insertErr;
      exerciseId = newPlan.exercise_id;
      finalParentPlan = newPlan;
    }

    // 2. 자식 아이템(exercise_items) 추가
    const { data: newItem, error: itemErr } = await supabase
      .from('exercise_items')
      .insert({
        exercise_id: exerciseId,
        exercise_name,
        calories: calories || 0,
        is_completed: false
      })
      .select()
      .single();

    if (itemErr) throw itemErr;

    res.json({ message: '추천 운동이 성공적으로 추가되었습니다.', parent_plan: finalParentPlan, item: newItem });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   PUT /api/v1/users/meals/recommend-replace
// @desc    홈 추천 식단 교체 (AI 거치지 않고 해당 시간대 식단을 통째로 교체)
// @access  Public (프로토타입)
exports.replaceRecommendedMeal = async (req, res) => {
  try {
    const userId = req.user.user_id;
    const { target_date, meal_type, food_name, calories } = req.body;
    if (!target_date || !meal_type || !food_name) {
      return res.status(400).json({ error: '필수 파라미터가 누락되었습니다.' });
    }

    // 1. 해당 시간대 식단이 이미 있는지 조회
    const { data: existingMeal } = await supabase
      .from('user_meal_plans')
      .select('meal_id')
      .eq('user_id', userId)
      .eq('target_date', target_date)
      .eq('meal_type', meal_type)
      .single();

    let resultMeal;

    if (existingMeal) {
      // 있으면 덮어쓰기(UPDATE)
      const { data: updatedMeal, error: updateErr } = await supabase
        .from('user_meal_plans')
        .update({
          food_name,
          calories: calories || 0
        })
        .eq('meal_id', existingMeal.meal_id)
        .select()
        .single();

      if (updateErr) throw updateErr;
      resultMeal = updatedMeal;
    } else {
      // 없으면 새로 생성(INSERT)
      const { data: newMeal, error: insertErr } = await supabase
        .from('user_meal_plans')
        .insert({
          user_id: userId,
          target_date,
          meal_type,
          food_name,
          calories: calories || 0
        })
        .select()
        .single();

      if (insertErr) throw insertErr;
      resultMeal = newMeal;
    }

    res.json({ message: '추천 식단으로 교체되었습니다.', meal: resultMeal });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

// @route   GET /api/v1/users/calendar
// @desc    특정 기간(start_date ~ end_date)의 운동 및 식단 정보 조회 (달력용)
// @access  Public (프로토타입)
exports.getCalendar = async (req, res) => {
  try {
    const userId = req.user.user_id;
    const startDate = req.query.start_date;
    const endDate = req.query.end_date;

    if (!startDate || !endDate) {
      return res.status(400).json({ error: 'start_date, end_date 파라미터가 모두 필요합니다.' });
    }

    // 1. 해당 기간의 운동 데이터 조회 (자식 아이템 포함)
    const { data: exercises, error: exErr } = await supabase
      .from('user_exercise_plans')
      .select('*, exercise_items(*)')
      .eq('user_id', userId)
      .gte('target_date', startDate)
      .lte('target_date', endDate)
      .order('created_at', { ascending: true });

    if (exErr) throw exErr;

    // 2. 해당 기간의 식단 데이터 조회
    const { data: meals, error: mealErr } = await supabase
      .from('user_meal_plans')
      .select('*')
      .eq('user_id', userId)
      .gte('target_date', startDate)
      .lte('target_date', endDate)
      .order('created_at', { ascending: true });

    if (mealErr) throw mealErr;

    // 3. 날짜별로 데이터 그룹화 (Grouping by target_date)
    const grouped = {};

    if (exercises) {
      exercises.forEach(ex => {
        if (!grouped[ex.target_date]) grouped[ex.target_date] = { exercises: [], meals: [] };
        grouped[ex.target_date].exercises.push(ex);
      });
    }

    if (meals) {
      meals.forEach(meal => {
        if (!grouped[meal.target_date]) grouped[meal.target_date] = { exercises: [], meals: [] };
        grouped[meal.target_date].meals.push(meal);
      });
    }

    res.json(grouped);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: '서버 에러가 발생했습니다.' });
  }
};

