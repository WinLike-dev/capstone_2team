export type WorkoutSlot = "upper_body" | "lower_body" | "cardio" | "stretching";
export type DietSlot = "breakfast" | "lunch" | "dinner";
export type RecommendationScope = "all" | "workout" | "diet";

export type WorkoutRecommendation = {
  exercise_name: string;
  summary: string;
  sets?: number | null;
  duration_minutes?: number | null;
  calories: number;
};

export type DietRecommendation = {
  food_name: string;
  summary: string;
  calories: number;
};

export type HomeRecommendations = {
  date: string;
  scope: RecommendationScope;
  workout: Record<WorkoutSlot, WorkoutRecommendation | null>;
  diet: Record<DietSlot, DietRecommendation | null>;
};

export type RecommendationAddedState = {
  workout: Record<WorkoutSlot, boolean>;
  diet: Record<DietSlot, boolean>;
};

export type HomeRecommendationCache = {
  recommendations: HomeRecommendations;
  added: RecommendationAddedState;
};

export const WORKOUT_SLOTS: WorkoutSlot[] = [
  "upper_body",
  "lower_body",
  "cardio",
  "stretching",
];

export const DIET_SLOTS: DietSlot[] = ["breakfast", "lunch", "dinner"];

export function createEmptyAddedState(): RecommendationAddedState {
  return {
    workout: {
      upper_body: false,
      lower_body: false,
      cardio: false,
      stretching: false,
    },
    diet: {
      breakfast: false,
      lunch: false,
      dinner: false,
    },
  };
}

export function createEmptyRecommendations(date: string): HomeRecommendations {
  return {
    date,
    scope: "all",
    workout: {
      upper_body: null,
      lower_body: null,
      cardio: null,
      stretching: null,
    },
    diet: {
      breakfast: null,
      lunch: null,
      dinner: null,
    },
  };
}

export function getHomeRecommendationCacheKey(userId: string, date: string) {
  return `healthAppHomeRecommendations:${userId}:${date}`;
}

export function mergeRecommendations(
  current: HomeRecommendations,
  incoming: HomeRecommendations,
  scope: RecommendationScope
): HomeRecommendations {
  if (scope === "workout") {
    return {
      ...current,
      date: incoming.date,
      scope,
      workout: incoming.workout,
    };
  }

  if (scope === "diet") {
    return {
      ...current,
      date: incoming.date,
      scope,
      diet: incoming.diet,
    };
  }

  return incoming;
}

export function resetAddedStateForScope(
  current: RecommendationAddedState,
  scope: RecommendationScope
): RecommendationAddedState {
  if (scope === "workout") {
    return {
      ...current,
      workout: createEmptyAddedState().workout,
    };
  }

  if (scope === "diet") {
    return {
      ...current,
      diet: createEmptyAddedState().diet,
    };
  }

  return createEmptyAddedState();
}
