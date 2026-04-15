function attachExerciseItemsToPlans(plans = [], items = []) {
  const groupedItems = new Map();

  for (const item of items) {
    const exerciseId = item.exercise_id;
    if (!groupedItems.has(exerciseId)) {
      groupedItems.set(exerciseId, []);
    }
    groupedItems.get(exerciseId).push(item);
  }

  return plans.map((plan) => ({
    ...plan,
    exercise_items: groupedItems.get(plan.exercise_id) || [],
  }));
}

async function loadExercisePlansWithItems(
  supabase,
  {
    userId,
    targetDate = null,
    startDate = null,
    endDate = null,
  }
) {
  let query = supabase
    .from('user_exercise_plans')
    .select('*')
    .eq('user_id', userId);

  if (targetDate) {
    query = query.eq('target_date', targetDate);
  }

  if (startDate) {
    query = query.gte('target_date', startDate);
  }

  if (endDate) {
    query = query.lte('target_date', endDate);
  }

  const { data: plans, error } = await query
    .order('target_date', { ascending: true })
    .order('created_at', { ascending: true });

  if (error) throw error;

  if (!plans || plans.length === 0) {
    return [];
  }

  const exerciseIds = plans
    .map((plan) => plan.exercise_id)
    .filter((value) => value !== null && value !== undefined);

  if (exerciseIds.length === 0) {
    return attachExerciseItemsToPlans(plans, []);
  }

  const { data: items, error: itemError } = await supabase
    .from('exercise_items')
    .select('*')
    .in('exercise_id', exerciseIds)
    .order('item_id', { ascending: true });

  if (itemError) throw itemError;

  return attachExerciseItemsToPlans(plans, items || []);
}

module.exports = {
  attachExerciseItemsToPlans,
  loadExercisePlansWithItems,
};
