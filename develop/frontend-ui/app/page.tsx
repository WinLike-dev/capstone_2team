/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Calendar, CheckSquare, Plus, Trash2, X, Droplets, Utensils, Activity, RefreshCw, Heart, Info, Dumbbell, PersonStanding } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { usePlan } from './context/PlanContext';

export type TodoItem = {
  id: number;
  text: string;
  completed: boolean;
  type?: 'workout' | 'diet' | 'general';
  mealType?: 'breakfast' | 'lunch' | 'dinner';
  calories?: number;
  img?: string;
};

const getFoodEmoji = (name: string) => {
  if (name.includes('샐러드') || name.includes('야채')) return '🥗';
  if (name.includes('스테이크') || name.includes('고기') || name.includes('장조림')) return '🍖';
  if (name.includes('쉐이크') || name.includes('우유')) return '🥛';
  if (name.includes('밥') || name.includes('국') || name.includes('찌개') || name.includes('된장')) return '🍚';
  if (name.includes('파스타') || name.includes('면') || name.includes('소바') || name.includes('우동')) return '🍝';
  if (name.includes('샌드위치') || name.includes('빵') || name.includes('오트밀')) return '🥪';
  if (name.includes('계란') || name.includes('에그') || name.includes('낫토')) return '🍳';
  if (name.includes('연어') || name.includes('초밥')) return '🍣';
  if (name.includes('요거트') || name.includes('보울')) return '🥣';
  if (name.includes('닭')) return '🍗';
  return '🥗';
};

export default function Home() {
  const router = useRouter();
  const { addWorkout, replaceDiet, getPlanByDate } = usePlan();
  const [userData, setUserData] = useState<{ nickname?: string, name?: string, goal?: string, allergies?: string[], conditions?: string[], gender?: string, age?: number | string, bmi?: number | string, weight?: string, height?: string, user_instruction?: string } | null>(null);
  const [isClient, setIsClient] = useState(false);
  const [isPlannerOpen, setIsPlannerOpen] = useState(false);

  // Calorie & Nutrient Modals state
  const [isCalorieModalOpen, setIsCalorieModalOpen] = useState(false);
  const [isNutrientModalOpen, setIsNutrientModalOpen] = useState(false);
  const [goalInput, setGoalInput] = useState({
    calories: '',
    carbs: '',
    protein: '',
    fat: '',
  });
  const [goalErrorMsg, setGoalErrorMsg] = useState('');
  const [isGoalSaving, setIsGoalSaving] = useState(false);

  // Targets (displayed in UI)
  const [targets, setTargets] = useState({
    calories: 2000,
    carbs: 250,
    protein: 80,
    fat: 50
  });

  // Current Intakes (mock for UI initially, gets updated by AI)
  const [resetConfirmModal, setResetConfirmModal] = useState<{ isOpen: boolean, target: 'calories' | 'macros' | null }>({ isOpen: false, target: null });
  const [intakes, setIntakes] = useState({
    calories: 0,
    carbs: 0,
    protein: 0,
    fat: 0
  });

  // Recommended Items Like State
  const [likedItems, setLikedItems] = useState<Record<string, boolean>>({});

  const handleLikeRecommendation = (e: React.MouseEvent, item: any) => {
    e.stopPropagation();
    // Toggle liked state locally
    setLikedItems(prev => ({ ...prev, [item.id]: !prev[item.id] }));
  };

  // Calculated Fallback
  const [recommendedCalories, setRecommendedCalories] = useState(2000);

  const handleCalorieSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setGoalErrorMsg('');

    const cal = Number(goalInput.calories);
    if (isNaN(cal) || cal <= 0 || cal >= 10000) {
      return setGoalErrorMsg('올바른 범위를 입력해주세요 (1~9999)');
    }

    setIsGoalSaving(true);
    try {
      const rawApiUrl = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || '';
      const baseUrl = rawApiUrl.endsWith('/') ? rawApiUrl.slice(0, -1) : rawApiUrl;
      const endpoint = baseUrl ? `${baseUrl}/users/profile` : '/api/mock-save';

      if (baseUrl) {
        await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true' },
          body: JSON.stringify({
            target_calories: cal,
            target_carbs: targets.carbs,
            target_protein: targets.protein,
            target_fat: targets.fat
          }),
        });
      }

      setTargets(prev => ({ ...prev, calories: cal }));
      setIsCalorieModalOpen(false);
    } catch (err) {
      console.error(err);
      setGoalErrorMsg('저장에 실패했습니다.');
    } finally {
      setIsGoalSaving(false);
    }
  };

  const handleNutrientSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setGoalErrorMsg('');

    const car = Number(goalInput.carbs);
    const pro = Number(goalInput.protein);
    const fa = Number(goalInput.fat);

    if (isNaN(car) || car <= 0 || car >= 10000 ||
      isNaN(pro) || pro <= 0 || pro >= 10000 ||
      isNaN(fa) || fa <= 0 || fa >= 10000) {
      return setGoalErrorMsg('올바른 범위를 입력해주세요 (1~9999)');
    }

    setIsGoalSaving(true);
    try {
      const rawApiUrl = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || '';
      const baseUrl = rawApiUrl.endsWith('/') ? rawApiUrl.slice(0, -1) : rawApiUrl;
      const endpoint = baseUrl ? `${baseUrl}/users/profile` : '/api/mock-save';

      if (baseUrl) {
        await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true' },
          body: JSON.stringify({
            target_calories: targets.calories,
            target_carbs: car,
            target_protein: pro,
            target_fat: fa
          }),
        });
      }

      setTargets(prev => ({ ...prev, carbs: car, protein: pro, fat: fa }));
      setIsNutrientModalOpen(false);
    } catch (err) {
      console.error(err);
      setGoalErrorMsg('저장에 실패했습니다.');
    } finally {
      setIsGoalSaving(false);
    }
  };

  // Diet Modal state
  const [isDietModalOpen, setIsDietModalOpen] = useState(false);
  const [manualInput, setManualInput] = useState({ calories: '', carbs: '', protein: '', fat: '' });
  const [dietAnalysis, setDietAnalysis] = useState<{ calories: number, carbs: number, protein: number, fat: number, message: string } | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Water tracker state (glasses of water)
  const [waterGlasses, setWaterGlasses] = useState(2);
  const maxWaterGlasses = 8;
  const [showWaterGoalAnim, setShowWaterGoalAnim] = useState(false);

  const [todos, setTodos] = useState<TodoItem[]>([
    { id: 1, text: '아침 스트레칭 10분', completed: false, type: 'workout' },
    { id: 2, text: '비타민 챙겨먹기', completed: false, type: 'general' },
    { id: 3, text: '기존 아침 식단 (사과 등)', completed: false, type: 'diet', mealType: 'breakfast', calories: 150 }
  ]);
  const [newTodo, setNewTodo] = useState('');

  // AI 추천 데이터 Mock
  const [aiRecommendations, setAiRecommendations] = useState({
    workout: {
      strength: {
        upper: { id: 's1', name: '푸시업', desc: '가슴/삼두근 강화', duration: '15분', icon: Activity },
        lower: { id: 's2', name: '스쿼트', desc: '하체/코어 단련', duration: '20분', icon: Activity }
      },
      cardio: { id: 'c1', name: '가벼운 조깅', desc: '심폐지구력 향상', duration: '30분', icon: Heart },
      stretching: { id: 'st1', name: '전신 이완 요가', desc: '근육 긴장 완화', duration: '10분', icon: Droplets }
    },
    diet: {
      breakfast: { id: 'd1', name: '오트밀과 과일', desc: '식이섬유 가득', calories: 350, icon: Utensils },
      lunch: { id: 'd2', name: '닭가슴살 샐러드', desc: '단백질 보충', calories: 450, icon: Utensils },
      dinner: { id: 'd3', name: '연어 스테이크', desc: '건강한 지방', calories: 500, icon: Utensils }
    }
  });

  // 팝업 모달 상태
  const [workoutPopup, setWorkoutPopup] = useState<{ isOpen: boolean, target: any }>({ isOpen: false, target: null });
  const [dietPopup, setDietPopup] = useState<{ isOpen: boolean, target: any, mealType: 'breakfast' | 'lunch' | 'dinner' | null }>({ isOpen: false, target: null, mealType: null });
  const [alertPopup, setAlertPopup] = useState<{ isOpen: boolean, message: string }>({ isOpen: false, message: '' });

  const handleWorkoutAddClick = (workout: any) => {
    setWorkoutPopup({ isOpen: true, target: workout });
  };

  const handleDietReplaceClick = (diet: any, mealType: 'breakfast' | 'lunch' | 'dinner') => {
    setDietPopup({ isOpen: true, target: diet, mealType });
  };

  const confirmWorkoutAdd = () => {
    if (workoutPopup.target) {
      const todayStr = new Date().toISOString().split('T')[0];
      const todayPlan = getPlanByDate(new Date());
      const isDuplicate = todayPlan?.exercises.some((ex: any) => ex.title === workoutPopup.target.name);

      if (isDuplicate) {
        setWorkoutPopup({ isOpen: false, target: null });
        setTimeout(() => setAlertPopup({ isOpen: true, message: '이미 캘린더에 추가된 운동입니다!' }), 100);
        return;
      }

      let typeLabel = '상체 운동';
      if (workoutPopup.target.desc.includes('가슴') || workoutPopup.target.desc.includes('상체')) typeLabel = '상체 운동';
      else if (workoutPopup.target.desc.includes('하체')) typeLabel = '하체 운동';
      else if (workoutPopup.target.desc.includes('심폐') || workoutPopup.target.desc.includes('조깅')) typeLabel = '유산소';
      else if (workoutPopup.target.desc.includes('이완') || workoutPopup.target.desc.includes('요가') || workoutPopup.target.desc.includes('스트레칭')) typeLabel = '스트레칭';

      addWorkout(todayStr, {
        title: workoutPopup.target.name,
        time: workoutPopup.target.duration || '15분',
        level: '초급',
        calories: '150 kcal',
        color: 'from-blue-500 to-indigo-600',
        type: typeLabel
      });
    }
    setWorkoutPopup({ isOpen: false, target: null });
  };

  const confirmDietReplace = () => {
    if (dietPopup.target && dietPopup.mealType) {
      const todayStr = new Date().toISOString().split('T')[0];
      const todayPlan = getPlanByDate(new Date());
      const mealLabel = dietPopup.mealType === 'breakfast' ? '아침' : dietPopup.mealType === 'lunch' ? '점심' : '저녁';
      const existingDiet = todayPlan?.diets.find((d: any) => d.type === mealLabel);

      if (existingDiet && existingDiet.name === dietPopup.target.name) {
        setDietPopup({ isOpen: false, target: null, mealType: null });
        setTimeout(() => setAlertPopup({ isOpen: true, message: '이미 캘린더에 추가된 음식입니다!' }), 100);
        return;
      }

      replaceDiet(todayStr, dietPopup.mealType, {
        name: dietPopup.target.name,
        desc: dietPopup.target.desc,
        kcal: dietPopup.target.calories + ' kcal'
      });
    }
    setDietPopup({ isOpen: false, target: null, mealType: null });
  };

  const addTodo = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTodo.trim()) return;
    setTodos([...todos, { id: Date.now(), text: newTodo, completed: false }]);
    setNewTodo('');
  };

  const toggleTodo = (id: number) => {
    setTodos(todos.map(todo => todo.id === id ? { ...todo, completed: !todo.completed } : todo));
  };

  const deleteTodo = (id: number) => {
    setTodos(todos.filter(todo => todo.id !== id));
  };

  const confirmResetIntake = () => {
    if (!resetConfirmModal.target) return;

    setIntakes(prev => {
      let newIntakes = { ...prev };
      if (resetConfirmModal.target === 'calories') {
        newIntakes.calories = 0;
      } else if (resetConfirmModal.target === 'macros') {
        newIntakes.carbs = 0;
        newIntakes.protein = 0;
        newIntakes.fat = 0;
      }

      const todayStr = new Date().toISOString().split('T')[0];
      localStorage.setItem('healthAppNutrition', JSON.stringify({
        date: todayStr,
        targetKcal: targets.calories,
        consumedKcal: newIntakes.calories,
        targetMacros: targets,
        consumedMacros: {
          carbs: newIntakes.carbs,
          protein: newIntakes.protein,
          fat: newIntakes.fat
        }
      }));

      return newIntakes;
    });

    setResetConfirmModal({ isOpen: false, target: null });
  };

  const handleDietSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualInput.calories && !manualInput.carbs && !manualInput.protein && !manualInput.fat) return;

    const inputCal = Number(manualInput.calories) || 0;
    const inputCarbs = Number(manualInput.carbs) || 0;
    const inputProtein = Number(manualInput.protein) || 0;
    const inputFat = Number(manualInput.fat) || 0;

    if (inputCal > 10000 || inputCarbs > 1000 || inputProtein > 1000 || inputFat > 1000) {
      setAlertPopup({
        isOpen: true,
        message: "입력 가능한 범위를 초과했습니다\n(최대 10,000 kcal 또는 각 1,000g)"
      });
      return;
    }

    setIsAnalyzing(true);
    setDietAnalysis(null);

    // Simulate save/analysis delay
    setTimeout(() => {
      setIntakes(prev => {
        const newIntakes = {
          calories: prev.calories + inputCal,
          carbs: prev.carbs + inputCarbs,
          protein: prev.protein + inputProtein,
          fat: prev.fat + inputFat
        };

        const todayStr = new Date().toISOString().split('T')[0];
        localStorage.setItem('healthAppNutrition', JSON.stringify({
          date: todayStr,
          targetKcal: targets.calories,
          consumedKcal: newIntakes.calories,
          targetMacros: targets,
          consumedMacros: {
            carbs: newIntakes.carbs,
            protein: newIntakes.protein,
            fat: newIntakes.fat
          }
        }));

        return newIntakes;
      });

      setDietAnalysis({
        calories: inputCal,
        carbs: inputCarbs,
        protein: inputProtein,
        fat: inputFat,
        message: '직접 입력한 영양소가 추가되었습니다.'
      });
      setIsAnalyzing(false);
      setManualInput({ calories: '', carbs: '', protein: '', fat: '' });
    }, 600);
  };

  const addWater = (e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (waterGlasses < maxWaterGlasses) {
      const newVal = waterGlasses + 1;
      setWaterGlasses(newVal);
      if (newVal === maxWaterGlasses) {
        setShowWaterGoalAnim(true);
        setTimeout(() => setShowWaterGoalAnim(false), 3000);
      }
    }
  };

  const removeWater = (e: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (waterGlasses > 0) setWaterGlasses(prev => prev - 1);
  };

  useEffect(() => {
    setIsClient(true);
    const token = localStorage.getItem('healthAppToken');
    const stored = localStorage.getItem('healthAppUser');
    
    if (!token || !stored) {
      router.push('/login'); 
    } else {
      const parsedData = JSON.parse(stored);
      setUserData(parsedData);

      const fetchProfile = async () => {
        if (!token) return;
        try {
          const rawApiUrl = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || '';
          const baseUrl = rawApiUrl.endsWith('/') ? rawApiUrl.slice(0, -1) : rawApiUrl;
          const endpoint = baseUrl ? `${baseUrl}/api/v1/users/profile` : '/api/v1/users/profile';
          const res = await fetch(endpoint, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'ngrok-skip-browser-warning': 'true'
            }
          });
          if (res.ok) {
            const freshData = await res.json();
            const newData = { ...parsedData, ...freshData };
            setUserData(newData);
            localStorage.setItem('healthAppUser', JSON.stringify(newData));
          }
        } catch (e) {
          console.error('Failed to sync profile', e);
        }
      };
      fetchProfile();

      // Load persisted nutrition data for today
      const savedNutrition = localStorage.getItem('healthAppNutrition');
      if (savedNutrition) {
        const parsed = JSON.parse(savedNutrition);
        const todayStr = new Date().toISOString().split('T')[0];
        if (parsed.date === todayStr) {
          setIntakes({
            calories: parsed.consumedKcal || 0,
            carbs: parsed.consumedMacros?.carbs || 0,
            protein: parsed.consumedMacros?.protein || 0,
            fat: parsed.consumedMacros?.fat || 0
          });
        }
      }

      if (parsedData.weight && parsedData.height && parsedData.age && parsedData.gender) {
        const w = parseFloat(parsedData.weight);
        const h = parseFloat(parsedData.height); // in cm
        const age = parseInt(parsedData.age, 10);
        const genderDelta = (parsedData.gender === '남성' || parsedData.gender === 'male') ? 5 : -161;

        // Mifflin-St Jeor Equation
        const bmr = 10 * w + 6.25 * h - 5 * age + genderDelta;
        const recCals = Math.round(bmr * 1.375); // Light activity multiplier

        setRecommendedCalories(recCals);

        const initialTargets = {
          calories: recCals,
          carbs: Math.round((recCals * 0.5) / 4),
          protein: Math.round((recCals * 0.3) / 4),
          fat: Math.round((recCals * 0.2) / 9)
        };

        setTargets(initialTargets);
        setGoalInput({
          calories: String(initialTargets.calories),
          carbs: String(initialTargets.carbs),
          protein: String(initialTargets.protein),
          fat: String(initialTargets.fat)
        });
      }
    }
  }, []);

const currentDate = new Date('2026-03-16').toLocaleDateString('ko-KR', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  weekday: 'long',
});

const allergies = userData?.allergies || [];
const conditions = userData?.conditions || [];

return (
  <div className="min-h-screen bg-[#f8fafc] text-gray-900 font-sans p-6 pb-32 md:p-8 lg:p-12 md:pb-36 lg:pb-40">
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <header className="flex justify-between items-start pt-4">
        <div className="flex flex-col space-y-2">
          <p className="text-sm font-semibold text-gray-500 tracking-wide">{currentDate}</p>
          {isClient && userData ? (
            <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}>
              <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">
                <span className="text-[#2563eb]">{userData?.nickname || userData?.name || '사용자'}</span> 님,
              </h1>
              <p className="text-gray-600 text-base font-medium mt-1">오늘은 <span className="text-[#2563eb] font-bold">{userData?.goal || '건강'}</span>을 목표로 달려봐요!</p>
            </motion.div>
          ) : (
            <div className="flex flex-col justify-center h-[76px] space-y-2 animate-pulse">
              <div className="h-8 bg-gray-200 rounded-md w-48"></div>
              <div className="h-4 bg-gray-200 rounded-md w-64"></div>
            </div>
          )}
        </div>
        <button
          onClick={() => setIsPlannerOpen(true)}
          className="px-3 py-3 bg-white rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.06)] border border-gray-100/80 text-[#2563eb] hover:bg-blue-50 hover:-translate-y-1 hover:shadow-[0_12px_40px_rgb(37,99,235,0.12)] transition-all duration-300 flex flex-col items-center justify-center min-w-[76px]"
        >
          <Calendar className="w-6 h-6 mb-1 drop-shadow-sm" />
          <span className="text-[10.5px] font-bold">오늘의 할 일</span>
        </button>
      </header>

      {/* Dashboard Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Intake Calories Card */}
        <div
          onClick={() => setIsCalorieModalOpen(true)}
          className="bg-white p-6 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100/60 flex flex-col justify-between hover:shadow-[0_12px_40px_rgb(249,115,22,0.08)] hover:-translate-y-1 transition-all duration-300 cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="w-11 h-11 rounded-2xl bg-orange-50/80 flex items-center justify-center text-orange-500 shadow-inner group-hover:scale-110 transition-transform">
                <Utensils className="w-5 h-5" />
              </div>
              <h2 className="text-base font-bold text-gray-800 tracking-wide">섭취 칼로리</h2>
            </div>
          </div>
          <div>
            <div className="flex items-baseline space-x-1 truncate max-w-[150px]">
              <p className="text-3xl font-extrabold text-gray-900 tracking-tight truncate min-w-0">{intakes.calories.toLocaleString()}</p>
              <span className="text-sm font-semibold text-gray-400 truncate min-w-0">/ {targets.calories.toLocaleString()} kcal</span>
            </div>
            <div className="flex items-center space-x-1 mt-2.5">
              <div className="w-full bg-gray-100 rounded-full h-1.5 flex-1 max-w-[120px] overflow-hidden">
                <motion.div initial={{ width: 0 }} animate={{ width: `${Math.min((intakes.calories / targets.calories) * 100, 100)}%` }} transition={{ duration: 1, ease: 'easeOut' }} className="bg-orange-500 h-1.5 rounded-full"></motion.div>
              </div>
              <p className="text-sm text-gray-500 font-semibold ml-2">{Math.round(Math.min((intakes.calories / targets.calories) * 100, 100))}%</p>
            </div>
          </div>
        </div>

        {/* Nutrients Card */}
        <div
          onClick={() => setIsNutrientModalOpen(true)}
          className="bg-white p-6 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100/60 flex flex-col justify-between hover:shadow-[0_12px_40px_rgb(16,185,129,0.08)] hover:-translate-y-1 transition-all duration-300 md:col-span-2 lg:col-span-2 cursor-pointer"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-11 h-11 rounded-2xl bg-emerald-50/80 flex items-center justify-center text-emerald-500 shadow-inner">
                <Activity className="w-5 h-5" />
              </div>
              <h2 className="text-base font-bold text-gray-800 tracking-wide">오늘의 영양소 (탄/단/지)</h2>
            </div>
          </div>
          <div className="flex gap-4 items-end justify-between h-full pt-2">
            <div className="flex-1 space-y-1.5 min-w-0">
              <div className="flex justify-between text-[11px] md:text-xs font-bold text-gray-500 whitespace-nowrap">
                <span>탄수화물</span><span className="truncate ml-1">{intakes.carbs.toLocaleString()}/{targets.carbs.toLocaleString()}g</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                <motion.div initial={{ width: 0 }} animate={{ width: `${Math.min((intakes.carbs / targets.carbs) * 100, 100)}%` }} transition={{ duration: 1 }} className="bg-amber-400 h-2 rounded-full"></motion.div>
              </div>
            </div>
            <div className="flex-1 space-y-1.5 min-w-0">
              <div className="flex justify-between text-[11px] md:text-xs font-bold text-gray-500 whitespace-nowrap">
                <span>단백질</span><span className="truncate ml-1">{intakes.protein.toLocaleString()}/{targets.protein.toLocaleString()}g</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                <motion.div initial={{ width: 0 }} animate={{ width: `${Math.min((intakes.protein / targets.protein) * 100, 100)}%` }} transition={{ duration: 1, delay: 0.1 }} className="bg-blue-400 h-2 rounded-full"></motion.div>
              </div>
            </div>
            <div className="flex-1 space-y-1.5 min-w-0">
              <div className="flex justify-between text-[11px] md:text-xs font-bold text-gray-500 whitespace-nowrap">
                <span>지방</span><span className="truncate ml-1">{intakes.fat.toLocaleString()}/{targets.fat.toLocaleString()}g</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                <motion.div initial={{ width: 0 }} animate={{ width: `${Math.min((intakes.fat / targets.fat) * 100, 100)}%` }} transition={{ duration: 1, delay: 0.2 }} className="bg-rose-400 h-2 rounded-full"></motion.div>
              </div>
            </div>
          </div>
        </div>

        {/* Hydration Tracker Card (NEW) */}
        <div
          onClick={() => { }}
          className="col-span-1 md:col-span-2 lg:col-span-1 bg-white p-6 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100/60 flex flex-col justify-between group hover:shadow-[0_12px_40px_rgb(14,165,233,0.12)] hover:-translate-y-1 transition-all duration-300 relative overflow-hidden"
        >
          {/* Animated background water fill level */}
          <motion.div
            className="absolute bottom-0 left-0 right-0 bg-sky-50/50 z-0"
            animate={{ height: `${(waterGlasses / maxWaterGlasses) * 100}%` }}
            transition={{ type: "spring", stiffness: 60, damping: 15 }}
          />

          {/* Goal Achieved Animation */}
          <AnimatePresence>
            {showWaterGoalAnim && (
              <>
                <motion.div
                  initial={{ y: 20, opacity: 0, scale: 0.5 }}
                  animate={{ y: -40, opacity: 1, scale: 1.2 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                  className="absolute top-4 left-1/2 -translate-x-1/2 z-20 flex space-x-1"
                >
                  <Droplets className="w-5 h-5 text-blue-500 drop-shadow-sm" />
                  <Droplets className="w-6 h-6 text-sky-400 -mt-2 drop-shadow-sm" />
                  <Droplets className="w-5 h-5 text-blue-500 drop-shadow-sm" />
                </motion.div>
                <motion.div
                  initial={{ y: 30, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ delay: 0.2, duration: 0.5 }}
                  className="absolute top-[80px] left-1/2 -translate-x-1/2 z-20 bg-blue-500 text-white text-[11px] font-bold px-3 py-1.5 rounded-full whitespace-nowrap shadow-md"
                >
                  오늘의 목표 달성! 🎉
                </motion.div>
              </>
            )}
          </AnimatePresence>

          <div className="flex items-center justify-between mb-4 z-10 relative">
            <div className="flex items-center space-x-3">
              <div className="w-11 h-11 rounded-2xl bg-sky-100/80 flex items-center justify-center text-sky-500 shadow-inner group-hover:scale-110 transition-transform">
                <Droplets className="w-5 h-5" />
              </div>
              <h2 className="text-base font-bold text-gray-800 tracking-wide">수분 섭취</h2>
            </div>
          </div>

          <div className="z-10 relative mt-2">
            <div className="flex items-center justify-between">
              <div className="flex items-baseline space-x-1">
                <motion.p
                  key={waterGlasses}
                  initial={{ scale: 1.5, opacity: 0, color: '#38bdf8' }}
                  animate={{ scale: 1, opacity: 1, color: '#111827' }}
                  className="text-3xl font-extrabold tracking-tight"
                >
                  {waterGlasses}
                </motion.p>
                <span className="text-sm font-semibold text-gray-400">/ {maxWaterGlasses} 잔</span>
              </div>
              <div className="flex items-center space-x-2">
                <button onClick={removeWater} className="w-8 h-8 rounded-full bg-sky-100 flex items-center justify-center text-sky-500 hover:bg-sky-500 hover:text-white transition-colors cursor-pointer disabled:opacity-50" disabled={waterGlasses === 0}>
                  <span className="text-xl font-bold leading-none mb-0.5">-</span>
                </button>
                <button onClick={addWater} className="w-8 h-8 rounded-full bg-sky-100 flex items-center justify-center text-sky-500 hover:bg-sky-500 hover:text-white transition-colors cursor-pointer disabled:opacity-50" disabled={waterGlasses === maxWaterGlasses}>
                  <Plus className="w-4 h-4 text-inherit" />
                </button>
              </div>
            </div>
            <p className="text-xs text-sky-600 font-semibold mt-3 text-center opacity-0 group-hover:opacity-100 transition-opacity">
              오늘도 충분한 수분을 섭취하세요!
            </p>
          </div>
        </div>
      </div>

      {/* Quick Actions (NEW) */}
      <div className="pt-2 pb-4">
        <p className="text-sm font-bold text-gray-500 mb-4 px-1">빠른 실행</p>
        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => router.push('/recommend')}
            className="group bg-gradient-to-r from-[#2563eb] to-blue-500 p-5 rounded-3xl shadow-[0_8px_30px_rgb(37,99,235,0.25)] hover:shadow-[0_12px_40px_rgb(37,99,235,0.35)] hover:-translate-y-1 transition-all duration-300 flex items-center justify-between text-left overflow-hidden relative"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-2xl -mr-10 -mt-10 group-hover:scale-110 transition-transform"></div>
            <div className="relative z-10">
              <h3 className="text-white font-bold text-lg mb-1">오늘 운동 추천</h3>
              <p className="text-blue-100 text-xs font-medium">AI가 분석한 맞춤형 플랜</p>
            </div>
            <div className="w-10 h-10 bg-white/20 backdrop-blur-md rounded-2xl flex items-center justify-center text-white relative z-10">
              <Activity className="w-5 h-5" />
            </div>
          </button>
          <button
            onClick={() => setIsDietModalOpen(true)}
            className="group bg-white p-5 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.06)] border border-gray-100/80 hover:shadow-[0_12px_40px_rgb(0,0,0,0.1)] hover:-translate-y-1 transition-all duration-300 flex items-center justify-between text-left"
          >
            <div>
              <h3 className="text-gray-900 font-bold text-lg mb-1">간편 영양 기록</h3>
              <p className="text-gray-400 text-xs font-medium">칼로리 관리의 시작</p>
            </div>
            <div className="w-10 h-10 bg-gray-50 rounded-2xl flex items-center justify-center text-gray-500 group-hover:bg-orange-50 group-hover:text-orange-500 transition-colors">
              <Utensils className="w-5 h-5" />
            </div>
          </button>
        </div>
      </div>

      {/* AI Recommended Section */}
      <section className="mt-4 mb-10 space-y-6">
        {/* Workout Recommendation Grid */}
        <div className="bg-white p-6 md:p-8 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100/60">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-bold text-gray-900 tracking-wide flex items-center">
              <span className="bg-gradient-to-r from-[#2563eb] to-indigo-500 text-transparent bg-clip-text mr-2">AI 운동 추천</span>
            </h2>
            <button className="text-gray-400 hover:text-[#2563eb] hover:bg-blue-50 transition-all p-2 rounded-full cursor-pointer group focus:outline-none">
              <RefreshCw className="w-5 h-5 group-hover:rotate-180 transition-transform duration-500" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Strength Upper */}
            <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm hover:shadow-[0_8px_24px_rgba(37,99,235,0.1)] transition-all flex flex-col relative group">
              <div className="flex justify-between items-start mb-4">
                <span className="px-2.5 py-1 bg-blue-50 border border-blue-100 text-blue-600 rounded-full text-xs font-bold shadow-sm">근력 (상체)</span>
                {aiRecommendations.workout?.strength?.upper && (
                  <button onClick={() => handleWorkoutAddClick(aiRecommendations.workout.strength.upper)} className="p-1.5 bg-blue-500 shadow-md text-white hover:bg-blue-600 rounded-full transition-colors z-10">
                    <Plus className="w-4 h-4" />
                  </button>
                )}
              </div>
              {aiRecommendations.workout?.strength?.upper ? (
                <div className="flex-1 flex flex-col">
                  <div className="w-14 h-14 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full mb-4 flex items-center justify-center text-blue-600 shadow-inner">
                    <Dumbbell className="w-7 h-7" />
                  </div>
                  <h4 className="font-bold text-gray-900 text-[15px] mb-1.5">{aiRecommendations.workout.strength.upper.name}</h4>
                  <p className="text-xs text-gray-500 leading-relaxed">{aiRecommendations.workout.strength.upper.desc}</p>
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center text-xs text-gray-400">추천 항목 없음</div>
              )}
            </div>

            {/* Strength Lower */}
            <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm hover:shadow-[0_8px_24px_rgba(37,99,235,0.1)] transition-all flex flex-col relative group">
              <div className="flex justify-between items-start mb-4">
                <span className="px-2.5 py-1 bg-indigo-50 border border-indigo-100 text-indigo-600 rounded-full text-xs font-bold shadow-sm">근력 (하체)</span>
                {aiRecommendations.workout?.strength?.lower && (
                  <button onClick={() => handleWorkoutAddClick(aiRecommendations.workout.strength.lower)} className="p-1.5 bg-indigo-500 shadow-md text-white hover:bg-indigo-600 rounded-full transition-colors z-10">
                    <Plus className="w-4 h-4" />
                  </button>
                )}
              </div>
              {aiRecommendations.workout?.strength?.lower ? (
                <div className="flex-1 flex flex-col">
                  <div className="w-14 h-14 bg-gradient-to-br from-indigo-100 to-indigo-200 rounded-full mb-4 flex items-center justify-center text-indigo-600 shadow-inner">
                    <PersonStanding className="w-7 h-7" />
                  </div>
                  <h4 className="font-bold text-gray-900 text-[15px] mb-1.5">{aiRecommendations.workout.strength.lower.name}</h4>
                  <p className="text-xs text-gray-500 leading-relaxed">{aiRecommendations.workout.strength.lower.desc}</p>
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center text-xs text-gray-400">추천 항목 없음</div>
              )}
            </div>

            {/* Cardio */}
            <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm hover:shadow-[0_8px_24px_rgba(244,63,94,0.15)] transition-all flex flex-col relative group">
              <div className="flex justify-between items-start mb-4">
                <span className="px-2.5 py-1 bg-rose-50 border border-rose-100 text-rose-500 rounded-full text-xs font-bold shadow-sm">유산소</span>
                {aiRecommendations.workout?.cardio && (
                  <button onClick={() => handleWorkoutAddClick(aiRecommendations.workout.cardio)} className="p-1.5 bg-rose-500 shadow-md text-white hover:bg-rose-600 rounded-full transition-colors z-10">
                    <Plus className="w-4 h-4" />
                  </button>
                )}
              </div>
              {aiRecommendations.workout?.cardio ? (
                <div className="flex-1 flex flex-col">
                  <div className="w-14 h-14 bg-gradient-to-br from-rose-100 to-rose-200 rounded-full mb-4 flex items-center justify-center text-rose-500 shadow-inner">
                    <Heart className="w-7 h-7" />
                  </div>
                  <h4 className="font-bold text-gray-900 text-[15px] mb-1.5">{aiRecommendations.workout.cardio.name}</h4>
                  <p className="text-xs text-gray-500 leading-relaxed">{aiRecommendations.workout.cardio.desc}</p>
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center text-xs text-gray-400">추천 항목 없음</div>
              )}
            </div>

            {/* Stretching */}
            <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm hover:shadow-[0_8px_24px_rgba(16,185,129,0.15)] transition-all flex flex-col relative group">
              <div className="flex justify-between items-start mb-4">
                <span className="px-2.5 py-1 bg-emerald-50 border border-emerald-100 text-emerald-500 rounded-full text-xs font-bold shadow-sm">스트레칭</span>
                {aiRecommendations.workout?.stretching && (
                  <button onClick={() => handleWorkoutAddClick(aiRecommendations.workout.stretching)} className="p-1.5 bg-emerald-500 shadow-md text-white hover:bg-emerald-600 rounded-full transition-colors z-10">
                    <Plus className="w-4 h-4" />
                  </button>
                )}
              </div>
              {aiRecommendations.workout?.stretching ? (
                <div className="flex-1 flex flex-col">
                  <div className="w-14 h-14 bg-gradient-to-br from-emerald-100 to-emerald-200 rounded-full mb-4 flex items-center justify-center text-emerald-500 shadow-inner">
                    <Droplets className="w-7 h-7" />
                  </div>
                  <h4 className="font-bold text-gray-900 text-[15px] mb-1.5">{aiRecommendations.workout.stretching.name}</h4>
                  <p className="text-xs text-gray-500 leading-relaxed">{aiRecommendations.workout.stretching.desc}</p>
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center text-xs text-gray-400">추천 항목 없음</div>
              )}
            </div>
          </div>
        </div>

        {/* Diet Recommendation Grid */}
        <div className="bg-white p-6 md:p-8 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100/60">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-bold text-gray-900 tracking-wide flex items-center">
              <span className="bg-gradient-to-r from-[#f59e0b] to-orange-500 text-transparent bg-clip-text mr-2">AI 식단 추천</span>
            </h2>
            <button className="text-gray-400 hover:text-orange-500 hover:bg-orange-50 transition-all p-2 rounded-full cursor-pointer group focus:outline-none">
              <RefreshCw className="w-5 h-5 group-hover:rotate-180 transition-transform duration-500" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {['breakfast', 'lunch', 'dinner'].map((mealType) => {
              const dietData = aiRecommendations.diet[mealType as 'breakfast' | 'lunch' | 'dinner'];
              const mealLabel = mealType === 'breakfast' ? '아침' : mealType === 'lunch' ? '점심' : '저녁';
              return (
                <div key={mealType} className="bg-orange-50/30 rounded-2xl p-4 border border-orange-100/50 relative group flex flex-col">
                  <div className="flex justify-between items-center mb-3">
                    <span className="px-2.5 py-1 bg-orange-50 border border-orange-100 text-orange-600 rounded-full text-xs font-bold shadow-sm">{mealLabel}</span>
                    {dietData && (
                      <button onClick={() => handleDietReplaceClick(dietData, mealType as 'breakfast' | 'lunch' | 'dinner')} className="p-1.5 bg-orange-500 shadow-md text-white hover:bg-orange-600 rounded-full transition-colors z-10">
                        <Plus className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                  {dietData ? (
                    <div className="flex-1 flex flex-col">
                      <div className="w-full h-24 bg-orange-50/50 border border-orange-100 shadow-sm rounded-xl mb-3 flex items-center justify-center">
                        <span className="text-4xl">{getFoodEmoji(dietData.name)}</span>
                      </div>
                      <h4 className="font-bold text-gray-900 text-sm mb-1">{dietData.name}</h4>
                      <p className="text-xs text-gray-500 mb-2 flex-1">{dietData.desc}</p>
                      <div className="text-xs font-bold text-orange-500">{dietData.calories} kcal</div>
                    </div>
                  ) : (
                    <div className="flex-1 flex items-center justify-center min-h-[120px] text-xs text-gray-400">추천 식단 없음</div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </section>
    </div>

    {/* Workout Add Popup */}
    <AnimatePresence>
      {workoutPopup.isOpen && workoutPopup.target && (
        <div className="fixed inset-0 z-[110] flex items-center justify-center p-4">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-gray-900/40 backdrop-blur-sm" onClick={() => setWorkoutPopup({ isOpen: false, target: null })} />
          <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }} className="bg-white rounded-3xl shadow-xl w-full max-w-sm overflow-hidden z-10">
            <div className="p-6 text-center">
              <div className="w-14 h-14 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <Calendar className="w-7 h-7" />
              </div>
              <h3 className="font-bold text-lg text-gray-900 mb-2">일정 추가</h3>
              <p className="text-sm text-gray-600 mb-6">
                <strong className="text-blue-600">{workoutPopup.target.name}</strong> 운동을<br />
                오늘의 캘린더 일정에 추가하시겠어요?
              </p>
              <div className="flex space-x-3">
                <button onClick={() => setWorkoutPopup({ isOpen: false, target: null })} className="flex-1 py-3 bg-gray-100 text-gray-700 font-bold rounded-xl hover:bg-gray-200 transition-colors">취소</button>
                <button onClick={confirmWorkoutAdd} className="flex-1 py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition-colors shadow-md">추가하기</button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>

    {/* Diet Replace Popup */}
    <AnimatePresence>
      {dietPopup.isOpen && dietPopup.target && dietPopup.mealType && (
        <div className="fixed inset-0 z-[110] flex items-center justify-center p-4">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-gray-900/40 backdrop-blur-sm" onClick={() => setDietPopup({ isOpen: false, target: null, mealType: null })} />
          <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }} className="bg-white rounded-3xl shadow-xl w-full max-w-md overflow-hidden z-10">
            <div className="p-6">
              <h3 className="font-bold text-lg text-gray-900 mb-1 text-center">식단 교체</h3>
              <p className="text-sm text-gray-500 mb-6 text-center">이 식단을 오늘의 캘린더 일정에 반영하시겠습니까?</p>

              <div className="flex items-center justify-between bg-gray-50 rounded-2xl p-4 mb-6 relative">
                {/* Old Diet */}
                <div className="flex-1 text-center max-w-[45%]">
                  <span className="text-[10px] font-bold text-gray-400 block mb-2">기존 식단</span>
                  {(() => {
                    const todayPlan = getPlanByDate(new Date());
                    const mealLabel = dietPopup.mealType === 'breakfast' ? '아침' : dietPopup.mealType === 'lunch' ? '점심' : '저녁';
                    const oldDiet = todayPlan?.diets.find(d => d.type === mealLabel);

                    if (oldDiet) {
                      return (
                        <div>
                          <div className="w-12 h-12 bg-white border border-gray-200 rounded-lg mx-auto mb-2 flex items-center justify-center text-gray-400 shadow-sm text-2xl">{getFoodEmoji(oldDiet.name)}</div>
                          <p className="text-xs font-bold text-gray-700 truncate px-1">{oldDiet.name}</p>
                          <p className="text-[10px] text-gray-500">{oldDiet.kcal}</p>
                        </div>
                      );
                    }
                    return (
                      <div className="flex flex-col items-center justify-center h-full min-h-[80px]">
                        <p className="text-xs text-gray-400 font-medium">비어 있음</p>
                      </div>
                    );
                  })()}
                </div>

                {/* Arrow */}
                <div className="px-1 text-gray-300">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                </div>

                {/* New Diet */}
                <div className="flex-1 text-center max-w-[45%]">
                  <span className="text-[10px] font-bold text-orange-500 block mb-2">새로운 추천 식단</span>
                  <div>
                    <div className="w-12 h-12 bg-orange-50 border border-orange-100 text-orange-400 rounded-lg mx-auto mb-2 flex items-center justify-center shadow-sm text-2xl">{getFoodEmoji(dietPopup.target.name)}</div>
                    <p className="text-xs font-bold text-orange-600 truncate px-1">{dietPopup.target.name}</p>
                    <p className="text-[10px] text-orange-400 font-bold">{dietPopup.target.calories} kcal</p>
                  </div>
                </div>
              </div>

              <div className="flex space-x-3">
                <button onClick={() => setDietPopup({ isOpen: false, target: null, mealType: null })} className="flex-1 py-3 bg-gray-100 text-gray-700 font-bold rounded-xl hover:bg-gray-200 transition-colors">취소</button>
                <button onClick={confirmDietReplace} className="flex-1 py-3 bg-orange-500 text-white font-bold rounded-xl hover:bg-orange-600 transition-colors shadow-md">변경하기</button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>

    {/* Planner Modal */}
    <AnimatePresence>
      {isPlannerOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="absolute inset-0 bg-gray-900/40 backdrop-blur-sm" onClick={() => setIsPlannerOpen(false)}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="bg-white rounded-3xl shadow-[0_20px_60px_-12px_rgba(0,0,0,0.15)] w-full max-w-sm overflow-hidden z-10"
          >
            <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-blue-50/50">
              <div className="flex items-center space-x-2">
                <CheckSquare className="w-5 h-5 text-[#2563eb]" />
                <h3 className="font-bold text-lg text-gray-900">오늘 할 일</h3>
              </div>
              <button onClick={() => setIsPlannerOpen(false)} className="text-gray-400 hover:text-gray-600 transition-colors p-1 bg-white rounded-full shadow-sm">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              <div className="space-y-3 max-h-[300px] overflow-y-auto mb-6 pr-1 custom-scrollbar">
                {todos.length === 0 ? (
                  <p className="text-center text-gray-400 py-4 text-sm font-medium">오늘은 어떤 운동을 해볼까요?</p>
                ) : (
                  todos.map(todo => (
                    <div key={todo.id} className={`flex items-center justify-between p-3 rounded-xl border transition-all duration-200 ${todo.completed ? 'bg-gray-50 border-gray-100' : 'bg-white border-blue-100 shadow-[0_2px_8px_-4px_rgba(37,99,235,0.1)]'}`}>
                      <div className="flex items-center space-x-3 cursor-pointer select-none flex-1" onClick={() => toggleTodo(todo.id)}>
                        <div className={`w-5 h-5 rounded flex items-center justify-center border transition-colors ${todo.completed ? 'bg-[#2563eb] border-[#2563eb] text-white' : 'border-gray-300 bg-white'}`}>
                          {todo.completed && <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
                        </div>
                        <span className={`text-sm font-medium transition-all ${todo.completed ? 'line-through text-gray-400' : 'text-gray-700'}`}>
                          {todo.text}
                          {todo.calories && <span className="ml-1.5 text-[10px] text-orange-400 bg-orange-50 px-1.5 py-0.5 rounded-md font-bold">{todo.calories} kcal</span>}
                          {todo.type === 'workout' && <span className="ml-1.5 text-[10px] text-blue-500 bg-blue-50 px-1.5 py-0.5 rounded-md font-bold">운동</span>}
                        </span>
                      </div>
                      <button onClick={() => deleteTodo(todo.id)} className="text-gray-300 hover:text-red-500 transition-colors p-1.5 focus:outline-none ml-2">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))
                )}
              </div>

              <form onSubmit={addTodo} className="flex gap-2 relative">
                <input
                  type="text"
                  value={newTodo}
                  onChange={(e) => setNewTodo(e.target.value)}
                  placeholder="새로운 할 일 추가"
                  className="flex-1 bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#2563eb]/20 focus:border-[#2563eb] transition-all"
                />
                <button
                  type="submit"
                  disabled={!newTodo.trim()}
                  className="bg-[#2563eb] text-white p-3 rounded-xl shadow-[0_4px_12px_rgba(37,99,235,0.2)] hover:bg-blue-700 hover:shadow-[0_6px_16px_rgba(37,99,235,0.3)] transition-all disabled:opacity-50 disabled:shadow-none focus:outline-none"
                >
                  <Plus className="w-5 h-5" />
                </button>
              </form>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>

    {/* Diet Modal */}
    <AnimatePresence>
      {isDietModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="absolute inset-0 bg-gray-900/40 backdrop-blur-sm" onClick={() => setIsDietModalOpen(false)}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="bg-white rounded-3xl shadow-[0_20px_60px_-12px_rgba(0,0,0,0.15)] w-full max-w-sm overflow-hidden z-10"
          >
            <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-blue-50/50">
              <div className="flex items-center space-x-2">
                <Utensils className="w-5 h-5 text-[#2563eb]" />
                <h3 className="font-bold text-lg text-gray-900">식단 기록하기</h3>
              </div>
              <button onClick={() => { setIsDietModalOpen(false); setTimeout(() => { setDietAnalysis(null); setManualInput({ calories: '', carbs: '', protein: '', fat: '' }); }, 300); }} className="text-gray-400 hover:text-gray-600 transition-colors p-1 bg-white rounded-full shadow-sm">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              <form onSubmit={handleDietSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <div className="flex justify-between items-center mb-2">
                      <label className="block text-sm font-bold text-gray-700">섭취 칼로리 (kcal)</label>
                      <button type="button" onClick={() => setResetConfirmModal({ isOpen: true, target: 'calories' })} className="text-[11px] text-gray-400 hover:text-red-500 transition-colors bg-gray-100 hover:bg-red-50 px-2 py-1 rounded-md font-bold">오늘 섭취량 초기화</button>
                    </div>
                    <input
                      type="number"
                      value={manualInput.calories}
                      onChange={(e) => setManualInput({ ...manualInput, calories: e.target.value })}
                      placeholder="예) 500"
                      className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#2563eb]/20 focus:border-[#2563eb] transition-all"
                    />
                  </div>
                  <div className="col-span-2 flex justify-between items-end mt-1 -mb-2">
                    <label className="block text-sm font-bold text-gray-700">상세 영양소 (g)</label>
                    <button type="button" onClick={() => setResetConfirmModal({ isOpen: true, target: 'macros' })} className="text-[11px] text-gray-400 hover:text-red-500 transition-colors bg-gray-100 hover:bg-red-50 px-2 py-1 rounded-md font-bold">오늘 섭취량 초기화</button>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">탄수화물 (g)</label>
                    <input
                      type="number"
                      value={manualInput.carbs}
                      onChange={(e) => setManualInput({ ...manualInput, carbs: e.target.value })}
                      placeholder="0"
                      className="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#2563eb]/20 focus:border-[#2563eb] transition-all text-center"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">단백질 (g)</label>
                    <input
                      type="number"
                      value={manualInput.protein}
                      onChange={(e) => setManualInput({ ...manualInput, protein: e.target.value })}
                      placeholder="0"
                      className="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#2563eb]/20 focus:border-[#2563eb] transition-all text-center"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-xs font-bold text-gray-700 mb-1">지방 (g)</label>
                    <input
                      type="number"
                      value={manualInput.fat}
                      onChange={(e) => setManualInput({ ...manualInput, fat: e.target.value })}
                      placeholder="0"
                      className="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#2563eb]/20 focus:border-[#2563eb] transition-all text-center"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={(!manualInput.calories && !manualInput.carbs && !manualInput.protein && !manualInput.fat) || isAnalyzing}
                  className="w-full bg-[#2563eb] text-white font-bold py-3.5 rounded-xl shadow-[0_4px_12px_rgba(37,99,235,0.2)] hover:bg-blue-700 transition-all disabled:opacity-50 disabled:shadow-none flex justify-center items-center h-[52px]"
                >
                  {isAnalyzing ? (
                    <div className="flex space-x-2 items-center">
                      <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      <span className="ml-2">저장 중...</span>
                    </div>
                  ) : (
                    '영양소 기록하기'
                  )}
                </button>
              </form>

              <AnimatePresence>
                {dietAnalysis && (
                  <motion.div
                    initial={{ opacity: 0, height: 0, marginTop: 0 }}
                    animate={{ opacity: 1, height: 'auto', marginTop: 24 }}
                    exit={{ opacity: 0, height: 0, marginTop: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="bg-blue-50/50 border border-blue-100 rounded-2xl p-5 space-y-3 relative overflow-hidden">
                      <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 rounded-full blur-xl -mr-10 -mt-10"></div>
                      <div className="flex justify-between items-center relative z-10">
                        <span className="text-sm font-bold text-gray-600">추가된 칼로리</span>
                        <span className="text-lg font-extrabold text-[#2563eb]">{dietAnalysis.calories} kcal</span>
                      </div>
                      <div className="flex justify-between items-center relative z-10 text-xs font-medium text-gray-500">
                        <span>탄 {dietAnalysis.carbs}g • 단 {dietAnalysis.protein}g • 지 {dietAnalysis.fat}g</span>
                      </div>
                      <div className="h-px w-full bg-blue-100/50 relative z-10"></div>
                      <div className="pt-1">
                        <span className="inline-block px-2 py-1 bg-blue-100 text-blue-700 text-[10px] font-bold rounded-md mb-2 relative z-10">AI의 한 줄 조언</span>
                        <div className="flex items-start space-x-2.5 relative z-10">
                          <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                            <span className="text-[10px]">🤖</span>
                          </div>
                          <p className="text-sm text-gray-700 leading-relaxed font-medium">
                            {dietAnalysis.message}
                          </p>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>

    {/* Calorie Goal Modal */}
    <AnimatePresence>
      {isCalorieModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="absolute inset-0 bg-gray-900/40 backdrop-blur-sm" onClick={() => setIsCalorieModalOpen(false)}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="bg-white rounded-3xl shadow-[0_20px_60px_-12px_rgba(0,0,0,0.15)] w-full max-w-sm overflow-hidden z-10"
          >
            <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-blue-50/50">
              <div className="flex items-center space-x-2">
                <Utensils className="w-5 h-5 text-[#2563eb]" />
                <h3 className="font-bold text-lg text-gray-900">목표 칼로리 설정</h3>
              </div>
              <button onClick={() => { setIsCalorieModalOpen(false); setGoalErrorMsg(''); }} className="text-gray-400 hover:text-gray-600 transition-colors p-1 bg-white rounded-full shadow-sm">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              <form onSubmit={handleCalorieSubmit} className="space-y-4">
                <div className="bg-blue-50 text-blue-800 p-3 rounded-xl text-sm mb-4 border border-blue-100 font-medium text-center">
                  💡 체형 맞춤형 권장 섭취량: <br /> 하루 <span className="font-bold text-blue-600">{recommendedCalories} kcal</span>
                </div>
                <div>
                  <label className="block text-sm font-bold text-gray-700 mb-1.5">하루 목표 칼로리 (kcal)</label>
                  <input
                    type="number"
                    value={goalInput.calories}
                    onChange={(e) => setGoalInput({ ...goalInput, calories: e.target.value })}
                    placeholder="예) 2000"
                    className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#2563eb]/20 focus:border-[#2563eb] transition-all"
                  />
                </div>

                {goalErrorMsg && (
                  <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-500 text-xs font-bold text-center mt-2">
                    {goalErrorMsg}
                  </motion.p>
                )}

                <button
                  type="submit"
                  disabled={isGoalSaving}
                  className="w-full bg-[#2563eb] text-white font-bold py-3.5 rounded-xl shadow-[0_4px_12px_rgba(37,99,235,0.2)] hover:bg-blue-700 transition-all disabled:opacity-50 disabled:shadow-none mt-2"
                >
                  {isGoalSaving ? '저장 중...' : '목표 저장'}
                </button>
              </form>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>

    {/* Nutrient Goal Modal */}
    <AnimatePresence>
      {isNutrientModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="absolute inset-0 bg-gray-900/40 backdrop-blur-sm" onClick={() => setIsNutrientModalOpen(false)}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="bg-white rounded-3xl shadow-[0_20px_60px_-12px_rgba(0,0,0,0.15)] w-full max-w-sm overflow-hidden z-10"
          >
            <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-blue-50/50">
              <div className="flex items-center space-x-2">
                <Activity className="w-5 h-5 text-[#2563eb]" />
                <h3 className="font-bold text-lg text-gray-900">목표 영양소 설정</h3>
              </div>
              <button onClick={() => { setIsNutrientModalOpen(false); setGoalErrorMsg(''); }} className="text-gray-400 hover:text-gray-600 transition-colors p-1 bg-white rounded-full shadow-sm">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              <form onSubmit={handleNutrientSubmit} className="space-y-4">
                <div className="bg-emerald-50 text-emerald-800 p-3 rounded-xl text-sm mb-4 border border-emerald-100 font-medium text-center">
                  💡 체형 맞춤형 권장 탄단지 (5:3:2) <br />
                  <span className="font-bold">탄 {Math.round((recommendedCalories * 0.5) / 4)}g / 단 {Math.round((recommendedCalories * 0.3) / 4)}g / 지 {Math.round((recommendedCalories * 0.2) / 9)}g</span>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">탄수화물 (g)</label>
                    <input
                      type="number"
                      value={goalInput.carbs}
                      onChange={(e) => setGoalInput({ ...goalInput, carbs: e.target.value })}
                      className="w-full bg-gray-50 border border-gray-200 rounded-xl px-2 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#2563eb]/20 focus:border-[#2563eb] transition-all text-center"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">단백질 (g)</label>
                    <input
                      type="number"
                      value={goalInput.protein}
                      onChange={(e) => setGoalInput({ ...goalInput, protein: e.target.value })}
                      className="w-full bg-gray-50 border border-gray-200 rounded-xl px-2 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#2563eb]/20 focus:border-[#2563eb] transition-all text-center"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">지방 (g)</label>
                    <input
                      type="number"
                      value={goalInput.fat}
                      onChange={(e) => setGoalInput({ ...goalInput, fat: e.target.value })}
                      className="w-full bg-gray-50 border border-gray-200 rounded-xl px-2 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#2563eb]/20 focus:border-[#2563eb] transition-all text-center"
                    />
                  </div>
                </div>

                {goalErrorMsg && (
                  <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-500 text-xs font-bold text-center mt-2">
                    {goalErrorMsg}
                  </motion.p>
                )}

                <button
                  type="submit"
                  disabled={isGoalSaving}
                  className="w-full bg-[#2563eb] text-white font-bold py-3.5 rounded-xl shadow-[0_4px_12px_rgba(37,99,235,0.2)] hover:bg-blue-700 transition-all disabled:opacity-50 disabled:shadow-none mt-2"
                >
                  {isGoalSaving ? '저장 중...' : '목표 저장'}
                </button>
              </form>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
    {/* Alert Popup */}
    <AnimatePresence>
      {alertPopup.isOpen && (
        <div className="fixed inset-0 z-[120] flex items-center justify-center p-4">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-gray-900/40 backdrop-blur-sm" onClick={() => setAlertPopup({ isOpen: false, message: '' })} />
          <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }} className="bg-white rounded-3xl shadow-xl w-full max-w-sm overflow-hidden z-10 px-6 py-8 text-center">
            <div className="w-16 h-16 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <Info className="w-8 h-8" />
            </div>
            <h3 className="font-bold text-lg text-gray-900 mb-2">알림</h3>
            <p className="text-gray-600 mb-6 font-medium">{alertPopup.message}</p>
            <button onClick={() => setAlertPopup({ isOpen: false, message: '' })} className="w-full py-3.5 bg-[#2563eb] text-white font-bold rounded-xl hover:bg-blue-700 transition-colors shadow-md">
              확인
            </button>
          </motion.div>
        </div>
      )}
    </AnimatePresence>

    {/* Reset Confirmation Modal */}
    <AnimatePresence>
      {resetConfirmModal.isOpen && (
        <div className="fixed inset-0 z-[130] flex items-center justify-center p-4">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-gray-900/40 backdrop-blur-sm" onClick={() => setResetConfirmModal({ isOpen: false, target: null })} />
          <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }} className="bg-white rounded-3xl shadow-xl w-full max-w-sm overflow-hidden z-10 px-6 py-8 text-center border border-gray-100">
            <div className="w-16 h-16 bg-red-50 text-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <RefreshCw className="w-8 h-8" />
            </div>
            <h3 className="font-bold text-lg text-gray-900 mb-2">섭취량 초기화</h3>
            <p className="text-gray-500 mb-6 font-medium text-sm">
              정말 오늘 기록을 초기화할까요?<br />
              진행 중인 {resetConfirmModal.target === 'calories' ? '칼로리' : '영양소(탄단지)'} 기록이 0으로 변경됩니다.
            </p>
            <div className="flex gap-3">
              <button onClick={() => setResetConfirmModal({ isOpen: false, target: null })} className="flex-1 py-3.5 bg-gray-100 text-gray-600 font-bold rounded-xl hover:bg-gray-200 transition-colors">
                취소
              </button>
              <button onClick={confirmResetIntake} className="flex-1 py-3.5 bg-red-500 text-white font-bold rounded-xl hover:bg-red-600 transition-colors shadow-[0_4px_12px_rgba(239,68,68,0.3)]">
                확인 (초기화)
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  </div>
);
}
