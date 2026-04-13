"use client";

import { Info, Clock, Flame, ChevronRight, Apple, Calendar as CalendarIcon, ChevronLeft, X } from 'lucide-react';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { usePlan, DailyPlan } from '../context/PlanContext';

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
  return '🥗'; // 기본 음식 아이콘
};

const mapWorkoutType = (typeRaw: string) => {
  if (!typeRaw) return '상체 운동';
  if (typeRaw.includes('하체') || typeRaw.includes('스쿼트')) return '하체 운동';
  if (typeRaw.includes('유산소') || typeRaw.includes('조깅') || typeRaw.includes('고강도') || typeRaw.includes('자전거') || typeRaw.includes('걷는') || typeRaw.includes('걷기')) return '유산소';
  if (typeRaw.includes('스트레칭') || typeRaw.includes('요가') || typeRaw.includes('이완')) return '스트레칭';
  return '상체 운동'; // 전신, 코어, 기타 모든 운동을 상체 운동으로 매핑
};

export default function RecommendPage() {
  const { completedTasks, completeWorkout, completeDiet, getPlanByDate, userData, isUserLoading } = usePlan();
  const initialToday = new Date();
  
  const [currentDate, setCurrentDate] = useState(
    () => new Date(initialToday.getFullYear(), initialToday.getMonth(), 1)
  );
  const [today] = useState<Date>(initialToday);

  const [confirmPopup, setConfirmPopup] = useState<{isOpen: boolean, target: {type: 'workout'|'diet', dateStr: string, name: string, index: number} | null}>({isOpen: false, target: null});

  const handleWorkoutComplete = (dateStr: string, name: string, index: number) => {
    setConfirmPopup({isOpen: true, target: {type: 'workout', dateStr, name, index}});
  };

  const handleDietComplete = (dateStr: string, name: string, index: number) => {
    setConfirmPopup({isOpen: true, target: {type: 'diet', dateStr, name, index}});
  };

  const executeConfirm = () => {
    if (!confirmPopup.target) return;
    if (confirmPopup.target.type === 'workout') {
      completeWorkout(confirmPopup.target.dateStr, confirmPopup.target.index);
    } else {
      completeDiet(confirmPopup.target.dateStr, confirmPopup.target.index);
    }
    setConfirmPopup({isOpen: false, target: null});
  };

  const [selectedPlan, setSelectedPlan] = useState<DailyPlan | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const todayPlan = getPlanByDate(today);

  const getDaysInMonth = (year: number, month: number) => new Date(year, month + 1, 0).getDate();
  const currentYear = currentDate.getFullYear();
  const currentMonth = currentDate.getMonth();

  const daysInMonth = getDaysInMonth(currentYear, currentMonth);
  const firstDayOfMonth = new Date(currentYear, currentMonth, 1).getDay();

  const days = [];
  for (let i = 0; i < firstDayOfMonth; i++) days.push(null);
  for (let i = 1; i <= daysInMonth; i++) days.push(i);

  const prevMonth = () => setCurrentDate(new Date(currentYear, currentMonth - 1, 1));
  const nextMonth = () => setCurrentDate(new Date(currentYear, currentMonth + 1, 1));

  const weekDays = ['일', '월', '화', '수', '목', '금', '토'];
  const shouldShowHeaderSkeleton = isUserLoading;

  let headerMessage = "꾸준한 식단 관리가<br />성공의 가장 빠른 지름길이에요!";
  let subMessage = "사용자님의 다이어트 목표 달성을 응원합니다.";

  if (isUserLoading) {
    subMessage = "";
  } else if (userData) {
    const displayName = userData.name || userData.nickname || '사용자';
    if (userData.goal === '다이어트') {
      headerMessage = `${displayName} 님의 다이어트 목표 달성을<br/>AI가 끝까지 응원합니다!`;
      subMessage = '꾸준한 식단과 유산소로 목표를 이루어봐요!';
    } else if (userData.goal === '건강 유지') {
      headerMessage = `오늘도 건강한 밸런스를 유지하는<br/>${displayName} 님이 멋져요!`;
      subMessage = '규칙적인 생활로 활기찬 하루를 보내세요.';
    } else if (userData.goal === '근력 향상') {
      headerMessage = `강력한 근력을 위해 오늘 추천된<br/>운동을 완료해 보세요!`;
      subMessage = `${displayName} 님의 한계 돌파를 응원합니다.`;
    } else {
      headerMessage = `${displayName} 님의 목표 달성을<br/>AI가 끝까지 응원합니다!`;
    }
  }

  const headerLines = headerMessage
    .split(/<br\s*\/?>/i)
    .map((line) => line.trim())
    .filter(Boolean);

  return (
    <div className="min-h-screen bg-[#f8fafc] text-gray-900 font-sans pb-28">
      {/* Top Message Section with Pastel Background */}
      <div className="bg-gradient-to-br from-blue-100 via-sky-50 to-indigo-100 pt-10 pb-8 px-6 md:px-8 rounded-b-[40px] shadow-[0_4px_24px_-8px_rgba(37,99,235,0.15)] relative overflow-hidden">
        <div className="absolute right-0 top-0 opacity-10">
          <svg width="150" height="150" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="currentColor" />
          </svg>
        </div>
        <div className="max-w-4xl mx-auto relative z-10">
          <div className="inline-flex items-center space-x-1.5 bg-white/60 backdrop-blur-sm px-3 py-1.5 rounded-full mb-3 shadow-sm">
            <Info className="w-4 h-4 text-[#2563eb]" />
            <span className="text-xs font-bold text-[#2563eb]">오늘의 건강 메시지</span>
          </div>
          <motion.h1 
            key={headerMessage}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-2xl md:text-3xl font-bold text-gray-900 tracking-tight leading-snug mb-2"
          >
            {shouldShowHeaderSkeleton ? (
              <>
                <span className="mb-2 block h-8 w-64 rounded-md bg-gray-200/50 animate-pulse" />
                <span className="block h-8 w-48 rounded-md bg-gray-200/50 animate-pulse" />
              </>
            ) : (
              headerLines.map((line, index) => (
                <span
                  key={`${line}-${index}`}
                  className={index === 0 ? 'block' : 'mt-1 block'}
                >
                  {line}
                </span>
              ))
            )}
          </motion.h1>
          <motion.p 
            key={subMessage}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-gray-600 font-medium text-sm"
          >
            {subMessage}
          </motion.p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 md:px-8 mt-8 space-y-10">

        {/* AI Plan Calendar Section (NEW) */}
        <section>
          <div className="flex justify-between items-center mb-5">
            <h2 className="text-xl font-bold text-gray-900 tracking-tight flex items-center">
              사용자 문진 기반 AI 맞춤 플랜
              <CalendarIcon className="w-5 h-5 text-indigo-500 mb-0.5 ml-1.5" />
            </h2>
          </div>

          <div className="bg-white rounded-3xl p-5 md:p-6 shadow-[0_4px_16px_-6px_rgba(0,0,0,0.06)] border border-gray-100">
            {/* Calendar Header */}
            <div className="flex justify-between items-center mb-6">
              <button onClick={prevMonth} className="p-2 hover:bg-gray-50 rounded-full transition-colors">
                <ChevronLeft className="w-5 h-5 text-gray-500" />
              </button>
              <h3 className="text-lg font-bold text-gray-900">
                {currentYear}년 {currentMonth + 1}월
              </h3>
              <button onClick={nextMonth} className="p-2 hover:bg-gray-50 rounded-full transition-colors">
                <ChevronRight className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Calendar Grid */}
            <div className="grid grid-cols-7 gap-1 md:gap-2 mb-2">
              {weekDays.map((day, idx) => (
                <div key={idx} className={`text-center text-xs font-bold mb-2 ${idx === 0 ? 'text-red-400' : idx === 6 ? 'text-blue-400' : 'text-gray-500'}`}>
                  {day}
                </div>
              ))}
            </div>

            <div className="grid grid-cols-7 gap-1 md:gap-2">
              {days.map((day, idx) => {
                if (day === null) return <div key={`empty-${idx}`} className="h-16 md:h-20 lg:h-24 bg-transparent rounded-xl"></div>;

                const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                const planForDay = getPlanByDate(dateStr);

                const isToday = today && day === today.getDate() && currentMonth === today.getMonth() && currentYear === today.getFullYear();
                const isWeekend = idx % 7 === 0 || idx % 7 === 6;

                const dayStatus = completedTasks[dateStr] || { workouts: [], diets: [] };
                let cellBgColor = 'hover:bg-gray-50 bg-white border-transparent';

                let workoutRatio = 0;
                let dietRatio = 0;

                let isAllWorkoutDone = false;
                let isAllDietDone = false;
                let isEverythingDone = false;

                if (planForDay) {
                  const totalWorkouts = planForDay.exercises.length;
                  const totalDiets = planForDay.diets.length;
                  const totalTasks = totalWorkouts + totalDiets;
                  
                  workoutRatio = totalWorkouts > 0 ? (dayStatus.workouts.length / totalWorkouts) * 100 : 0;
                  dietRatio = totalDiets > 0 ? (dayStatus.diets.length / totalDiets) * 100 : 0;

                  isAllWorkoutDone = dayStatus.workouts.length === totalWorkouts && totalWorkouts > 0;
                  isAllDietDone = dayStatus.diets.length === totalDiets && totalDiets > 0;
                  
                  const completedCount = dayStatus.workouts.length + dayStatus.diets.length;
                  isEverythingDone = completedCount === totalTasks && totalTasks > 0;
                  
                  if (completedCount === totalTasks && totalTasks > 0) {
                    cellBgColor = 'bg-green-100/60 border-green-200 hover:bg-green-100/80';
                  } else if (completedCount > 0) {
                    cellBgColor = 'bg-orange-50/70 border-orange-200 hover:bg-orange-100/80';
                  } else {
                    const cellDate = new Date(currentYear, currentMonth, day);
                    // Check if date is in the past compared to today (without time)
                    if (today && cellDate < new Date(today.getFullYear(), today.getMonth(), today.getDate())) {
                      cellBgColor = 'bg-red-50 border-red-100 hover:bg-red-100/70';
                    }
                  }
                }

                return (
                  <div
                    key={`day-${day}`}
                    onClick={() => {
                      if (planForDay) {
                        setSelectedPlan(planForDay);
                        setIsModalOpen(true);
                      }
                    }}
                    className={`relative h-[110px] md:h-32 p-1.5 md:p-2.5 rounded-2xl flex flex-col items-center md:items-start border transition-all cursor-pointer ${cellBgColor} ${isToday && cellBgColor.includes('bg-white') ? '!bg-blue-50/50 !border-blue-100' : ''}`}
                  >
                    <div className="flex justify-between w-full items-start">
                      <span className={`text-sm md:text-base font-bold relative z-10 ${isToday ? 'text-white bg-[#2563eb] w-7 h-7 md:w-8 md:h-8 rounded-full flex items-center justify-center -ml-1 -mt-1 shadow-sm' : isWeekend ? 'text-gray-400' : 'text-gray-700'} pl-1 pt-0.5`}>
                        {day}
                      </span>
                      {/* Checkmark or Sparkles if 100% complete for the day */}
                      {isEverythingDone && (
                        <motion.div initial={{scale:0, rotate:-180}} animate={{scale:1, rotate:0}} transition={{type:'spring', stiffness:200}} className="text-yellow-500 drop-shadow-sm text-sm md:text-base">
                          ✨
                        </motion.div>
                      )}
                    </div>
                    {planForDay && (
                      <div className="mt-auto w-full flex flex-col space-y-1.5 md:space-y-2 pb-1">

                        {/* Workout Progress Pill */}
                        <motion.div 
                          layout
                          className={`flex items-center w-full rounded-lg md:rounded-full transition-all duration-300 ${
                            isAllWorkoutDone ? 'bg-orange-500 px-1.5 md:px-2 py-0.5 md:py-1 justify-center shadow-md shadow-orange-500/20' : 'bg-white/80 border border-orange-100 px-1.5 md:px-2 py-1 md:py-1 space-x-1.5 md:space-x-2'
                          }`}
                        >
                          <Flame className={`w-3 h-3 md:w-3.5 md:h-3.5 flex-shrink-0 transition-colors ${isAllWorkoutDone ? 'text-white fill-white' : 'text-orange-500 fill-orange-500'}`} />
                          {isAllWorkoutDone ? (
                            <motion.span initial={{scale:0}} animate={{scale:1}} className="text-[9px] md:text-[10px] font-bold text-white ml-1 hidden md:block tracking-wide">완료</motion.span>
                          ) : (
                            <div className="flex-1 h-1 md:h-1.5 bg-orange-100 rounded-full overflow-hidden">
                              <motion.div className="h-full bg-orange-500 rounded-full" initial={{width:0}} animate={{ width: `${workoutRatio}%` }} transition={{duration:0.4, ease: "easeOut"}}/>
                            </div>
                          )}
                        </motion.div>

                        {/* Diet Progress Pill */}
                        <motion.div 
                          layout
                          className={`flex items-center w-full rounded-lg md:rounded-full transition-all duration-300 ${
                            isAllDietDone ? 'bg-green-500 px-1.5 md:px-2 py-0.5 md:py-1 justify-center shadow-md shadow-green-500/20' : 'bg-white/80 border border-green-100 px-1.5 md:px-2 py-1 md:py-1 space-x-1.5 md:space-x-2'
                          }`}
                        >
                          <Apple className={`w-3 h-3 md:w-3.5 md:h-3.5 flex-shrink-0 transition-colors ${isAllDietDone ? 'text-white fill-white' : 'text-green-500 fill-green-500'}`} />
                          {isAllDietDone ? (
                            <motion.span initial={{scale:0}} animate={{scale:1}} className="text-[9px] md:text-[10px] font-bold text-white ml-1 hidden md:block tracking-wide">완료</motion.span>
                          ) : (
                            <div className="flex-1 h-1 md:h-1.5 bg-green-100 rounded-full overflow-hidden">
                              <motion.div className="h-full bg-green-500 rounded-full" initial={{width:0}} animate={{ width: `${dietRatio}%` }} transition={{duration:0.4, ease: "easeOut"}}/>
                            </div>
                          )}
                        </motion.div>

                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Workout section */}
        <section>
          <div className="flex justify-between items-center mb-5">
            <h2 className="text-xl font-bold text-gray-900 tracking-tight flex items-center">
              오늘의 운동
              <Flame className="w-5 h-5 text-orange-500 mb-0.5 ml-1.5" />
            </h2>
          </div>
          {todayPlan && todayPlan.exercises && todayPlan.exercises.length > 0 ? (
            <div className="space-y-4">
              {todayPlan.exercises.map((ex, idx) => {
                const todayDateStr = todayPlan.date;
                const isCompleted = (completedTasks[todayDateStr]?.workouts || []).includes(idx);

                return (
                  <div key={idx} className={`bg-white rounded-2xl p-5 shadow-[0_4px_16px_-6px_rgba(0,0,0,0.06)] border border-gray-100 flex items-center hover:shadow-[0_8px_24px_-6px_rgba(37,99,235,0.12)] hover:-translate-y-1 transition-all duration-300 group`}>
                    <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${ex.color} flex items-center justify-center text-white shadow-inner flex-shrink-0`}>
                      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className={`ml-4 flex-1`}>
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="text-[10px] font-bold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-full shadow-sm">{mapWorkoutType(ex.type || '')}</span>
                        <h3 className="font-bold text-gray-900 text-[17px]">{ex.title}</h3>
                      </div>
                      <div className="flex items-center space-x-3 text-xs font-semibold text-gray-500">
                        <span className="flex items-center"><Clock className="w-3.5 h-3.5 mr-1" />{ex.time}</span>
                        <span className="w-1 h-1 rounded-full bg-gray-300"></span>
                        <span className="text-[#2563eb]">{ex.level}</span>
                        <span className="w-1 h-1 rounded-full bg-gray-300"></span>
                        <span>{ex.calories}</span>
                      </div>
                    </div>
                    <button 
                      onClick={(e) => { e.stopPropagation(); if (!isCompleted) handleWorkoutComplete(todayDateStr, ex.title, idx); }}
                      disabled={isCompleted}
                      className={`ml-4 text-sm px-4 py-2 rounded-xl font-bold transition-all shadow-sm ${isCompleted ? 'bg-gray-400 text-white cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700'}`}
                    >
                      {isCompleted ? '완료!' : '완료'}
                    </button>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="bg-white rounded-2xl p-8 text-center shadow-[0_4px_16px_-6px_rgba(0,0,0,0.06)] border border-gray-100">
              <p className="text-gray-500 font-medium tracking-tight">오늘은 휴식일입니다. 푹 쉬면서 에너지를 재충전하세요! 🛌</p>
            </div>
          )}
        </section>

        {/* Diet section */}
        <section>
          <div className="flex justify-between items-center mb-5">
            <h2 className="text-xl font-bold text-gray-900 tracking-tight flex items-center">
              오늘의 식단
              <Apple className="w-5 h-5 text-green-500 mb-0.5 ml-1.5" />
            </h2>
          </div>
          {todayPlan && todayPlan.diets && todayPlan.diets.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {todayPlan.diets.map((diet, idx) => {
                const todayDateStr = todayPlan.date;
                const isCompleted = (completedTasks[todayDateStr]?.diets || []).includes(idx);

                return (
                  <div key={idx} className={`bg-white rounded-2xl p-5 flex flex-col items-center text-center shadow-[0_4px_16px_-6px_rgba(0,0,0,0.06)] border border-gray-100 hover:shadow-[0_8px_24px_-6px_rgba(37,99,235,0.12)] transition-all shrink-0 ${isCompleted ? 'opacity-50 grayscale bg-gray-50/50' : ''}`}>
                    <div className="text-xs font-bold text-[#2563eb] bg-blue-50 px-3 py-1 rounded-full mb-3">
                      {diet.type}
                    </div>
                    <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center text-3xl mb-4 shadow-sm">
                      {getFoodEmoji(diet.name)}
                    </div>
                    <h3 className={`font-bold text-[15px] mb-1 ${isCompleted ? 'text-gray-400 line-through' : 'text-gray-900'}`}>{diet.name}</h3>
                    <p className={`text-xs font-semibold mb-2 ${isCompleted ? 'text-gray-400 line-through' : 'text-gray-500'}`}>{diet.desc}</p>
                    <div className="mt-auto pt-3 pb-3 w-full border-t border-gray-50">
                      <span className={`text-xs font-bold ${isCompleted ? 'text-gray-400' : 'text-[#2563eb]'}`}>{diet.kcal}</span>
                    </div>
                    <button 
                      onClick={(e) => { e.stopPropagation(); if(!isCompleted) handleDietComplete(todayDateStr, diet.name, idx); }}
                      disabled={isCompleted}
                      className={`w-full mt-2 text-sm py-2 rounded-xl font-bold transition-all shadow-sm ${isCompleted ? 'bg-gray-400 text-white cursor-not-allowed' : 'bg-green-500 text-white hover:bg-green-600'}`}
                    >
                      {isCompleted ? '완료!' : '완료'}
                    </button>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="bg-white rounded-2xl p-8 text-center shadow-[0_4px_16px_-6px_rgba(0,0,0,0.06)] border border-gray-100">
              <p className="text-gray-500 font-medium tracking-tight">기본 추천 플랜: 가벼운 일반식과 수분 보충을 충분히 해주세요! 💧</p>
            </div>
          )}
        </section>

      </div>

      {/* Plan Detail Modal */}
      <AnimatePresence>
        {isModalOpen && selectedPlan && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="absolute inset-0 bg-gray-900/40 backdrop-blur-sm" 
              onClick={() => setIsModalOpen(false)}
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="bg-white rounded-3xl shadow-[0_20px_60px_-12px_rgba(0,0,0,0.15)] w-full max-w-md overflow-hidden z-10"
            >
              <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-blue-50/50">
                <div className="flex items-center space-x-2">
                  <CalendarIcon className="w-5 h-5 text-[#2563eb]" />
                  <h3 className="font-bold text-lg text-gray-900">{selectedPlan.date.split('-')[1]}월 {selectedPlan.date.split('-')[2]}일 상세 플랜</h3>
                </div>
                <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600 transition-colors p-1 bg-white rounded-full shadow-sm">
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <div className="p-6 space-y-6">
                <div>
                  <div className="flex items-center space-x-2 mb-3">
                    <Flame className="w-5 h-5 text-orange-500" />
                    <h4 className="font-bold text-gray-900">추천 운동</h4>
                  </div>
                  <div className="bg-orange-50/50 border border-orange-100 rounded-xl p-4 space-y-3">
                    {selectedPlan.exercises.map((ex, idx) => {
                      const isCompleted = (completedTasks[selectedPlan.date]?.workouts || []).includes(idx);
                      return (
                        <div key={idx} className="flex justify-between items-center group">
                          <div className="flex items-center flex-1 pr-3">
                            <span className={`text-[10px] font-bold ${isCompleted ? 'text-gray-400 bg-gray-100 border-gray-200' : 'text-orange-700 bg-orange-50'} px-2.5 py-1 rounded-full shadow-sm whitespace-nowrap transition-colors`}>
                              {mapWorkoutType(ex.type || '')}
                            </span>
                            <span className={`text-sm font-bold text-left ml-4 transition-all ${isCompleted ? 'text-gray-400 line-through decoration-gray-400' : 'text-gray-900'}`}>{ex.title}</span>
                          </div>
                          <button 
                            onClick={(e) => { e.stopPropagation(); if(!isCompleted) handleWorkoutComplete(selectedPlan.date, ex.title, idx); }}
                            disabled={isCompleted}
                            className={`text-[11px] px-3 py-1.5 rounded-lg font-bold transition-all shadow-sm ${isCompleted ? 'bg-gray-400 text-white cursor-not-allowed' : 'bg-orange-500 text-white hover:bg-orange-600'}`}
                          >
                            {isCompleted ? '완료!' : '완료'}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div>
                  <div className="flex items-center space-x-2 mb-3">
                    <Apple className="w-5 h-5 text-green-500" />
                    <h4 className="font-bold text-gray-900">추천 식단</h4>
                  </div>
                  <div className="bg-green-50/50 border border-green-100 rounded-xl p-4 space-y-3">
                    {selectedPlan.diets.map((diet, idx) => {
                      const isCompleted = (completedTasks[selectedPlan.date]?.diets || []).includes(idx);
                      // selectedPlan uses diet.breakfast, diet.lunch, diet.dinner strings in plan.diets. Wait, no.
                      // Checking structure... selectedPlan.diets is an array of objects
                      return (
                        <div key={idx} className="flex justify-between items-center group">
                          <div className="flex items-center flex-1 pr-3">
                            <span className={`text-[10px] font-bold ${isCompleted ? 'text-gray-400 bg-gray-100 border-gray-200' : 'text-green-700 bg-green-50'} px-2.5 py-1 rounded-full shadow-sm whitespace-nowrap transition-colors`}>
                              {diet.type}
                            </span>
                            <span className={`text-sm font-bold text-left ml-4 transition-all ${isCompleted ? 'text-gray-400 line-through decoration-gray-400' : 'text-gray-900'}`}>{diet.name}</span>
                          </div>
                          <button 
                            onClick={(e) => { e.stopPropagation(); if(!isCompleted) handleDietComplete(selectedPlan.date, diet.name, idx); }}
                            disabled={isCompleted}
                            className={`text-[11px] px-3 py-1.5 rounded-lg font-bold transition-all shadow-sm ${isCompleted ? 'bg-gray-400 text-white cursor-not-allowed' : 'bg-green-500 text-white hover:bg-green-600'}`}
                          >
                            {isCompleted ? '완료!' : '완료'}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Confirm Popup */}
      <AnimatePresence>
        {confirmPopup.isOpen && confirmPopup.target && (
          <div className="fixed inset-0 z-[120] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-gray-900/40 backdrop-blur-sm" onClick={() => setConfirmPopup({isOpen: false, target: null})} />
            <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }} className="bg-white rounded-3xl shadow-xl w-full max-w-sm overflow-hidden z-10 px-6 py-8 text-center">
              <div className={`w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-4 ${confirmPopup.target.type === 'workout' ? 'bg-orange-50 text-orange-500' : 'bg-green-50 text-green-500'}`}>
                {confirmPopup.target.type === 'workout' ? <Flame className="w-7 h-7" /> : <Apple className="w-7 h-7" />}
              </div>
              <h3 className="font-bold text-lg text-gray-900 mb-2">일정 완료</h3>
              <p className="text-sm text-gray-600 mb-6 font-medium leading-relaxed">
                오늘의 <strong className={confirmPopup.target.type === 'workout' ? 'text-orange-600' : 'text-green-600'}>{confirmPopup.target.name}</strong> 일정을<br />
                완료하시나요? 한번 완료하면 다시 취소할 수 없습니다.
              </p>
              <div className="flex space-x-3">
                <button onClick={() => setConfirmPopup({isOpen: false, target: null})} className="flex-1 py-3 bg-gray-100 text-gray-700 font-bold rounded-xl hover:bg-gray-200 transition-colors">취소</button>
                <button onClick={executeConfirm} className={`flex-1 py-3 text-white font-bold rounded-xl transition-colors shadow-md ${confirmPopup.target.type === 'workout' ? 'bg-orange-500 hover:bg-orange-600' : 'bg-green-500 hover:bg-green-600'}`}>완료하기</button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <style dangerouslySetInnerHTML={{
        __html: `
        .hide-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .hide-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}} />
    </div>
  );
}
