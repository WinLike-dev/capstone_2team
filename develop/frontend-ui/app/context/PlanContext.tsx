"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  AUTH_TOKEN_STORAGE_KEY,
  AUTH_USER_STORAGE_KEY,
  redirectToLoginForExpiredSession,
} from "@/lib/auth";
import { formatKstDate } from "@/lib/date";

export type WorkoutItem = {
  itemId?: string;
  title: string;
  time: string;
  level: string;
  calories: string;
  color: string;
  type?: string;
  targetSets?: number | null;
  durationMinutes?: number | null;
};

export type DietItem = {
  itemId?: string;
  type: string;
  name: string;
  desc: string;
  kcal: string;
};

export type DailyPlan = {
  date: string;
  task: string;
  workout: { type: string; sets: string };
  diet: { breakfast: string; lunch: string; dinner: string };
  exercises: WorkoutItem[];
  diets: DietItem[];
};

export type UserData = {
  user_id?: string;
  login_id?: string;
  name?: string;
  nickname?: string;
  email?: string;
  goal?: string;
  allergies?: string[];
  conditions?: string[];
  medical_history?: string[] | string;
  gender?: string;
  age?: number | string;
  bmi?: number | string;
  weight?: string | number;
  height?: string | number;
  activityLevel?: string;
  activity_level?: string;
  has_health_profile?: boolean;
  mbti?: string;
  otherAllergy?: string;
  selected_ai_persona?: string | null;
};

type CompletedTasksType = Record<string, { workouts: number[]; diets: number[] }>;

interface PlanContextType {
  plans: DailyPlan[];
  completedTasks: CompletedTasksType;
  addWorkout: (dateStr: string, workout: WorkoutItem) => Promise<boolean>;
  replaceDiet: (
    dateStr: string,
    mealType: string,
    newDiet: Omit<DietItem, "type">
  ) => Promise<boolean>;
  completeWorkout: (dateStr: string, idx: number) => Promise<void>;
  completeDiet: (dateStr: string, idx: number) => Promise<void>;
  getPlanByDate: (date: Date | string) => DailyPlan | null;
  userData: UserData | null;
  isUserLoading: boolean;
  fetchPlans: () => Promise<void>;
  fetchUserProfile: () => Promise<void>;
  updateUserData: (data: Partial<UserData>) => void;
}

const PlanContext = createContext<PlanContextType | undefined>(undefined);

const WORKOUT_COLORS = [
  "from-sky-400 to-blue-500",
  "from-indigo-500 to-purple-600",
  "from-teal-400 to-emerald-500",
  "from-orange-400 to-red-500",
];

type CalendarExerciseItem = {
  item_id?: number;
  exercise_name?: string;
  is_completed?: boolean;
  calories?: number;
  target_sets?: number | null;
  duration_minutes?: number | null;
};

type CalendarExercisePlan = {
  exercise_id?: number;
  exercise_type?: string;
  total_calories?: number;
  status?: number;
  target_date?: string;
  exercise_items?: CalendarExerciseItem[];
};

type CalendarMealPlan = {
  meal_id?: number;
  meal_type?: string;
  food_name?: string;
  calories?: number;
  is_completed?: boolean;
  target_date?: string;
};

type CalendarResponse = Record<
  string,
  {
    exercises?: CalendarExercisePlan[];
    meals?: CalendarMealPlan[];
  }
>;

function getApiBaseUrl() {
  const raw =
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "";
  return raw.endsWith("/") ? raw.slice(0, -1) : raw;
}

function buildApiUrl(path: string) {
  const baseUrl = getApiBaseUrl();
  return baseUrl ? `${baseUrl}${path}` : path;
}

function getAuthHeaders() {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)
      : null;

  return {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function safeParseArray(value: unknown) {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value.map(String);
  }

  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return [];
    if (trimmed.startsWith("[")) {
      try {
        const parsed = JSON.parse(trimmed);
        return Array.isArray(parsed) ? parsed.map(String) : [];
      } catch (error) {
        return [];
      }
    }
    return [trimmed];
  }

  return [];
}

function formatDateKey(date: Date | string) {
  if (typeof date === "string") {
    return date;
  }

  return formatKstDate(date);
}

function parseCalories(value: string) {
  const matched = value.match(/\d+/);
  return matched ? Number(matched[0]) : 0;
}

function buildSummaryMealLabel(mealType?: string) {
  const key = String(mealType || "").toLowerCase();
  if (key.includes("breakfast") || key.includes("아침")) return "Breakfast";
  if (key.includes("lunch") || key.includes("점심")) return "Lunch";
  if (key.includes("dinner") || key.includes("저녁")) return "Dinner";
  return mealType || "Meal";
}

function normalizeCalendarResponse(response: CalendarResponse) {
  const completedTasks: CompletedTasksType = {};
  const plans: DailyPlan[] = Object.entries(response || {})
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([date, payload]) => {
      const exercisePlans = [...(payload.exercises || [])].sort(
        (left, right) => (left.exercise_id || 0) - (right.exercise_id || 0)
      );
      const mealPlans = [...(payload.meals || [])].sort(
        (left, right) => (left.meal_id || 0) - (right.meal_id || 0)
      );

      const exercises: (WorkoutItem & { completed?: boolean })[] = [];
      exercisePlans.forEach((plan, planIndex) => {
        const exerciseItems = Array.isArray(plan.exercise_items)
          ? plan.exercise_items
          : [];

        if (exerciseItems.length > 0) {
          exerciseItems.forEach((item, itemIndex) => {
            exercises.push({
              itemId: item.item_id
                ? `exercise-item-${item.item_id}`
                : undefined,
              title: item.exercise_name || plan.exercise_type || "Exercise",
              time: item.duration_minutes
                ? `${item.duration_minutes} min`
                : item.target_sets
                  ? `${item.target_sets} sets`
                  : "scheduled",
              level: plan.exercise_type || "exercise",
              calories: `${item.calories ?? 0} kcal`,
              color:
                WORKOUT_COLORS[(planIndex + itemIndex) % WORKOUT_COLORS.length],
              type: plan.exercise_type || "exercise",
              targetSets: item.target_sets ?? null,
              durationMinutes: item.duration_minutes ?? null,
              completed: Boolean(item.is_completed),
            });
          });
          return;
        }

        exercises.push({
          itemId: plan.exercise_id ? `exercise-${plan.exercise_id}` : undefined,
          title: plan.exercise_type || "Exercise",
          time: "scheduled",
          level: "plan",
          calories: `${plan.total_calories ?? 0} kcal`,
          color: WORKOUT_COLORS[planIndex % WORKOUT_COLORS.length],
          type: plan.exercise_type || "exercise",
          completed: plan.status === 1,
        });
      });

      const diets: (DietItem & { completed?: boolean })[] = mealPlans.map(
        (meal) => ({
          itemId: meal.meal_id ? `meal-${meal.meal_id}` : undefined,
          type: buildSummaryMealLabel(meal.meal_type),
          name: meal.food_name || "Meal",
          desc: meal.meal_type || "meal",
          kcal: `${meal.calories ?? 0} kcal`,
          completed: Boolean(meal.is_completed),
        })
      );

      completedTasks[date] = {
        workouts: exercises.reduce<number[]>((acc, item, index) => {
          if (item.completed) acc.push(index);
          return acc;
        }, []),
        diets: diets.reduce<number[]>((acc, item, index) => {
          if (item.completed) acc.push(index);
          return acc;
        }, []),
      };

      const breakfast =
        diets.find((item) => item.type === "Breakfast")?.name || "";
      const lunch = diets.find((item) => item.type === "Lunch")?.name || "";
      const dinner = diets.find((item) => item.type === "Dinner")?.name || "";

      return {
        date,
        task:
          exercises.length || diets.length
            ? "AI synced plan"
            : "No synced plan",
        workout: {
          type: exercises.length ? "exercise plan" : "rest",
          sets: `${exercises.length} items`,
        },
        diet: {
          breakfast,
          lunch,
          dinner,
        },
        exercises: exercises.map(({ completed, ...item }) => item),
        diets: diets.map(({ completed, ...item }) => item),
      };
    });

  return {
    plans,
    completedTasks,
  };
}

export const PlanProvider = ({ children }: { children: ReactNode }) => {
  const [plans, setPlans] = useState<DailyPlan[]>([]);
  const [completedTasks, setCompletedTasks] = useState<CompletedTasksType>({});
  const [userData, setUserData] = useState<UserData | null>(null);
  const [isUserLoading, setIsUserLoading] = useState(true);

  const fetchPlans = useCallback(async () => {
    if (typeof window === "undefined") return;

    const token = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
    if (!token) {
      setPlans([]);
      setCompletedTasks({});
      return;
    }

    const currentYear = Number(formatKstDate().slice(0, 4));
    const startDate = `${currentYear}-01-01`;
    const endDate = `${currentYear}-12-31`;

    try {
      const response = await fetch(
        buildApiUrl(
          `/api/v1/users/calendar?start_date=${startDate}&end_date=${endDate}`
        ),
        {
          headers: getAuthHeaders(),
        }
      );

      if (response.status === 401) {
        redirectToLoginForExpiredSession();
        return;
      }

      if (!response.ok) {
        throw new Error("Failed to fetch calendar.");
      }

      const data = (await response.json()) as CalendarResponse;
      const normalized = normalizeCalendarResponse(data);
      setPlans(normalized.plans);
      setCompletedTasks(normalized.completedTasks);
    } catch (error) {
      console.error("Failed to sync plans", error);
      setPlans([]);
      setCompletedTasks({});
    }
  }, []);

  const fetchUserProfile = useCallback(async () => {
    setIsUserLoading(true);

    if (typeof window === "undefined") {
      setIsUserLoading(false);
      return;
    }

    const token = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
    const stored = localStorage.getItem(AUTH_USER_STORAGE_KEY);

    if (stored) {
      try {
        const parsedStored = JSON.parse(stored);
        parsedStored.allergies = safeParseArray(parsedStored.allergies);
        parsedStored.conditions = safeParseArray(
          parsedStored.conditions || parsedStored.medical_history
        );
        setUserData(parsedStored);
      } catch (error) {
        console.error("Failed to parse local user cache", error);
      }
    }

    if (!token) {
      setIsUserLoading(false);
      return;
    }

    try {
      const response = await fetch(buildApiUrl("/api/v1/users/profile"), {
        headers: getAuthHeaders(),
      });

      if (response.status === 401) {
        redirectToLoginForExpiredSession();
        return;
      }

      if (!response.ok) {
        throw new Error("Failed to fetch profile.");
      }

      const freshData = await response.json();
      const previousData = stored ? JSON.parse(stored) : {};
      const mergedData = {
        ...previousData,
        ...freshData,
        activityLevel: freshData.activity_level || previousData.activityLevel,
        allergies: safeParseArray(freshData.allergies),
        conditions: safeParseArray(
          freshData.conditions || freshData.medical_history
        ),
      };

      setUserData(mergedData);
      localStorage.setItem(AUTH_USER_STORAGE_KEY, JSON.stringify(mergedData));
    } catch (error) {
      console.error("Failed to sync profile", error);
    } finally {
      setIsUserLoading(false);
    }
  }, []);

  const updateUserData = useCallback((data: Partial<UserData>) => {
    setUserData((previous) => {
      const next = { ...previous, ...data };
      if (typeof window !== "undefined") {
        localStorage.setItem(AUTH_USER_STORAGE_KEY, JSON.stringify(next));
      }
      return next;
    });
  }, []);

  useEffect(() => {
    fetchUserProfile();
    fetchPlans();
  }, [fetchPlans, fetchUserProfile]);

  const completePlanItem = useCallback(
    async (dateStr: string, idx: number, kind: "workout" | "diet") => {
      const plan = plans.find((item) => item.date === dateStr);
      const target =
        kind === "workout" ? plan?.exercises[idx] : plan?.diets[idx];

      if (!target?.itemId) {
        return;
      }

      try {
        const response = await fetch(buildApiUrl("/api/v1/users/plans/check"), {
          method: "PUT",
          headers: getAuthHeaders(),
          body: JSON.stringify({ item_id: target.itemId }),
        });

        if (response.status === 401) {
          redirectToLoginForExpiredSession();
          return;
        }

        if (!response.ok) {
          throw new Error("Failed to check plan item.");
        }

        await fetchPlans();
      } catch (error) {
        console.error("Failed to check plan item", error);
      }
    },
    [fetchPlans, plans]
  );

  const completeWorkout = useCallback(
    async (dateStr: string, idx: number) => {
      await completePlanItem(dateStr, idx, "workout");
    },
    [completePlanItem]
  );

  const completeDiet = useCallback(
    async (dateStr: string, idx: number) => {
      await completePlanItem(dateStr, idx, "diet");
    },
    [completePlanItem]
  );

  const addWorkout = useCallback(
    async (dateStr: string, workout: WorkoutItem) => {
      try {
        const response = await fetch(
          buildApiUrl("/api/v1/users/exercises/recommend-add"),
          {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify({
              target_date: dateStr,
              exercise_type: workout.type || "recommended",
              exercise_name: workout.title,
              calories: parseCalories(workout.calories),
              target_sets: workout.targetSets ?? null,
              duration_minutes: workout.durationMinutes ?? null,
            }),
          }
        );

        if (response.status === 401) {
          redirectToLoginForExpiredSession();
          return false;
        }

        if (!response.ok) {
          throw new Error("Failed to add recommended exercise.");
        }

        await fetchPlans();
        return true;
      } catch (error) {
        console.error("Failed to add recommended exercise", error);
        return false;
      }
    },
    [fetchPlans]
  );

  const replaceDiet = useCallback(
    async (dateStr: string, mealType: string, newDiet: Omit<DietItem, "type">) => {
      try {
        const response = await fetch(
          buildApiUrl("/api/v1/users/meals/recommend-replace"),
          {
            method: "PUT",
            headers: getAuthHeaders(),
            body: JSON.stringify({
              target_date: dateStr,
              meal_type: mealType,
              food_name: newDiet.name,
              calories: parseCalories(newDiet.kcal),
            }),
          }
        );

        if (response.status === 401) {
          redirectToLoginForExpiredSession();
          return false;
        }

        if (!response.ok) {
          throw new Error("Failed to replace recommended meal.");
        }

        await fetchPlans();
        return true;
      } catch (error) {
        console.error("Failed to replace recommended meal", error);
        return false;
      }
    },
    [fetchPlans]
  );

  const getPlanByDate = useCallback(
    (date: Date | string) => {
      const dateKey = formatDateKey(date);
      return plans.find((plan) => plan.date === dateKey) || null;
    },
    [plans]
  );

  return (
    <PlanContext.Provider
      value={{
        plans,
        completedTasks,
        addWorkout,
        replaceDiet,
        completeWorkout,
        completeDiet,
        getPlanByDate,
        userData,
        isUserLoading,
        fetchPlans,
        fetchUserProfile,
        updateUserData,
      }}
    >
      {children}
    </PlanContext.Provider>
  );
};

export const usePlan = () => {
  const context = useContext(PlanContext);
  if (!context) {
    throw new Error("usePlan must be used within a PlanProvider");
  }
  return context;
};
