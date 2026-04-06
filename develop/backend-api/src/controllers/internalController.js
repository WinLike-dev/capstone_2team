const supabase = require('../config/db');
const logger = require('../utils/logger');

// ──────────────────────────────────────────────
// 3.1 프로필 조회
// GET /api/user/profile/:user_id
// 용도: 세션 첫 턴, profile-updated 이벤트 이후 refresh
// ──────────────────────────────────────────────
exports.getProfile = async (req, res) => {
    try {
        const { user_id } = req.params;

        const { data: profile, error } = await supabase
            .from('user_health_profiles')
            .select('*')
            .eq('user_id', user_id)
            .single();

        if (error || !profile) {
            return res.status(404).json({ error: '해당 사용자의 프로필을 찾을 수 없습니다.' });
        }

        // was_api_contract.md 3.1 기준 응답 형식
        // FastAPI는 정의되지 않은 extra field를 무시하므로 전부 내려줘도 안전
        const response = {
            user_id: profile.user_id,
            weight: profile.weight,
            height: profile.height,
            age: profile.age,
            gender: profile.gender,
            diet_type: profile.diet_type || null,
            allergies: profile.allergies || [],
            injury_history: profile.injury_history || [],
            goal: profile.goal,
            activity_level: profile.activity_level,
            selected_ai_persona: profile.selected_ai_persona || null,
            // 기존 필드도 함께 내려줌 (extra field — AI가 무시해도 무방)
            bmi: profile.bmi,
            medical_history: profile.medical_history
        };

        res.json(response);
    } catch (err) {
        logger.error('Internal getProfile 에러:', err);
        res.status(500).json({ error: '서버 에러가 발생했습니다.' });
    }
};

// ──────────────────────────────────────────────
// 3.2 오늘 플랜 조회
// GET /api/plan/today/:user_id
// 용도: 세션 첫 턴에서 오늘 체크 대상과 컨텍스트 확보
// ──────────────────────────────────────────────
exports.getTodayPlan = async (req, res) => {
    try {
        const { user_id } = req.params;
        const today = new Date().toISOString().split('T')[0];

        // 오늘 운동 플랜 + 자식 아이템 조회
        const { data: exercises, error: exErr } = await supabase
            .from('user_exercise_plans')
            .select('*, exercise_items(*)')
            .eq('user_id', user_id)
            .eq('target_date', today)
            .order('created_at', { ascending: true });

        if (exErr) throw exErr;

        // 오늘 식단 플랜 조회
        const { data: meals, error: mlErr } = await supabase
            .from('user_meal_plans')
            .select('*')
            .eq('user_id', user_id)
            .eq('target_date', today)
            .order('created_at', { ascending: true });

        if (mlErr) throw mlErr;

        // was_api_contract.md 3.2 기준 응답 형식으로 변환
        // 운동 아이템을 플랫하게 펼침
        const planItems = [];

        if (exercises) {
            exercises.forEach(ex => {
                if (ex.exercise_items && ex.exercise_items.length > 0) {
                    ex.exercise_items.forEach(item => {
                        planItems.push({
                            id: `exercise-item-${item.item_id}`,
                            type: 'exercise',
                            name: ex.exercise_type || '운동',
                            detail: item.exercise_name,
                            day: getDayOfWeek(today),
                            completed: item.is_completed || false
                        });
                    });
                } else {
                    planItems.push({
                        id: `exercise-${ex.exercise_id}`,
                        type: 'exercise',
                        name: ex.exercise_type || '운동',
                        detail: `총 ${ex.total_calories || 0}kcal`,
                        day: getDayOfWeek(today),
                        completed: ex.status === 1
                    });
                }
            });
        }

        if (meals) {
            meals.forEach(meal => {
                planItems.push({
                    id: `meal-${meal.meal_id}`,
                    type: 'meal',
                    name: meal.meal_type || '식사',
                    detail: `${meal.food_name} (${meal.calories || 0}kcal)`,
                    day: getDayOfWeek(today),
                    completed: meal.is_completed || false
                });
            });
        }

        res.json(planItems);
    } catch (err) {
        logger.error('Internal getTodayPlan 에러:', err);
        res.status(500).json({ error: '서버 에러가 발생했습니다.' });
    }
};

// ──────────────────────────────────────────────
// 3.3 프로필 수정
// PUT /api/user/profile/:user_id
// 용도: 기록/프로필 수정 intent에서 확정된 변경 반영
// 규칙: partial update만 보냄, 정의된 필드만 허용
// ──────────────────────────────────────────────
exports.updateProfile = async (req, res) => {
    try {
        const { user_id } = req.params;
        const updateFields = req.body;

        // 허용된 필드만 필터링 (DataFormat_3_v2 3.5 기준 mbti 포함)
        const allowedFields = [
            'weight', 'height', 'age', 'gender', 'diet_type',
            'allergies', 'injury_history', 'goal', 'activity_level',
            'selected_ai_persona', 'medical_history', 'bmi', 'mbti'
        ];

        const filteredUpdate = {};
        for (const key of allowedFields) {
            if (updateFields[key] !== undefined) {
                filteredUpdate[key] = updateFields[key];
            }
        }

        if (Object.keys(filteredUpdate).length === 0) {
            return res.status(400).json({ error: '수정할 필드가 없습니다.' });
        }

        // BMI 자동 재계산 (weight 또는 height가 변경된 경우)
        if (filteredUpdate.weight || filteredUpdate.height) {
            // 기존 프로필에서 나머지 값 가져오기
            const { data: existing } = await supabase
                .from('user_health_profiles')
                .select('weight, height')
                .eq('user_id', user_id)
                .single();

            if (existing) {
                const w = filteredUpdate.weight || existing.weight;
                const h = filteredUpdate.height || existing.height;
                if (w && h) {
                    const hm = h / 100;
                    filteredUpdate.bmi = parseFloat((w / (hm * hm)).toFixed(1));
                }
            }
        }

        const { data: updated, error } = await supabase
            .from('user_health_profiles')
            .update(filteredUpdate)
            .eq('user_id', user_id)
            .select()
            .single();

        if (error) throw error;

        res.json({ status: 'success', updated_fields: Object.keys(filteredUpdate) });
    } catch (err) {
        logger.error('Internal updateProfile 에러:', err);
        res.status(500).json({ error: '서버 에러가 발생했습니다.' });
    }
};

// ──────────────────────────────────────────────
// 3.4 플랜 생성
// POST /api/plan/create/:user_id
// 용도: 승인된 새 계획 저장
// ──────────────────────────────────────────────
exports.createPlan = async (req, res) => {
    try {
        const { user_id } = req.params;
        const { plan_type, items } = req.body;

        if (!plan_type || !items || !Array.isArray(items)) {
            return res.status(400).json({ error: 'plan_type과 items 배열이 필요합니다.' });
        }

        const createdItems = [];

        if (plan_type === 'workout') {
            // 운동 플랜 생성
            for (const item of items) {
                const targetDate = dayToDate(item.day);

                // 부모(exercise_plan) 생성
                const { data: plan, error: planErr } = await supabase
                    .from('user_exercise_plans')
                    .insert({
                        user_id,
                        exercise_type: item.name,
                        total_calories: 0,
                        status: 0,
                        target_date: targetDate
                    })
                    .select()
                    .single();

                if (planErr) throw planErr;

                // 자식(exercise_item) 생성
                if (item.detail) {
                    const { data: exerciseItem, error: itemErr } = await supabase
                        .from('exercise_items')
                        .insert({
                            exercise_id: plan.exercise_id,
                            exercise_name: item.detail,
                            calories: 0,
                            is_completed: false
                        })
                        .select()
                        .single();

                    if (itemErr) throw itemErr;
                    createdItems.push({ plan, item: exerciseItem });
                } else {
                    createdItems.push({ plan });
                }
            }
        } else if (plan_type === 'diet' || plan_type === 'meal') {
            // 식단 플랜 생성
            for (const item of items) {
                const targetDate = dayToDate(item.day);

                const { data: meal, error: mealErr } = await supabase
                    .from('user_meal_plans')
                    .insert({
                        user_id,
                        food_name: item.detail || item.name,
                        meal_type: item.name,
                        calories: 0,
                        target_date: targetDate
                    })
                    .select()
                    .single();

                if (mealErr) throw mealErr;
                createdItems.push(meal);
            }
        } else {
            return res.status(400).json({ error: `지원하지 않는 plan_type: ${plan_type}` });
        }

        res.status(201).json({
            status: 'success',
            plan_type,
            created_count: createdItems.length,
            items: createdItems
        });
    } catch (err) {
        logger.error('Internal createPlan 에러:', err);
        res.status(500).json({ error: '서버 에러가 발생했습니다.' });
    }
};

// ──────────────────────────────────────────────
// 3.5 플랜 수정
// PUT /api/plan/update/:user_id
// 용도: 승인된 수정안 저장 (형식은 create와 동일)
// ──────────────────────────────────────────────
exports.updatePlan = async (req, res) => {
    try {
        const { user_id } = req.params;
        const { plan_type, items } = req.body;

        if (!plan_type || !items || !Array.isArray(items)) {
            return res.status(400).json({ error: 'plan_type과 items 배열이 필요합니다.' });
        }

        if (plan_type === 'workout') {
            // 기존 운동 플랜에서 해당 날짜 항목을 찾아 수정하거나, 없으면 새로 생성
            for (const item of items) {
                const targetDate = dayToDate(item.day);

                // 해당 날짜 + 타입으로 기존 플랜 검색
                const { data: existingPlan } = await supabase
                    .from('user_exercise_plans')
                    .select('exercise_id')
                    .eq('user_id', user_id)
                    .eq('target_date', targetDate)
                    .eq('exercise_type', item.name)
                    .single();

                if (existingPlan) {
                    // 기존 플랜 수정
                    await supabase
                        .from('user_exercise_plans')
                        .update({ exercise_type: item.name })
                        .eq('exercise_id', existingPlan.exercise_id);

                    // 기존 자식 삭제 후 재생성
                    await supabase
                        .from('exercise_items')
                        .delete()
                        .eq('exercise_id', existingPlan.exercise_id);

                    if (item.detail) {
                        await supabase
                            .from('exercise_items')
                            .insert({
                                exercise_id: existingPlan.exercise_id,
                                exercise_name: item.detail,
                                calories: 0,
                                is_completed: false
                            });
                    }
                } else {
                    // 없으면 새로 생성 (create와 동일)
                    const { data: plan } = await supabase
                        .from('user_exercise_plans')
                        .insert({
                            user_id,
                            exercise_type: item.name,
                            total_calories: 0,
                            status: 0,
                            target_date: targetDate
                        })
                        .select()
                        .single();

                    if (plan && item.detail) {
                        await supabase
                            .from('exercise_items')
                            .insert({
                                exercise_id: plan.exercise_id,
                                exercise_name: item.detail,
                                calories: 0,
                                is_completed: false
                            });
                    }
                }
            }
        } else if (plan_type === 'diet' || plan_type === 'meal') {
            for (const item of items) {
                const targetDate = dayToDate(item.day);

                const { data: existingMeal } = await supabase
                    .from('user_meal_plans')
                    .select('meal_id')
                    .eq('user_id', user_id)
                    .eq('target_date', targetDate)
                    .eq('meal_type', item.name)
                    .single();

                if (existingMeal) {
                    await supabase
                        .from('user_meal_plans')
                        .update({
                            food_name: item.detail || item.name,
                            meal_type: item.name
                        })
                        .eq('meal_id', existingMeal.meal_id);
                } else {
                    await supabase
                        .from('user_meal_plans')
                        .insert({
                            user_id,
                            food_name: item.detail || item.name,
                            meal_type: item.name,
                            calories: 0,
                            target_date: targetDate
                        });
                }
            }
        } else {
            return res.status(400).json({ error: `지원하지 않는 plan_type: ${plan_type}` });
        }

        res.json({ status: 'success', plan_type, updated_count: items.length });
    } catch (err) {
        logger.error('Internal updatePlan 에러:', err);
        res.status(500).json({ error: '서버 에러가 발생했습니다.' });
    }
};

// ──────────────────────────────────────────────
// 3.6 플랜 체크 완료
// PUT /api/plan/check/:user_id
// 용도: 오늘 플랜 항목 완료 처리
// ──────────────────────────────────────────────
exports.checkPlan = async (req, res) => {
    try {
        const { user_id } = req.params;
        const { item_id } = req.body;

        if (!item_id) {
            return res.status(400).json({ error: 'item_id가 필요합니다.' });
        }

        // item_id 형식에 따라 운동/식단 구분
        // id 형식: "exercise-item-{id}" 또는 "meal-{id}" 또는 "exercise-{id}"
        if (item_id.startsWith('exercise-item-')) {
            const actualId = parseInt(item_id.replace('exercise-item-', ''));

            // 자식 아이템 완료 처리
            const { data: updatedItem, error: itemErr } = await supabase
                .from('exercise_items')
                .update({ is_completed: true })
                .eq('item_id', actualId)
                .select()
                .single();

            if (itemErr) throw itemErr;

            // 부모 상태 자동 계산 (0: 미완, 1: 전체완료, 2: 부분완료)
            const parentId = updatedItem.exercise_id;
            const { data: siblings } = await supabase
                .from('exercise_items')
                .select('is_completed')
                .eq('exercise_id', parentId);

            const total = siblings.length;
            const completedCount = siblings.filter(s => s.is_completed).length;
            let newStatus = 0;
            if (completedCount === total && total > 0) newStatus = 1;
            else if (completedCount > 0 && completedCount < total) newStatus = 2;

            await supabase
                .from('user_exercise_plans')
                .update({ status: newStatus })
                .eq('exercise_id', parentId);

            res.json({ status: 'success', item_id, checked: true, parent_status: newStatus });

        } else if (item_id.startsWith('meal-')) {
            const actualId = parseInt(item_id.replace('meal-', ''));

            const { error: mealErr } = await supabase
                .from('user_meal_plans')
                .update({ is_completed: true })
                .eq('meal_id', actualId);

            if (mealErr) throw mealErr;

            res.json({ status: 'success', item_id, checked: true });

        } else if (item_id.startsWith('exercise-')) {
            // 부모 운동 플랜 자체를 완료 처리
            const actualId = parseInt(item_id.replace('exercise-', ''));

            await supabase
                .from('user_exercise_plans')
                .update({ status: 1 })
                .eq('exercise_id', actualId);

            // 자식 아이템도 모두 완료 처리
            await supabase
                .from('exercise_items')
                .update({ is_completed: true })
                .eq('exercise_id', actualId);

            res.json({ status: 'success', item_id, checked: true });

        } else {
            return res.status(400).json({ error: `인식할 수 없는 item_id 형식: ${item_id}` });
        }
    } catch (err) {
        logger.error('Internal checkPlan 에러:', err);
        res.status(500).json({ error: '서버 에러가 발생했습니다.' });
    }
};

// ──────────────────────────────────────────────
// 3.3-추가 운동 전체 플랜 조회
// GET /api/workout-plan/full/:user_id
// 용도: 수정 intent에서 기존 운동 전체 플랜을 읽음
// DataFormat_3_v2_was_fastapi.md 섹션 3.3 기준
// ──────────────────────────────────────────────
exports.getFullWorkoutPlan = async (req, res) => {
    try {
        const { user_id } = req.params;

        // 전체 운동 플랜 + 자식 아이템 조회
        const { data: exercises, error } = await supabase
            .from('user_exercise_plans')
            .select('*, exercise_items(*)')
            .eq('user_id', user_id)
            .order('target_date', { ascending: true });

        if (error) throw error;

        // DataFormat 3.3 응답 형식으로 변환
        const items = [];

        if (exercises) {
            exercises.forEach(ex => {
                if (ex.exercise_items && ex.exercise_items.length > 0) {
                    ex.exercise_items.forEach(item => {
                        items.push({
                            id: `workout-${item.item_id}`,
                            name: item.exercise_name,
                            detail: `${ex.exercise_type} / ${item.calories || 0}kcal`,
                            day: getDayOfWeek(ex.target_date),
                            completed: item.is_completed || false
                        });
                    });
                } else {
                    items.push({
                        id: `workout-plan-${ex.exercise_id}`,
                        name: ex.exercise_type,
                        detail: `총 ${ex.total_calories || 0}kcal`,
                        day: getDayOfWeek(ex.target_date),
                        completed: ex.status === 1
                    });
                }
            });
        }

        res.json({
            plan_type: 'workout',
            items
        });
    } catch (err) {
        logger.error('Internal getFullWorkoutPlan 에러:', err);
        res.status(500).json({ error: '서버 에러가 발생했습니다.' });
    }
};

// ──────────────────────────────────────────────
// 3.4-추가 식단 전체 플랜 조회
// GET /api/diet-plan/full/:user_id
// 용도: 수정 intent에서 기존 식단 전체 플랜을 읽음
// DataFormat_3_v2_was_fastapi.md 섹션 3.4 기준
// ──────────────────────────────────────────────
exports.getFullDietPlan = async (req, res) => {
    try {
        const { user_id } = req.params;

        const { data: meals, error } = await supabase
            .from('user_meal_plans')
            .select('*')
            .eq('user_id', user_id)
            .order('target_date', { ascending: true });

        if (error) throw error;

        // DataFormat 3.4 응답 형식으로 변환
        const items = (meals || []).map(meal => ({
            id: `diet-${meal.meal_id}`,
            name: meal.food_name,
            detail: `${meal.meal_type} / ${meal.target_date}`,
            day: getDayOfWeek(meal.target_date),
            completed: meal.is_completed || false
        }));

        res.json({
            plan_type: 'diet',
            items
        });
    } catch (err) {
        logger.error('Internal getFullDietPlan 에러:', err);
        res.status(500).json({ error: '서버 에러가 발생했습니다.' });
    }
};

// ──────────────────────────────────────────────
// 유틸 함수
// ──────────────────────────────────────────────

/**
 * 날짜 문자열(YYYY-MM-DD)을 요일 영문으로 변환
 */
function getDayOfWeek(dateStr) {
    const days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
    const date = new Date(dateStr + 'T00:00:00');
    return days[date.getDay()];
}

/**
 * 요일 영문(monday 등)을 이번 주 해당 날짜(YYYY-MM-DD)로 변환
 */
function dayToDate(day) {
    if (!day) return new Date().toISOString().split('T')[0]; // 없으면 오늘

    const dayMap = {
        'sunday': 0, 'monday': 1, 'tuesday': 2, 'wednesday': 3,
        'thursday': 4, 'friday': 5, 'saturday': 6
    };

    const targetDay = dayMap[day.toLowerCase()];
    if (targetDay === undefined) return new Date().toISOString().split('T')[0];

    const now = new Date();
    const currentDay = now.getDay();
    const diff = targetDay - currentDay;

    const targetDate = new Date(now);
    targetDate.setDate(now.getDate() + diff);

    return targetDate.toISOString().split('T')[0];
}
