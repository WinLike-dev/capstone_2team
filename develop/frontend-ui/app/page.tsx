/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Calendar, CheckSquare, Plus, Trash2, X, Droplets, Utensils, Activity, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Home() {
  const router = useRouter();
  const [userData, setUserData] = useState<{name: string, goal: string, allergies?: string[], conditions?: string[]} | null>(null);
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

  // Current Intakes (mock for UI)
  const [intakes] = useState({
    calories: 420,
    carbs: 120,
    protein: 45,
    fat: 30
  });

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
  const [foodInput, setFoodInput] = useState('');
  const [dietAnalysis, setDietAnalysis] = useState<{ calories: string, message: string } | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Water tracker state (glasses of water)
  const [waterGlasses, setWaterGlasses] = useState(2);
  const maxWaterGlasses = 8;
  const [showWaterGoalAnim, setShowWaterGoalAnim] = useState(false);

  const [todos, setTodos] = useState<{id: number, text: string, completed: boolean}[]>([
    { id: 1, text: '아침 스트레칭 10분', completed: false },
    { id: 2, text: '비타민 챙겨먹기', completed: false }
  ]);
  const [newTodo, setNewTodo] = useState('');

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

  const handleDietSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!foodInput.trim()) return;
    
    setIsAnalyzing(true);
    setTimeout(() => {
      let mockResult = { calories: '320 kcal', message: '적당한 칼로리네요. 든든한 식사 되세요!' };
      
      if (foodInput.includes('떡볶이') || foodInput.includes('마카롱') || foodInput.includes('케이크') || foodInput.includes('아이스크림') || foodInput.includes('초콜릿') || foodInput.includes('과자') || foodInput.includes('콜라') || foodInput.includes('당') || foodInput.includes('단')) {
        mockResult = { calories: '450 kcal', message: '이 음식은 당분이 높으니 오후엔 가벼운 산책을 추천해요.' };
      } else if (foodInput.includes('샐러드') || foodInput.includes('닭가슴살') || foodInput.includes('야채')) {
        mockResult = { calories: '180 kcal', message: '건강한 선택이네요! 목표 달성에 큰 도움이 될 거예요.' };
      } else if (foodInput.includes('치킨') || foodInput.includes('피자') || foodInput.includes('햄버거') || foodInput.includes('튀김') || foodInput.includes('고기')) {
        mockResult = { calories: '800 kcal', message: '칼로리가 다소 높아요. 저녁은 가볍게 드시는 것을 추천합니다.' };
      }
      
      setDietAnalysis(mockResult);
      setIsAnalyzing(false);
    }, 1500);
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
    const stored = localStorage.getItem('healthAppUser');
    if (!stored) {
      router.push('/onboarding');
    } else {
      const parsedData = JSON.parse(stored);
      setUserData(parsedData);
      
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
  }, [router]);

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
                  <span className="text-[#2563eb]">{userData?.name || '사용자'}</span> 님,
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
              <div className="flex items-baseline space-x-1">
                <p className="text-3xl font-extrabold text-gray-900 tracking-tight">{dietAnalysis ? intakes.calories + 320 : intakes.calories}</p>
                <span className="text-sm font-semibold text-gray-400">/ {targets.calories} kcal</span>
              </div>
              <div className="flex items-center space-x-1 mt-2.5">
                <div className="w-full bg-gray-100 rounded-full h-1.5 flex-1 max-w-[120px] overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: `${Math.min(((dietAnalysis ? intakes.calories + 320 : intakes.calories) / targets.calories) * 100, 100)}%` }} transition={{ duration: 1, ease: 'easeOut' }} className="bg-orange-500 h-1.5 rounded-full"></motion.div>
                </div>
                <p className="text-sm text-gray-500 font-semibold ml-2">{Math.round(Math.min(((dietAnalysis ? intakes.calories + 320 : intakes.calories) / targets.calories) * 100, 100))}%</p>
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
              <div className="flex-1 space-y-1.5">
                <div className="flex justify-between text-[11px] md:text-xs font-bold text-gray-500">
                  <span>탄수화물</span><span>{intakes.carbs}/{targets.carbs}g</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: `${Math.min((intakes.carbs / targets.carbs) * 100, 100)}%` }} transition={{ duration: 1 }} className="bg-amber-400 h-2 rounded-full"></motion.div>
                </div>
              </div>
              <div className="flex-1 space-y-1.5">
                <div className="flex justify-between text-[11px] md:text-xs font-bold text-gray-500">
                  <span>단백질</span><span>{intakes.protein}/{targets.protein}g</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: `${Math.min((intakes.protein / targets.protein) * 100, 100)}%` }} transition={{ duration: 1, delay: 0.1 }} className="bg-blue-400 h-2 rounded-full"></motion.div>
                </div>
              </div>
              <div className="flex-1 space-y-1.5">
                <div className="flex justify-between text-[11px] md:text-xs font-bold text-gray-500">
                  <span>지방</span><span>{intakes.fat}/{targets.fat}g</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: `${Math.min((intakes.fat / targets.fat) * 100, 100)}%` }} transition={{ duration: 1, delay: 0.2 }} className="bg-rose-400 h-2 rounded-full"></motion.div>
                </div>
              </div>
            </div>
          </div>

          {/* Hydration Tracker Card (NEW) */}
          <div 
            onClick={() => {}}
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
                <h3 className="text-gray-900 font-bold text-lg mb-1">식단 기록하기</h3>
                <p className="text-gray-400 text-xs font-medium">칼로리 관리의 시작</p>
              </div>
              <div className="w-10 h-10 bg-gray-50 rounded-2xl flex items-center justify-center text-gray-500 group-hover:bg-orange-50 group-hover:text-orange-500 transition-colors">
                <Utensils className="w-5 h-5" />
              </div>
            </button>
          </div>
        </div>

        {/* AI Recommended Section */}
        <section className="bg-white p-6 md:p-8 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100/60 mt-4 mb-10">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-bold text-gray-900 tracking-wide flex items-center">
              <span className="bg-gradient-to-r from-[#2563eb] to-indigo-500 text-transparent bg-clip-text mr-2">AI 추천</span>
              운동 / 식단
            </h2>
            <button className="text-gray-400 hover:text-[#2563eb] hover:bg-blue-50 transition-all p-2 rounded-full cursor-pointer group focus:outline-none">
              <RefreshCw className="w-5 h-5 group-hover:rotate-180 transition-transform duration-500" />
            </button>
          </div>

          <div className="flex overflow-x-auto space-x-4 pb-4 custom-scrollbar hide-scrollbar -mx-6 px-6 md:mx-0 md:px-0">
            {/* Workout Item 1 */}
            <div onClick={() => router.push('/recommend')} className="min-w-[220px] bg-gradient-to-br from-blue-50 to-indigo-50/50 p-5 rounded-2xl border border-blue-100 hover:-translate-y-1 transition-all duration-300 cursor-pointer group relative overflow-hidden">
              <div className="absolute -right-4 -bottom-4 opacity-10 group-hover:scale-125 transition-transform duration-500">
                <Activity className="w-24 h-24 text-blue-600" />
              </div>
              <div className="bg-white w-10 h-10 rounded-xl flex items-center justify-center text-[#2563eb] mb-3 shadow-sm">
                <Activity className="w-5 h-5" />
              </div>
              <span className="bg-[#2563eb] text-white text-[10px] font-bold px-2 py-1 rounded-md mb-2 inline-block shadow-sm">오늘의 운동</span>
              <h3 className="font-bold text-gray-900 mb-1">코어 강화 데드버그</h3>
              <p className="text-xs text-gray-500 font-medium line-clamp-2">{conditions.includes('허리 디스크') ? '허리에 무리가 가지 않는 코어 운동입니다.' : '데드버그, 플랭크 루틴으로 복부 근력을 길러보세요.'}</p>
            </div>

            {/* Diet Item 1 */}
            <div onClick={() => router.push('/recommend')} className="min-w-[220px] bg-gradient-to-br from-orange-50 to-amber-50/50 p-5 rounded-2xl border border-orange-100 hover:-translate-y-1 transition-all duration-300 cursor-pointer group relative overflow-hidden">
               <div className="absolute -right-4 -bottom-4 opacity-10 group-hover:scale-125 transition-transform duration-500">
                <Utensils className="w-24 h-24 text-orange-600" />
              </div>
              <div className="bg-white w-10 h-10 rounded-xl flex items-center justify-center text-orange-500 mb-3 shadow-sm">
                <Utensils className="w-5 h-5" />
              </div>
              <span className="bg-orange-500 text-white text-[10px] font-bold px-2 py-1 rounded-md mb-2 inline-block shadow-sm">오늘의 식단</span>
              <h3 className="font-bold text-gray-900 mb-1">고단백 닭가슴살 샐러드</h3>
              <p className="text-xs text-gray-500 font-medium line-clamp-2">{allergies.length > 0 && !allergies.includes('해당 없음') ? `알레르기(\${allergies[0]})를 피해 구성한 식단입니다.` : '운동 후 단백질 보충을 위한 최적의 식단입니다.'}</p>
            </div>

            {/* Workout Item 2 */}
            <div onClick={() => router.push('/recommend')} className="min-w-[220px] bg-gradient-to-br from-emerald-50 to-teal-50/50 p-5 rounded-2xl border border-emerald-100 hover:-translate-y-1 transition-all duration-300 cursor-pointer group relative overflow-hidden">
              <div className="absolute -right-4 -bottom-4 opacity-10 group-hover:scale-125 transition-transform duration-500">
                <Droplets className="w-24 h-24 text-emerald-600" />
              </div>
              <div className="bg-white w-10 h-10 rounded-xl flex items-center justify-center text-emerald-500 mb-3 shadow-sm">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              </div>
              <span className="bg-emerald-500 text-white text-[10px] font-bold px-2 py-1 rounded-md mb-2 inline-block shadow-sm">회복 요가</span>
              <h3 className="font-bold text-gray-900 mb-1">아침 스트레칭</h3>
              <p className="text-xs text-gray-500 font-medium line-clamp-2">하루를 가볍게 시작할 수 있는 전신 스트레칭입니다.</p>
            </div>
          </div>
          <style dangerouslySetInnerHTML={{ __html: `
            .hide-scrollbar::-webkit-scrollbar { display: none; }
            .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
          `}} />
        </section>
      </div>

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
                          <span className={`text-sm font-medium transition-all ${todo.completed ? 'line-through text-gray-400' : 'text-gray-700'}`}>{todo.text}</span>
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
                <button onClick={() => { setIsDietModalOpen(false); setTimeout(() => { setDietAnalysis(null); setFoodInput(''); }, 300); }} className="text-gray-400 hover:text-gray-600 transition-colors p-1 bg-white rounded-full shadow-sm">
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <div className="p-6">
                <form onSubmit={handleDietSubmit} className="space-y-4">
                  <div>
                    <label className="block text-sm font-bold text-gray-700 mb-2">어떤 음식을 드셨나요?</label>
                    <input 
                      type="text" 
                      value={foodInput}
                      onChange={(e) => setFoodInput(e.target.value)}
                      placeholder="예) 참치 김밥과 떡볶이" 
                      className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#2563eb]/20 focus:border-[#2563eb] transition-all"
                    />
                  </div>
                  
                  <button 
                    type="submit" 
                    disabled={!foodInput.trim() || isAnalyzing}
                    className="w-full bg-[#2563eb] text-white font-bold py-3.5 rounded-xl shadow-[0_4px_12px_rgba(37,99,235,0.2)] hover:bg-blue-700 transition-all disabled:opacity-50 disabled:shadow-none flex justify-center items-center h-[52px]"
                  >
                    {isAnalyzing ? (
                      <div className="flex space-x-2 items-center">
                        <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                        <span className="ml-2">AI 분석 중...</span>
                      </div>
                    ) : (
                      'AI 분석'
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
                          <span className="text-sm font-bold text-gray-600">예상 칼로리</span>
                          <span className="text-lg font-extrabold text-[#2563eb]">{dietAnalysis.calories}</span>
                        </div>
                        <div className="h-px w-full bg-blue-100/50 relative z-10"></div>
                        <div className="flex items-start space-x-2.5 relative z-10 pt-1">
                          <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                            <span className="text-[10px]">🤖</span>
                          </div>
                          <p className="text-sm text-gray-700 leading-relaxed font-medium">
                            {dietAnalysis.message}
                          </p>
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
                      onChange={(e) => setGoalInput({...goalInput, calories: e.target.value})}
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
                        onChange={(e) => setGoalInput({...goalInput, carbs: e.target.value})}
                        className="w-full bg-gray-50 border border-gray-200 rounded-xl px-2 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#2563eb]/20 focus:border-[#2563eb] transition-all text-center"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-gray-700 mb-1">단백질 (g)</label>
                      <input 
                        type="number" 
                        value={goalInput.protein}
                        onChange={(e) => setGoalInput({...goalInput, protein: e.target.value})}
                        className="w-full bg-gray-50 border border-gray-200 rounded-xl px-2 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#2563eb]/20 focus:border-[#2563eb] transition-all text-center"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-gray-700 mb-1">지방 (g)</label>
                      <input 
                        type="number" 
                        value={goalInput.fat}
                        onChange={(e) => setGoalInput({...goalInput, fat: e.target.value})}
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
    </div>
  );
}
