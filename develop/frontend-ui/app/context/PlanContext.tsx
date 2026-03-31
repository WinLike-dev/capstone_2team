"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type WorkoutItem = {
  title: string;
  time: string;
  level: string;
  calories: string;
  color: string;
  type?: string; 
};

export type DietItem = {
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

type CompletedTasksType = Record<string, { workouts: number[], diets: number[] }>;

interface PlanContextType {
  plans: DailyPlan[];
  completedTasks: CompletedTasksType;
  addWorkout: (dateStr: string, workout: WorkoutItem) => void;
  replaceDiet: (dateStr: string, mealType: string, newDiet: Omit<DietItem, 'type'>) => void;
  completeWorkout: (dateStr: string, idx: number) => void;
  completeDiet: (dateStr: string, idx: number) => void;
  getPlanByDate: (date: Date | string) => DailyPlan | null;
}

const PlanContext = createContext<PlanContextType | undefined>(undefined);

const generateMockPlans = (): DailyPlan[] => {
  const generatedPlans: DailyPlan[] = [];
  const start = new Date('2026-03-01');
  const end = new Date('2026-04-30');
  
  const workoutTemplates = [
    [
      { title: "모닝 조깅 & 워밍업", time: "20분", level: "초급", calories: "150 kcal", color: "from-sky-400 to-blue-500", type: "유산소" },
      { title: "전신 근력 데드리프트", time: "40분", level: "중급", calories: "350 kcal", color: "from-indigo-500 to-purple-600", type: "전신운동" },
      { title: "수면 전 릴렉스 요가", time: "15분", level: "초급", calories: "50 kcal", color: "from-teal-400 to-emerald-500", type: "스트레칭" }
    ],
    [
      { title: "공복 실내 자전거", time: "30분", level: "초급", calories: "200 kcal", color: "from-blue-500 to-indigo-600", type: "유산소" },
      { title: "맨몸 코어 트레이닝", time: "20분", level: "중급", calories: "150 kcal", color: "from-orange-400 to-red-500", type: "코어운동" },
      { title: "폼롤러 하체 스트레칭", time: "10분", level: "초급", calories: "40 kcal", color: "from-pink-400 to-rose-500", type: "하체운동" }
    ],
    [
      { title: "경사로 걷기 (인클라인)", time: "40분", level: "초급", calories: "250 kcal", color: "from-sky-400 to-blue-500", type: "유산소" },
      { title: "상체 덤벨 웨이트", time: "35분", level: "중급", calories: "280 kcal", color: "from-indigo-500 to-purple-600", type: "상체운동" },
      { title: "어깨/목 뭉침 해소 스트레칭", time: "15분", level: "초급", calories: "60 kcal", color: "from-green-400 to-emerald-500", type: "스트레칭" }
    ],
    [
      { title: "HIIT 인터벌 트레이닝", time: "20분", level: "상급", calories: "300 kcal", color: "from-red-500 to-orange-600", type: "고강도" },
      { title: "하체 중심 맨몸 스쿼트", time: "25분", level: "중급", calories: "200 kcal", color: "from-purple-500 to-indigo-600", type: "하체운동" },
      { title: "정적인 전신 요가", time: "20분", level: "초급", calories: "80 kcal", color: "from-teal-400 to-emerald-500", type: "스트레칭" }
    ],
  ];

  const dietTemplates = [
    {
      breakfast: { name: "두부 된장국 & 소고기 장조림", desc: "속이 편안한 한식 아침", kcal: "350 kcal" },
      lunch: { name: "닭가슴살 볶음밥", desc: "단백질 풍부한 든든한 점심", kcal: "450 kcal" },
      dinner: { name: "소고기 무국", desc: "따뜻하고 담백한 저녁", kcal: "300 kcal" }
    },
    {
      breakfast: { name: "통밀 샌드위치 & 우유", desc: "가벼운 서양식 조식", kcal: "320 kcal" },
      lunch: { name: "연어 아보카도 포케 보울", desc: "건강한 지방 충전", kcal: "420 kcal" },
      dinner: { name: "안심 스테이크 & 구운 야채", desc: "풍미 가득한 단백질", kcal: "500 kcal" }
    },
    {
      breakfast: { name: "낫토 & 계란말이 밥", desc: "건강한 발효 한 끼", kcal: "380 kcal" },
      lunch: { name: "메밀 소바 & 닭가슴살 토핑", desc: "깔끔하고 시원한 점심", kcal: "400 kcal" },
      dinner: { name: "연어 초밥 & 미니 우동", desc: "부담 없는 저녁", kcal: "450 kcal" }
    },
    {
      breakfast: { name: "그릭 요거트 & 그래놀라", desc: "가볍게 시작하는 하루", kcal: "250 kcal" },
      lunch: { name: "닭가슴살 샐러드 파스타", desc: "식이섬유 & 단백질 조합", kcal: "350 kcal" },
      dinner: { name: "단백질 쉐이크 & 고구마", desc: "칼로리 조절 저녁", kcal: "280 kcal" }
    }
  ];

  let current = new Date(start);
  let dayCount = 0;
  while (current <= end) {
    const dateStr = `${current.getFullYear()}-${String(current.getMonth() + 1).padStart(2, '0')}-${String(current.getDate()).padStart(2, '0')}`;
    const wT = workoutTemplates[dayCount % workoutTemplates.length];
    const dT = dietTemplates[dayCount % dietTemplates.length];
    
    generatedPlans.push({
      date: dateStr,
      task: '맞춤형 복합 밸런스 플랜',
      workout: { type: '유산소 + 근력 + 스트레칭', sets: '총 3가지 운동 코스 진행' },
      diet: { breakfast: dT.breakfast.name, lunch: dT.lunch.name, dinner: dT.dinner.name },
      exercises: [...wT], // copy to prevent mutation reference issues
      diets: [
        { type: "아침", ...dT.breakfast },
        { type: "점심", ...dT.lunch },
        { type: "저녁", ...dT.dinner }
      ]
    });
    
    current.setDate(current.getDate() + 1);
    dayCount++;
  }
  return generatedPlans;
};

export const PlanProvider = ({ children }: { children: ReactNode }) => {
  const [plans, setPlans] = useState<DailyPlan[]>([]);
  const [completedTasks, setCompletedTasks] = useState<CompletedTasksType>({});

  useEffect(() => {
    // 앱 진입 시 한 번만 mock 데이터 로드 (실제라면 API Fetch)
    // 로컬 스토리지에 저장된 플랜 데이터가 있다면 불러오고, 없으면 mock 생성
    const storedPlans = localStorage.getItem('healthAppPlans');
    if (storedPlans) {
      setPlans(JSON.parse(storedPlans));
    } else {
      const initPlans = generateMockPlans();
      setPlans(initPlans);
      localStorage.setItem('healthAppPlans', JSON.stringify(initPlans));
    }

    const storedCompleted = localStorage.getItem('healthAppCompletedTasks');
    if (storedCompleted) {
      setCompletedTasks(JSON.parse(storedCompleted));
    }
  }, []);

  // 상태 변경될 때마다 localStorage 갱신 (선택적 영속화)
  useEffect(() => {
    if (plans.length > 0) {
      localStorage.setItem('healthAppPlans', JSON.stringify(plans));
    }
  }, [plans]);

  useEffect(() => {
    localStorage.setItem('healthAppCompletedTasks', JSON.stringify(completedTasks));
  }, [completedTasks]);

  const completeWorkout = (dateStr: string, idx: number) => {
    setCompletedTasks(prev => {
      const dayTasks = prev[dateStr] || { workouts: [], diets: [] };
      if (dayTasks.workouts.includes(idx)) return prev; // 이미 완료된 경우 (추가 클릭 방지용)
      
      const newWorkouts = [...dayTasks.workouts, idx];
      return { ...prev, [dateStr]: { ...dayTasks, workouts: newWorkouts } };
    });
  };

  const completeDiet = (dateStr: string, idx: number) => {
    setCompletedTasks(prev => {
      const dayTasks = prev[dateStr] || { workouts: [], diets: [] };
      if (dayTasks.diets.includes(idx)) return prev; // 이미 완료된 경우 (추가 클릭 방지용)

      const newDiets = [...dayTasks.diets, idx];
      return { ...prev, [dateStr]: { ...dayTasks, diets: newDiets } };
    });
  };

  const addWorkout = (dateStr: string, workout: WorkoutItem) => {
    setPlans(prevPlans => prevPlans.map(plan => {
      if (plan.date === dateStr) {
        return {
          ...plan,
          exercises: [...plan.exercises, workout]
        };
      }
      return plan;
    }));
  };

  const replaceDiet = (dateStr: string, mealType: string, newDiet: Omit<DietItem, 'type'>) => {
    // mealType: 'breakfast' | 'lunch' | 'dinner'
    const mealLabel = mealType === 'breakfast' ? '아침' : mealType === 'lunch' ? '점심' : '저녁';
    
    setPlans(prevPlans => prevPlans.map(plan => {
      if (plan.date === dateStr) {
        const updatedDiets = plan.diets.map(d => {
          if (d.type === mealLabel) {
            return {
              type: mealLabel,
              ...newDiet
            };
          }
          return d;
        });
        
        // If not found (e.g., someone deleted it?), adding it logic here could exist, but map suffices for our fixed 3 elements
        
        return {
          ...plan,
          diets: updatedDiets
        };
      }
      return plan;
    }));

    // 기존에 만약 '완료' 처리가 된 경우 초기화 필요하다면 진행 (생략해도 무방)
    setCompletedTasks(prev => {
        const dayTasks = prev[dateStr] || { workouts: [], diets: [] };
        // 아/점/저 인덱스는 0/1/2 로 고정됨
        const targetIdx = mealLabel === '아침' ? 0 : mealLabel === '점심' ? 1 : 2;
        if (dayTasks.diets.includes(targetIdx)) {
            const newDiets = dayTasks.diets.filter(id => id !== targetIdx);
            return { ...prev, [dateStr]: { ...dayTasks, diets: newDiets } };
        }
        return prev;
    });
  };

  const getPlanByDate = (date: Date | string) => {
    let dateStr = "";
    if (typeof date === 'string') {
      dateStr = date;
    } else {
      dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    }
    return plans.find(p => p.date === dateStr) || null;
  };

  return (
    <PlanContext.Provider value={{ plans, completedTasks, addWorkout, replaceDiet, completeWorkout, completeDiet, getPlanByDate }}>
      {children}
    </PlanContext.Provider>
  );
};

export const usePlan = () => {
  const context = useContext(PlanContext);
  if (context === undefined) {
    throw new Error('usePlan must be used within a PlanProvider');
  }
  return context;
};
