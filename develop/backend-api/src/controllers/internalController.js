const supabase = require('../config/db');
const logger = require('../utils/logger');
const { formatKstDate, normalizeIsoDate } = require('../utils/kst');
const {
  parseStoredArray,
  serializeArrayField,
  toOptionalNumber,
  toOptionalString,
} = require('../utils/profileFields');
const {
  buildProfileRowForUpsert,
  ensureUserHealthProfile,
  ensureUserHealthProfileRow,
} = require('../services/profileService');
const { loadExercisePlansWithItems } = require('../services/exercisePlanReadService');
const planMutationService = require('../services/planMutationService');

function normalizePlanType(value) {
  const text = String(value || '').trim().toLowerCase();
  if (text === 'diet' || text === 'meal') return 'diet';
  if (text === 'workout' || text === 'exercise') return 'workout';
  return null;
}

function dedupeDates(items = []) {
  return [...new Set(items.map((item) => item.day))];
}

function normalizeExerciseList(rawExerciseList, detailFallback) {
  if (Array.isArray(rawExerciseList) && rawExerciseList.length > 0) {
    return rawExerciseList
      .map((item) => ({
        exercise_name: toOptionalString(
          item.exercise_name || item.name || item.title || item.exercise
        ),
        sets: toOptionalNumber(item.sets || item.set || item.count),
        duration_minutes: toOptionalNumber(
          item.duration_minutes || item.duration || item.minutes
        ),
        calories: toOptionalNumber(item.calories) || 0,
      }))
      .filter((item) => item.exercise_name);
  }

  const detailText = toOptionalString(detailFallback);
  if (!detailText) {
    return [];
  }

  return [
    {
      exercise_name: detailText,
      sets: 3,
      duration_minutes: null,
      calories: 0,
    },
  ];
}

function normalizeIncomingPlanItems(planType, items) {
  if (!Array.isArray(items)) {
    return [];
  }

  return items
    .map((item) => {
      const day = normalizeIsoDate(item.day || item.date);
      const name = toOptionalString(item.name);
      const detail = toOptionalString(item.detail);

      if (!day || !name) {
        return null;
      }

      return {
        id: toOptionalString(item.id),
        day,
        name,
        detail,
        ex_list: planType === 'workout'
          ? normalizeExerciseList(item.ex_list, detail)
          : [],
      };
    })
    .filter(Boolean);
}

function parsePlanCheckId(itemId) {
  if (itemId.startsWith('exercise-item-')) {
    return {
      kind: 'exercise-item',
      numericId: Number(itemId.replace('exercise-item-', '')),
    };
  }

  if (itemId.startsWith('exercise-')) {
    return {
      kind: 'exercise',
      numericId: Number(itemId.replace('exercise-', '')),
    };
  }

  if (itemId.startsWith('meal-')) {
    return {
      kind: 'meal',
      numericId: Number(itemId.replace('meal-', '')),
    };
  }

  return null;
}

function calculateBmi(weight, height) {
  if (!weight || !height) return null;
  const heightInMeters = height / 100;
  if (!heightInMeters) return null;
  return Number((weight / (heightInMeters * heightInMeters)).toFixed(1));
}

async function getOwnedExercisePlan(userId, exerciseId) {
  const { data, error } = await supabase
    .from('user_exercise_plans')
    .select('exercise_id')
    .eq('user_id', userId)
    .eq('exercise_id', exerciseId)
    .maybeSingle();

  if (error) throw error;
  return data;
}

async function getOwnedExerciseItem(userId, itemId) {
  const { data: item, error } = await supabase
    .from('exercise_items')
    .select('item_id, exercise_id')
    .eq('item_id', itemId)
    .maybeSingle();

  if (error) throw error;
  if (!item) return null;

  const ownedPlan = await getOwnedExercisePlan(userId, item.exercise_id);
  if (!ownedPlan) return null;

  return item;
}

async function rebuildParentExerciseStatus(exerciseId) {
  const { data: siblings, error } = await supabase
    .from('exercise_items')
    .select('is_completed')
    .eq('exercise_id', exerciseId);

  if (error) throw error;

  const total = siblings.length;
  const completedCount = siblings.filter((item) => item.is_completed).length;

  let nextStatus = 0;
  if (total > 0 && completedCount === total) nextStatus = 1;
  else if (completedCount > 0) nextStatus = 2;

  const { error: parentError } = await supabase
    .from('user_exercise_plans')
    .update({ status: nextStatus })
    .eq('exercise_id', exerciseId);

  if (parentError) throw parentError;
  return nextStatus;
}

async function createWorkoutPlans(userId, normalizedItems) {
  const createdItems = [];

  for (const item of normalizedItems) {
    const totalCalories = item.ex_list.reduce(
      (sum, exercise) => sum + Number(exercise.calories || 0),
      0
    );
    const { data: plan, error: planError } = await supabase
      .from('user_exercise_plans')
      .insert({
        user_id: userId,
        exercise_type: item.name,
        total_calories: totalCalories,
        status: 0,
        target_date: item.day,
      })
      .select('*')
      .single();

    if (planError) throw planError;

    let exerciseItems = [];
    if (item.ex_list.length > 0) {
      const insertRows = item.ex_list.map((exercise) => ({
        exercise_id: plan.exercise_id,
        exercise_name: exercise.exercise_name,
        calories: Number(exercise.calories || 0),
        target_sets: exercise.sets ?? null,
        duration_minutes: exercise.duration_minutes ?? null,
        is_completed: false,
      }));

      const { data: insertedItems, error: itemError } = await supabase
        .from('exercise_items')
        .insert(insertRows)
        .select('*');

      if (itemError) throw itemError;
      exerciseItems = insertedItems || [];
    }

    createdItems.push({
      ...item,
      plan,
      exercise_items: exerciseItems,
    });
  }

  return createdItems;
}

async function createDietPlans(userId, normalizedItems) {
  const createdItems = [];

  for (const item of normalizedItems) {
    const { data: meal, error } = await supabase
      .from('user_meal_plans')
      .insert({
        user_id: userId,
        food_name: item.detail || item.name,
        meal_type: item.name,
        target_date: item.day,
        is_completed: false,
        calories: 0,
      })
      .select('*')
      .single();

    if (error && !String(error.message || '').includes('calories')) {
      throw error;
    }

    if (error) {
      const retry = await supabase
        .from('user_meal_plans')
        .insert({
          user_id: userId,
          food_name: item.detail || item.name,
          meal_type: item.name,
          target_date: item.day,
          is_completed: false,
        })
        .select('*')
        .single();

      if (retry.error) throw retry.error;
      createdItems.push(retry.data);
      continue;
    }

    createdItems.push(meal);
  }

  return createdItems;
}

async function deleteWorkoutPlansForDates(userId, targetDates) {
  if (targetDates.length === 0) return;

  const { data: existingPlans, error } = await supabase
    .from('user_exercise_plans')
    .select('exercise_id')
    .eq('user_id', userId)
    .in('target_date', targetDates);

  if (error) throw error;

  const exerciseIds = (existingPlans || []).map((plan) => plan.exercise_id);
  if (exerciseIds.length > 0) {
    const { error: itemError } = await supabase
      .from('exercise_items')
      .delete()
      .in('exercise_id', exerciseIds);

    if (itemError) throw itemError;
  }

  const { error: deleteError } = await supabase
    .from('user_exercise_plans')
    .delete()
    .eq('user_id', userId)
    .in('target_date', targetDates);

  if (deleteError) throw deleteError;
}

async function deleteDietPlansForDates(userId, targetDates) {
  if (targetDates.length === 0) return;

  const { error } = await supabase
    .from('user_meal_plans')
    .delete()
    .eq('user_id', userId)
    .in('target_date', targetDates);

  if (error) throw error;
}

async function loadExistingConflictDates(userId, planType, targetDates) {
  if (targetDates.length === 0) return [];

  if (planType === 'workout') {
    const { data, error } = await supabase
      .from('user_exercise_plans')
      .select('target_date')
      .eq('user_id', userId)
      .in('target_date', targetDates);

    if (error) throw error;
    return [...new Set((data || []).map((row) => row.target_date))];
  }

  const { data, error } = await supabase
    .from('user_meal_plans')
    .select('target_date')
    .eq('user_id', userId)
    .in('target_date', targetDates);

  if (error) throw error;
  return [...new Set((data || []).map((row) => row.target_date))];
}

// GET /api/user/profile/:user_id
exports.getProfile = async (req, res) => {
  try {
    const { user_id: userId } = req.params;
    const profile = await ensureUserHealthProfile(supabase, userId);
    if (!profile) {
      return res.status(404).json({ error: 'Profile not found.' });
    }

    return res.json({
      user_id: profile.user_id,
      weight: profile.weight ?? null,
      height: profile.height ?? null,
      age: profile.age ?? null,
      gender: profile.gender ?? null,
      diet_type: profile.diet_type ?? null,
      allergies: parseStoredArray(profile.allergies),
      injury_history: parseStoredArray(profile.injury_history),
      goal: profile.goal ?? null,
      activity_level: profile.activity_level ?? null,
      selected_ai_persona: profile.selected_ai_persona ?? null,
      bmi: profile.bmi ?? null,
      medical_history: parseStoredArray(profile.medical_history),
      mbti: profile.mbti ?? null,
    });
  } catch (error) {
    logger.error(`Internal getProfile error: ${error.message}`);
    return res.status(500).json({ error: 'Failed to load profile.' });
  }
};

// GET /api/plan/today/:user_id
exports.getTodayPlan = async (req, res) => {
  try {
    const { user_id: userId } = req.params;
    const today = formatKstDate();

    const exercises = await loadExercisePlansWithItems(supabase, {
      userId,
      targetDate: today,
    });

    const { data: meals, error: mealError } = await supabase
      .from('user_meal_plans')
      .select('*')
      .eq('user_id', userId)
      .eq('target_date', today)
      .order('created_at', { ascending: true });

    if (mealError) throw mealError;

    const planItems = [];

    for (const exercise of exercises || []) {
      const exerciseItems = exercise.exercise_items || [];
      if (exerciseItems.length > 0) {
        for (const item of exerciseItems) {
          planItems.push({
            id: `exercise-item-${item.item_id}`,
            type: 'exercise',
            name: exercise.exercise_type || 'exercise',
            detail: item.exercise_name,
            day: exercise.target_date,
            completed: Boolean(item.is_completed),
          });
        }
      } else {
        planItems.push({
          id: `exercise-${exercise.exercise_id}`,
          type: 'exercise',
          name: exercise.exercise_type || 'exercise',
          detail: `total ${exercise.total_calories || 0} kcal`,
          day: exercise.target_date,
          completed: exercise.status === 1,
        });
      }
    }

    for (const meal of meals || []) {
      planItems.push({
        id: `meal-${meal.meal_id}`,
        type: 'meal',
        name: meal.meal_type || 'meal',
        detail: meal.food_name,
        day: meal.target_date,
        completed: Boolean(meal.is_completed),
      });
    }

    return res.json(planItems);
  } catch (error) {
    logger.error(`Internal getTodayPlan error: ${error.message}`);
    return res.status(500).json({ error: 'Failed to load today plan.' });
  }
};

// PUT /api/user/profile/:user_id
exports.updateProfile = async (req, res) => {
  try {
    const { user_id: userId } = req.params;
    const allowedUpdates = {
      weight: toOptionalNumber(req.body.weight),
      height: toOptionalNumber(req.body.height),
      age: toOptionalNumber(req.body.age),
      gender: toOptionalString(req.body.gender),
      diet_type: req.body.diet_type !== undefined ? toOptionalString(req.body.diet_type) : undefined,
      allergies: req.body.allergies !== undefined ? serializeArrayField(req.body.allergies) : undefined,
      injury_history: req.body.injury_history !== undefined ? serializeArrayField(req.body.injury_history) : undefined,
      goal: toOptionalString(req.body.goal),
      activity_level: toOptionalString(req.body.activity_level),
      medical_history: req.body.medical_history !== undefined
        ? serializeArrayField(req.body.medical_history)
        : undefined,
      mbti: toOptionalString(req.body.mbti),
    };

    const filteredUpdate = Object.fromEntries(
      Object.entries(allowedUpdates).filter(([, value]) => value !== undefined)
    );

    if (Object.keys(filteredUpdate).length === 0) {
      return res.status(400).json({ error: 'No valid profile fields provided.' });
    }

    const existingProfile = await ensureUserHealthProfileRow(supabase, userId);
    if (!existingProfile) {
      return res.status(404).json({ error: 'User not found.' });
    }

    const profilePayload = buildProfileRowForUpsert(userId, existingProfile, filteredUpdate);
    profilePayload.bmi = calculateBmi(profilePayload.weight, profilePayload.height) ?? 0;

    const { data: updatedProfile, error } = await supabase
      .from('user_health_profiles')
      .upsert(profilePayload, { onConflict: 'user_id' })
      .select('*')
      .single();

    if (error) throw error;

    return res.json({
      status: 'success',
      updated_fields: Object.keys(filteredUpdate),
      profile: updatedProfile,
    });
  } catch (error) {
    logger.error(`Internal updateProfile error: ${error.message}`);
    return res.status(500).json({ error: 'Failed to update profile.' });
  }
};

// POST /api/plan/create/:user_id
exports.createPlan = async (req, res) => {
  try {
    const { user_id: userId } = req.params;
    const planType = normalizePlanType(req.body.plan_type);

    if (!planType) {
      return res.status(400).json({ error: 'plan_type is required.' });
    }

    const normalizedItems = normalizeIncomingPlanItems(planType, req.body.items);

    if (normalizedItems.length === 0) {
      return res.status(400).json({ error: 'plan_type and valid items are required.' });
    }

    const targetDates = dedupeDates(normalizedItems);
    const conflictDates = await planMutationService.loadExistingConflictDates(
      supabase,
      userId,
      planType,
      targetDates
    );

    if (conflictDates.length > 0) {
      return res.status(409).json({
        error: 'Existing plans already exist for one or more requested dates.',
        conflict_dates: conflictDates,
        suggested_action: 'update',
      });
    }

    const created = planType === 'workout'
      ? await planMutationService.createWorkoutPlans(supabase, userId, normalizedItems)
      : await planMutationService.createDietPlans(supabase, userId, normalizedItems);

    return res.status(201).json({
      status: 'success',
      plan_type: planType,
      created_count: created.length,
      items: created,
    });
  } catch (error) {
    logger.error(`Internal createPlan error: ${error.message}`);
    return res.status(500).json({ error: 'Failed to create plan.' });
  }
};

// PUT /api/plan/update/:user_id
exports.updatePlan = async (req, res) => {
  try {
    const { user_id: userId } = req.params;
    const planType = normalizePlanType(req.body.plan_type);

    if (!planType) {
      return res.status(400).json({ error: 'plan_type is required.' });
    }

    const normalizedItems = normalizeIncomingPlanItems(planType, req.body.items);

    if (normalizedItems.length === 0) {
      return res.status(400).json({ error: 'plan_type and valid items are required.' });
    }

    const targetDates = dedupeDates(normalizedItems);

    const updated = planType === 'workout'
      ? await planMutationService.replaceWorkoutPlans(supabase, userId, normalizedItems)
      : await planMutationService.replaceDietPlans(supabase, userId, normalizedItems);

    return res.json({
      status: 'success',
      plan_type: planType,
      replaced_dates: targetDates,
      updated_count: updated.length,
    });
  } catch (error) {
    logger.error(`Internal updatePlan error: ${error.message}`);
    return res.status(500).json({ error: 'Failed to update plan.' });
  }
};

// PUT /api/plan/check/:user_id
exports.checkPlan = async (req, res) => {
  try {
    const { user_id: userId } = req.params;
    const { item_id: itemId } = req.body;
    const parsed = parsePlanCheckId(itemId || '');

    if (!parsed || !Number.isFinite(parsed.numericId)) {
      return res.status(400).json({ error: 'Invalid item_id format.' });
    }

    if (parsed.kind === 'exercise-item') {
      const ownedItem = await getOwnedExerciseItem(userId, parsed.numericId);
      if (!ownedItem) {
        return res.status(404).json({ error: 'Exercise item not found.' });
      }

      const { data: updatedItem, error } = await supabase
        .from('exercise_items')
        .update({ is_completed: true })
        .eq('item_id', parsed.numericId)
        .select('item_id, exercise_id')
        .single();

      if (error) throw error;

      const parentStatus = await rebuildParentExerciseStatus(updatedItem.exercise_id);
      return res.json({
        status: 'success',
        item_id: itemId,
        checked: true,
        parent_status: parentStatus,
      });
    }

    if (parsed.kind === 'exercise') {
      const ownedPlan = await getOwnedExercisePlan(userId, parsed.numericId);
      if (!ownedPlan) {
        return res.status(404).json({ error: 'Exercise plan not found.' });
      }

      const { data: updatedPlan, error: parentError } = await supabase
        .from('user_exercise_plans')
        .update({ status: 1 })
        .eq('exercise_id', parsed.numericId)
        .eq('user_id', userId)
        .select('exercise_id')
        .maybeSingle();

      if (parentError) throw parentError;
      if (!updatedPlan) {
        return res.status(404).json({ error: 'Exercise plan not found.' });
      }

      const { error: itemError } = await supabase
        .from('exercise_items')
        .update({ is_completed: true })
        .eq('exercise_id', parsed.numericId);

      if (itemError) throw itemError;

      return res.json({
        status: 'success',
        item_id: itemId,
        checked: true,
        parent_status: 1,
      });
    }

    const { data: updatedMeal, error: mealError } = await supabase
      .from('user_meal_plans')
      .update({ is_completed: true })
      .eq('meal_id', parsed.numericId)
      .eq('user_id', userId)
      .select('meal_id')
      .maybeSingle();

    if (mealError) throw mealError;
    if (!updatedMeal) {
      return res.status(404).json({ error: 'Meal plan not found.' });
    }

    return res.json({
      status: 'success',
      item_id: itemId,
      checked: true,
    });
  } catch (error) {
    logger.error(`Internal checkPlan error: ${error.message}`);
    return res.status(500).json({ error: 'Failed to check plan item.' });
  }
};

// GET /api/workout-plan/full/:user_id
exports.getFullWorkoutPlan = async (req, res) => {
  try {
    const { user_id: userId } = req.params;
    const exercises = await loadExercisePlansWithItems(supabase, { userId });

    return res.json({
      plan_type: 'workout',
      items: (exercises || []).map((exercise) => ({
        id: `exercise-${exercise.exercise_id}`,
        name: exercise.exercise_type,
        detail: (exercise.exercise_items || []).map((item) => item.exercise_name).join(', ') || null,
        day: exercise.target_date,
        completed: exercise.status === 1,
        ex_list: (exercise.exercise_items || []).map((item) => ({
          exercise_name: item.exercise_name,
          sets: item.target_sets ?? null,
          duration_minutes: item.duration_minutes ?? null,
          calories: item.calories ?? 0,
        })),
      })),
    });
  } catch (error) {
    logger.error(`Internal getFullWorkoutPlan error: ${error.message}`);
    return res.status(500).json({ error: 'Failed to load workout plans.' });
  }
};

// GET /api/diet-plan/full/:user_id
exports.getFullDietPlan = async (req, res) => {
  try {
    const { user_id: userId } = req.params;

    const { data: meals, error } = await supabase
      .from('user_meal_plans')
      .select('*')
      .eq('user_id', userId)
      .order('target_date', { ascending: true })
      .order('created_at', { ascending: true });

    if (error) throw error;

    return res.json({
      plan_type: 'diet',
      items: (meals || []).map((meal) => ({
        id: `meal-${meal.meal_id}`,
        name: meal.meal_type,
        detail: meal.food_name,
        day: meal.target_date,
        completed: Boolean(meal.is_completed),
      })),
    });
  } catch (error) {
    logger.error(`Internal getFullDietPlan error: ${error.message}`);
    return res.status(500).json({ error: 'Failed to load diet plans.' });
  }
};
