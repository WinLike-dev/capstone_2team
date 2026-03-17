"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Calendar, CheckSquare, Plus, Trash2, X, Droplets, Utensils, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Home() {
  const router = useRouter();
  const [userData, setUserData] = useState<{name: string, goal: string} | null>(null);
  const [isClient, setIsClient] = useState(false);
  const [isPlannerOpen, setIsPlannerOpen] = useState(false);
  
  // Water tracker state (glasses of water)
  const [waterGlasses, setWaterGlasses] = useState(2);
  const maxWaterGlasses = 8;

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

  const addWater = (e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (waterGlasses < maxWaterGlasses) setWaterGlasses(prev => prev + 1);
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
      setUserData(JSON.parse(stored));
    }
  }, [router]);

  const currentDate = new Date('2026-03-16').toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  });

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
                  <span className="text-[#2563eb]">{userData.name}</span> 님,
                </h1>
                <p className="text-gray-600 text-base font-medium mt-1">오늘은 <span className="text-[#2563eb] font-bold">{userData.goal}</span>을 목표로 달려봐요!</p>
              </motion.div>
            ) : (
              <div className="h-[76px]"></div>
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
          {/* Steps Card */}
          <div className="bg-white p-6 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100/60 flex flex-col justify-between hover:shadow-[0_12px_40px_rgb(37,99,235,0.08)] hover:-translate-y-1 transition-all duration-300">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div className="w-11 h-11 rounded-2xl bg-blue-50/80 flex items-center justify-center text-[#2563eb] shadow-inner">
                  <Activity className="w-5 h-5" />
                </div>
                <h2 className="text-base font-bold text-gray-800 tracking-wide">오늘의 걸음</h2>
              </div>
            </div>
            <div>
              <div className="flex items-baseline space-x-1">
                <p className="text-3xl font-extrabold text-gray-900 tracking-tight">8,432</p>
                <span className="text-sm font-semibold text-gray-400">걸음</span>
              </div>
              <div className="flex items-center space-x-1 mt-2.5">
                <svg className="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                </svg>
                <p className="text-sm text-emerald-600 font-semibold">어제보다 12% 증가</p>
              </div>
            </div>
          </div>

          {/* Calories Card */}
          <div className="bg-white p-6 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100/60 flex flex-col justify-between hover:shadow-[0_12px_40px_rgb(249,115,22,0.08)] hover:-translate-y-1 transition-all duration-300">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div className="w-11 h-11 rounded-2xl bg-orange-50/80 flex items-center justify-center text-orange-500 shadow-inner">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
                  </svg>
                </div>
                <h2 className="text-base font-bold text-gray-800 tracking-wide">소모 칼로리</h2>
              </div>
            </div>
            <div>
              <div className="flex items-baseline space-x-1">
                <p className="text-3xl font-extrabold text-gray-900 tracking-tight">420</p>
                <span className="text-sm font-semibold text-gray-400">kcal</span>
              </div>
              <div className="flex items-center space-x-1 mt-2.5">
                <div className="w-full bg-gray-100 rounded-full h-1.5 flex-1 max-w-[120px] overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: '60%' }} transition={{ duration: 1, ease: 'easeOut' }} className="bg-orange-500 h-1.5 rounded-full"></motion.div>
                </div>
                <p className="text-sm text-gray-500 font-semibold ml-2">60%</p>
              </div>
            </div>
          </div>

          {/* Sleep Card */}
          <div className="bg-white p-6 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100/60 flex flex-col justify-between hover:shadow-[0_12px_40px_rgb(99,102,241,0.08)] hover:-translate-y-1 transition-all duration-300 md:col-span-2 lg:col-span-1">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div className="w-11 h-11 rounded-2xl bg-indigo-50/80 flex items-center justify-center text-indigo-500 shadow-inner">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                </div>
                <h2 className="text-base font-bold text-gray-800 tracking-wide">수면 시간</h2>
              </div>
            </div>
            <div>
              <div className="flex items-baseline space-x-1">
                <p className="text-3xl font-extrabold text-gray-900 tracking-tight">7</p>
                <span className="text-base font-semibold text-gray-500 pr-1">h</span>
                <p className="text-3xl font-extrabold text-gray-900 tracking-tight">20</p>
                <span className="text-base font-semibold text-gray-500">m</span>
              </div>
              <div className="flex items-center space-x-1 mt-2.5">
                <p className="text-sm text-[#2563eb] font-semibold">✨ 좋은 수면 상태입니다</p>
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
            <button className="group bg-white p-5 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.06)] border border-gray-100/80 hover:shadow-[0_12px_40px_rgb(0,0,0,0.1)] hover:-translate-y-1 transition-all duration-300 flex items-center justify-between text-left">
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

        {/* Weekly Chart Placeholder */}
        <section className="bg-white p-6 md:p-8 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100/60 mt-4 mb-10">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-bold text-gray-900 tracking-wide">주간 활동량</h2>
            <button className="text-sm font-bold text-[#2563eb] hover:text-white hover:bg-[#2563eb] transition-all bg-blue-50 px-4 py-2 rounded-xl">자세히 보기</button>
          </div>

          <div className="w-full h-[240px] bg-gradient-to-br from-gray-50/80 to-gray-100/30 rounded-2xl border border-dashed border-gray-200 flex items-center justify-center relative overflow-hidden group">
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9InJnYmEoMjI2LCAyMzIsIDI0MCwgMC40KSIvPjwvc3ZnPg==')] [mask-image:linear-gradient(to_bottom,white,transparent)]"></div>
            <div className="text-center relative z-10 p-5 bg-white/90 backdrop-blur-md rounded-2xl shadow-sm border border-gray-100 transition-transform group-hover:scale-105 duration-300">
              <div className="w-14 h-14 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-3 text-[#2563eb] shadow-inner">
                <Activity className="w-6 h-6" />
              </div>
              <p className="text-gray-900 font-bold mb-1 tracking-wide">주간 차트 영역</p>
              <p className="text-gray-500 text-xs font-medium">데이터를 연결하여 추이를 확인하세요</p>
            </div>
            {/* Decorative bars */}
            <div className="absolute bottom-0 left-0 right-0 px-10 pt-8 flex justify-between items-end h-full opacity-[0.08] pointer-events-none">
              <div className="w-8 md:w-10 bg-[#2563eb] rounded-t-lg h-[40%]"></div>
              <div className="w-8 md:w-10 bg-[#2563eb] rounded-t-lg h-[65%]"></div>
              <div className="w-8 md:w-10 bg-[#2563eb] rounded-t-lg h-[35%]"></div>
              <div className="w-8 md:w-10 bg-[#2563eb] rounded-t-lg h-[85%]"></div>
              <div className="w-8 md:w-10 bg-[#2563eb] rounded-t-lg h-[55%]"></div>
              <div className="w-8 md:w-10 bg-[#2563eb] rounded-t-lg h-[95%]"></div>
              <div className="w-8 md:w-10 bg-[#2563eb] rounded-t-lg h-[75%]"></div>
            </div>
          </div>
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
    </div>
  );
}
