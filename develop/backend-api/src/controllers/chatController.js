const axios = require('axios');
const supabase = require('../config/db');

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';
const AI_TIMEOUT = parseInt(process.env.AI_REQUEST_TIMEOUT) || 30000;

// @route   POST /api/v1/chat
// @desc    AI 채팅 메시지 전송 및 FastAPI 중계 (DataFormat_3_ai)
//          현재 운동 플랜 + 식단 플랜을 항상 함께 전송하여 AI가 수정 요청을 처리할 수 있도록 함
// @access  Public (프로토타입 — 인증 미들웨어 없음)
exports.sendMessage = async (req, res) => {
    try {
        const { user_id, message, is_first_message } = req.body;

        if (!user_id) {
            return res.status(400).json({ error: 'user_id가 필요합니다.' });
        }
        if (!message) {
            return res.status(400).json({ error: '메시지를 입력해주세요.' });
        }

        const today = new Date().toISOString().split('T')[0];

        // 1. 첫 메시지일 때만 유저 프로필 조회 (이후는 AI 서버가 보유)
        let userProfile = undefined;
        if (is_first_message) {
            const { data: profile } = await supabase
                .from('user_health_profiles')
                .select('*')
                .eq('user_id', user_id)
                .single();

            if (profile) {
                userProfile = {
                    gender: profile.gender,
                    age: profile.age,
                    height: profile.height,
                    weight: profile.weight,
                    bmi: profile.bmi,
                    goal: profile.goal,
                    activity_level: profile.activity_level,
                    target_calories: profile.target_calories,
                    target_carbs: profile.target_carbs,
                    target_protein: profile.target_protein,
                    target_fat: profile.target_fat,
                    medical_history: profile.medical_history,
                    allergies: profile.allergies
                };
            }
        }

        // 2. 오늘 이후 운동 플랜 조회 (exercise_items 포함)
        const { data: exercises } = await supabase
            .from('user_exercise_plans')
            .select('*, exercise_items(*)')
            .eq('user_id', user_id)
            .gte('target_date', today)
            .order('created_at', { ascending: true });

        // 3. 오늘 이후 식단 플랜 조회
        const { data: meals } = await supabase
            .from('user_meal_plans')
            .select('*')
            .eq('user_id', user_id)
            .gte('target_date', today)
            .order('created_at', { ascending: true });

        // 4. AI 서버로 전송할 페이로드 구성
        const payload = {
            user_id,
            ...(userProfile && { user_profile: userProfile }),  // 첫 메시지일 때만 포함
            user_message: message,

            // 현재 운동 플랜 (항상 포함 — AI가 수정 요청 시 맥락 파악용)
            current_exercise_plans: (exercises || []).map(ex => ({
                exercise_id: ex.exercise_id,
                exercise_type: ex.exercise_type,
                total_calories: ex.total_calories,
                status: ex.status,
                target_date: ex.target_date,
                items: (ex.exercise_items || []).map(item => ({
                    item_id: item.item_id,
                    exercise_name: item.exercise_name,
                    calories: item.calories,
                    is_completed: item.is_completed
                }))
            })),

            // 현재 식단 플랜 (항상 포함)
            current_meal_plans: (meals || []).map(m => ({
                meal_id: m.meal_id,
                food_name: m.food_name,
                meal_type: m.meal_type,
                calories: m.calories,
                target_date: m.target_date
            }))
        };

        let aiResponseData = null;

        try {
            const response = await axios.post(`${FASTAPI_URL}/ai-chat`, payload, { timeout: AI_TIMEOUT });
            aiResponseData = response.data;
        } catch (aiError) {
            console.error('AI 서버 통신 실패:', aiError.message);
            aiResponseData = {
                status: 'fallback',
                action: 'chat_only',
                data: {
                    message: '현재 AI 서버와 통신할 수 없습니다. 잠시 후 다시 시도해주세요.'
                }
            };
        }

        // 4. AI 응답의 action에 따라 DB 업데이트 처리
        if (aiResponseData && aiResponseData.status === 'success') {
            const action = aiResponseData.action;

            // 운동 플랜 수정
            if ((action === 'modify_exercise' || action === 'modify_both')
                && aiResponseData.data?.modified_exercise_plans) {
                await applyExerciseModifications(aiResponseData.data.modified_exercise_plans, user_id, today);
            }

            // 식단 플랜 수정
            if ((action === 'modify_meal' || action === 'modify_both')
                && aiResponseData.data?.modified_meal_plans) {
                await applyMealModifications(aiResponseData.data.modified_meal_plans, user_id, today);
            }
        }

        // 5. 프론트엔드로 응답 반환
        res.json(aiResponseData);

    } catch (err) {
        console.error(err);
        res.status(500).json({ error: '서버 에러가 발생했습니다.' });
    }
};

// ──────────────────────────────────────────────
// 운동 플랜 수정 적용
// ──────────────────────────────────────────────
async function applyExerciseModifications(modifiedPlans, userId, targetDate) {
    for (const plan of modifiedPlans) {
        // 기존 플랜 수정 (exercise_id가 있는 경우)
        if (plan.exercise_id) {
            // 부모 업데이트
            await supabase
                .from('user_exercise_plans')
                .update({
                    exercise_type: plan.exercise_type,
                    total_calories: plan.total_calories
                })
                .eq('exercise_id', plan.exercise_id);

            // 자식 항목 처리
            if (plan.items) {
                for (const item of plan.items) {
                    if (item.is_new) {
                        // 새 항목 추가
                        await supabase
                            .from('exercise_items')
                            .insert({
                                exercise_id: plan.exercise_id,
                                exercise_name: item.exercise_name,
                                calories: item.calories || 0,
                                is_completed: false
                            });
                    } else if (item.item_id) {
                        // 기존 항목 수정
                        await supabase
                            .from('exercise_items')
                            .update({
                                exercise_name: item.exercise_name,
                                calories: item.calories
                            })
                            .eq('item_id', item.item_id);
                    }
                }
            }
        } else {
            // 새 플랜 생성 (exercise_id가 없는 경우)
            const { data: newPlan } = await supabase
                .from('user_exercise_plans')
                .insert({
                    user_id: userId,
                    exercise_type: plan.exercise_type,
                    total_calories: plan.total_calories || 0,
                    status: 0,
                    target_date: targetDate
                })
                .select()
                .single();

            if (newPlan && plan.items) {
                const itemsToInsert = plan.items.map(item => ({
                    exercise_id: newPlan.exercise_id,
                    exercise_name: item.exercise_name,
                    calories: item.calories || 0,
                    is_completed: false
                }));

                await supabase
                    .from('exercise_items')
                    .insert(itemsToInsert);
            }
        }
    }
}

// ──────────────────────────────────────────────
// 식단 플랜 수정 적용
// ──────────────────────────────────────────────
async function applyMealModifications(modifiedMeals, userId, targetDate) {
    for (const meal of modifiedMeals) {
        if (meal.is_new) {
            // 새 식단 추가
            await supabase
                .from('user_meal_plans')
                .insert({
                    user_id: userId,
                    food_name: meal.food_name,
                    meal_type: meal.meal_type || '기타',
                    calories: meal.calories,
                    target_date: targetDate
                });
        } else if (meal.meal_id) {
            // 기존 식단 수정
            await supabase
                .from('user_meal_plans')
                .update({
                    food_name: meal.food_name,
                    meal_type: meal.meal_type,
                    calories: meal.calories
                })
                .eq('meal_id', meal.meal_id);
        }
    }
}