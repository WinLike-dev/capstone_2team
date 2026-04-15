function dedupeDates(items = []) {
  return [...new Set(items.map((item) => item.day))];
}

async function deleteWorkoutPlansByIds(supabase, userId, exerciseIds = []) {
  if (exerciseIds.length === 0) return;

  const { error: itemError } = await supabase
    .from('exercise_items')
    .delete()
    .in('exercise_id', exerciseIds);

  if (itemError) throw itemError;

  const { error: planError } = await supabase
    .from('user_exercise_plans')
    .delete()
    .eq('user_id', userId)
    .in('exercise_id', exerciseIds);

  if (planError) throw planError;
}

async function deleteDietPlansByIds(supabase, userId, mealIds = []) {
  if (mealIds.length === 0) return;

  const { error } = await supabase
    .from('user_meal_plans')
    .delete()
    .eq('user_id', userId)
    .in('meal_id', mealIds);

  if (error) throw error;
}

async function loadExistingConflictDates(supabase, userId, planType, targetDates = []) {
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

async function loadExistingWorkoutPlanIdsForDates(supabase, userId, targetDates = []) {
  if (targetDates.length === 0) return [];

  const { data, error } = await supabase
    .from('user_exercise_plans')
    .select('exercise_id')
    .eq('user_id', userId)
    .in('target_date', targetDates);

  if (error) throw error;
  return (data || []).map((plan) => plan.exercise_id).filter(Boolean);
}

async function loadExistingDietPlanIdsForDates(supabase, userId, targetDates = []) {
  if (targetDates.length === 0) return [];

  const { data, error } = await supabase
    .from('user_meal_plans')
    .select('meal_id')
    .eq('user_id', userId)
    .in('target_date', targetDates);

  if (error) throw error;
  return (data || []).map((meal) => meal.meal_id).filter(Boolean);
}

async function createWorkoutPlans(supabase, userId, normalizedItems = []) {
  const createdItems = [];
  const createdExerciseIds = [];

  try {
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
      createdExerciseIds.push(plan.exercise_id);

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
  } catch (error) {
    if (createdExerciseIds.length > 0) {
      try {
        await deleteWorkoutPlansByIds(supabase, userId, createdExerciseIds);
      } catch (rollbackError) {
        error.rollbackError = rollbackError;
      }
    }
    throw error;
  }
}

async function createDietPlans(supabase, userId, normalizedItems = []) {
  const createdItems = [];
  const createdMealIds = [];

  try {
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
        createdMealIds.push(retry.data.meal_id);
        createdItems.push(retry.data);
        continue;
      }

      createdMealIds.push(meal.meal_id);
      createdItems.push(meal);
    }

    return createdItems;
  } catch (error) {
    if (createdMealIds.length > 0) {
      try {
        await deleteDietPlansByIds(supabase, userId, createdMealIds);
      } catch (rollbackError) {
        error.rollbackError = rollbackError;
      }
    }
    throw error;
  }
}

async function replaceWorkoutPlans(supabase, userId, normalizedItems = []) {
  const targetDates = dedupeDates(normalizedItems);
  const existingExerciseIds = await loadExistingWorkoutPlanIdsForDates(supabase, userId, targetDates);
  const createdItems = await createWorkoutPlans(supabase, userId, normalizedItems);

  try {
    await deleteWorkoutPlansByIds(supabase, userId, existingExerciseIds);
  } catch (error) {
    const createdExerciseIds = createdItems
      .map((item) => item.plan?.exercise_id)
      .filter(Boolean);

    try {
      await deleteWorkoutPlansByIds(supabase, userId, createdExerciseIds);
    } catch (rollbackError) {
      error.rollbackError = rollbackError;
    }
    throw error;
  }

  return createdItems;
}

async function replaceDietPlans(supabase, userId, normalizedItems = []) {
  const targetDates = dedupeDates(normalizedItems);
  const existingMealIds = await loadExistingDietPlanIdsForDates(supabase, userId, targetDates);
  const createdItems = await createDietPlans(supabase, userId, normalizedItems);

  try {
    await deleteDietPlansByIds(supabase, userId, existingMealIds);
  } catch (error) {
    const createdMealIds = createdItems
      .map((item) => item.meal_id)
      .filter(Boolean);

    try {
      await deleteDietPlansByIds(supabase, userId, createdMealIds);
    } catch (rollbackError) {
      error.rollbackError = rollbackError;
    }
    throw error;
  }

  return createdItems;
}

module.exports = {
  createDietPlans,
  createWorkoutPlans,
  deleteDietPlansByIds,
  deleteWorkoutPlansByIds,
  loadExistingConflictDates,
  replaceDietPlans,
  replaceWorkoutPlans,
};
