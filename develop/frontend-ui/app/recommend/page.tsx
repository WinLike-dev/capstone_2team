/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import { Info, Clock, Flame, ChevronRight, Apple, Calendar as CalendarIcon, ChevronLeft, X } from 'lucide-react';
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const getFoodEmoji = (name: string) => {
  if (name.includes('샐러드') || name.includes('야채')) return '🥗';
  if (name.includes('스테이크') || name.includes('고기') || name.includes('장조림')) return '🍖';
  if (name.includes('쉐이크') || name.includes('우유')) return '🥛';
  if (name.includes('밥') || name.includes('국') || name.includes('찌개')) return '🍚';
  if (name.includes('파스타') || name.includes('면') || name.includes('소바') || name.includes('우동')) return '🍝';
  if (name.includes('샌드위치') || name.includes('빵')) return '🥪';
  if (name.includes('계란') || name.includes('에그') || name.includes('낫토')) return '🍳';
  if (name.includes('연어') || name.includes('초밥')) return '🍣';
  if (name.includes('요거트') || name.includes('보울')) return '🥣';
  if (name.includes('닭')) return '🍗';
  return '🥗'; // 기본 음식 아이콘
};

const generateMockPlans = () => {
  const plans = [];
  const start = new Date('2026-03-01');
  const end = new Date('2026-04-30');
  
  const workoutTemplates = [
    [
      { title: "모닝 조깅 & 워밍업", time: "20분", level: "초급", calories: "150 kcal", color: "from-sky-400 to-blue-500" },
      { title: "전신 근력 데드리프트", time: "40분", level: "중급", calories: "350 kcal", color: "from-indigo-500 to-purple-600" },
      { title: "수면 전 릴렉스 요가", time: "15분", level: "초급", calories: "50 kcal", color: "from-teal-400 to-emerald-500" }
    ],
    [
      { title: "공복 실내 자전거", time: "30분", level: "초급", calories: "200 kcal", color: "from-blue-500 to-indigo-600" },
      { title: "맨몸 코어 트레이닝", time: "20분", level: "중급", calories: "150 kcal", color: "from-orange-400 to-red-500" },
      { title: "폼롤러 하체 스트레칭", time: "10분", level: "초급", calories: "40 kcal", color: "from-pink-400 to-rose-500" }
    ],
    [
      { title: "경사로 걷기 (인클라인)", time: "40분", level: "초급", calories: "250 kcal", color: "from-sky-400 to-blue-500" },
      { title: "상체 덤벨 웨이트", time: "35분", level: "중급", calories: "280 kcal", color: "from-indigo-500 to-purple-600" },
      { title: "어깨/목 뭉침 해소 스트레칭", time: "15분", level: "초급", calories: "60 kcal", color: "from-green-400 to-emerald-500" }
    ],
    [
      { title: "HIIT 인터벌 트레이닝", time: "20분", level: "상급", calories: "300 kcal", color: "from-red-500 to-orange-600" },
      { title: "하체 중심 맨몸 스쿼트", time: "25분", level: "중급", calories: "200 kcal", color: "from-purple-500 to-indigo-600" },
      { title: "정적인 전신 요가", time: "20분", level: "초급", calories: "80 kcal", color: "from-teal-400 to-emerald-500" }
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
    
    plans.push({
      date: dateStr,
      task: '맞춤형 복합 밸런스 플랜',
      workout: { type: '유산소 + 근력 + 스트레칭', sets: '총 3가지 운동 코스 진행' },
      diet: { breakfast: dT.breakfast.name, lunch: dT.lunch.name, dinner: dT.dinner.name },
      exercises: wT,
      diets: [
        { type: "아침", ...dT.breakfast },
        { type: "점심", ...dT.lunch },
        { type: "저녁", ...dT.dinner }
      ]
    });
    
    current.setDate(current.getDate() + 1);
    dayCount++;
  }
  return plans;
}

const mockPlans = generateMockPlans();

export const getTodayPlan = (date: Date) => {
  const dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  return mockPlans.find(plan => plan.date === dateStr) || null;
};

export default function RecommendPage() {
  const [currentDate, setCurrentDate] = useState(new Date('2026-03-01'));
  const [today, setToday] = useState<Date | null>(null);
  const [todayPlan, setTodayPlan] = useState<typeof mockPlans[0] | null>(null);

  const [userData, setUserData] = useState<{name: string, goal: string, allergies?: string[], conditions?: string[]} | null>(null);

  // const allergies = userData?.allergies || [];
  // const conditions = userData?.conditions || [];

  useEffect(() => {
    const now = new Date();
    setToday(now);
    setCurrentDate(new Date(now.getFullYear(), now.getMonth(), 1));
    setTodayPlan(getTodayPlan(now));

    const stored = localStorage.getItem('healthAppUser');
    if (stored) {
      setUserData(JSON.parse(stored));
    }
  }, []);

  const [selectedPlan, setSelectedPlan] = useState<typeof mockPlans[0] | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

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



  let headerMessage = "꾸준한 식단 관리가<br />성공의 가장 빠른 지름길이에요!";
  let subMessage = "사용자님의 다이어트 목표 달성을 응원합니다.";

  if (userData) {
    if (userData.goal === '다이어트') {
      headerMessage = `${userData.name} 님의 다이어트 목표 달성을<br/>AI가 끝까지 응원합니다!`;
      subMessage = '꾸준한 식단과 유산소로 목표를 이루어봐요!';
    } else if (userData.goal === '건강 유지') {
      headerMessage = `오늘도 건강한 밸런스를 유지하는<br/>${userData.name} 님이 멋져요!`;
      subMessage = '규칙적인 생활로 활기찬 하루를 보내세요.';
    } else if (userData.goal === '근력 향상') {
      headerMessage = `강력한 근력을 위해 오늘 추천된<br/>운동을 완료해 보세요!`;
      subMessage = `${userData.name} 님의 한계 돌파를 응원합니다.`;
    }
  }

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
            dangerouslySetInnerHTML={{ __html: `"${headerMessage}"` }}
          />
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
                const planForDay = mockPlans.find(p => p.date === dateStr);

                const isToday = today && day === today.getDate() && currentMonth === today.getMonth() && currentYear === today.getFullYear();
                const isWeekend = idx % 7 === 0 || idx % 7 === 6;

                return (
                  <div
                    key={`day-${day}`}
                    onClick={() => {
                      if (planForDay) {
                        setSelectedPlan(planForDay);
                        setIsModalOpen(true);
                      }
                    }}
                    className={`h-16 md:h-20 lg:h-24 p-1 md:p-2 rounded-xl flex flex-col items-center md:items-start border border-transparent transition-all hover:bg-gray-50 cursor-pointer ${isToday ? 'bg-blue-50/50 border-blue-100' : ''
                      }`}
                  >
                    <span className={`text-sm font-semibold ${isToday ? 'text-white bg-[#2563eb] w-6 h-6 rounded-full flex items-center justify-center mb-1' : isWeekend ? 'text-gray-400' : 'text-gray-700'}`}>
                      {day}
                    </span>
                    {planForDay && (
                      <div className="mt-auto md:mt-1 w-full flex justify-center md:justify-start">
                        <span className="md:hidden w-1.5 h-1.5 bg-blue-500 rounded-full mt-1"></span>
                        <div className="hidden md:block w-full bg-blue-50 text-blue-600 border border-blue-100 text-[10px] md:text-xs font-semibold px-1.5 py-1 rounded-md truncate shadow-sm" title={planForDay.exercises[0].title}>
                          {planForDay.exercises[0].title.length > 10 ? `${planForDay.exercises[0].title.substring(0, 10)}...` : planForDay.exercises[0].title}
                        </div>
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
              {todayPlan.exercises.map((ex, idx) => (
                <div key={idx} className="bg-white rounded-2xl p-5 shadow-[0_4px_16px_-6px_rgba(0,0,0,0.06)] border border-gray-100 flex items-center hover:shadow-[0_8px_24px_-6px_rgba(37,99,235,0.12)] hover:-translate-y-1 transition-all duration-300 group cursor-pointer">
                  <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${ex.color} flex items-center justify-center text-white shadow-inner flex-shrink-0`}>
                    <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-4 flex-1">
                    <h3 className="font-bold text-gray-900 text-[17px] mb-1">{ex.title}</h3>
                    <div className="flex items-center space-x-3 text-xs font-semibold text-gray-500">
                      <span className="flex items-center"><Clock className="w-3.5 h-3.5 mr-1" />{ex.time}</span>
                      <span className="w-1 h-1 rounded-full bg-gray-300"></span>
                      <span className="text-[#2563eb]">{ex.level}</span>
                      <span className="w-1 h-1 rounded-full bg-gray-300"></span>
                      <span>{ex.calories}</span>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-[#2563eb] transition-colors" />
                </div>
              ))}
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
              {todayPlan.diets.map((diet, idx) => (
                <div key={idx} className="bg-white rounded-2xl p-5 flex flex-col items-center text-center shadow-[0_4px_16px_-6px_rgba(0,0,0,0.06)] border border-gray-100 hover:shadow-[0_8px_24px_-6px_rgba(37,99,235,0.12)] transition-all shrink-0">
                  <div className="text-xs font-bold text-[#2563eb] bg-blue-50 px-3 py-1 rounded-full mb-3">
                    {diet.type}
                  </div>
                  <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center text-3xl mb-4 shadow-sm">
                    {getFoodEmoji(diet.name)}
                  </div>
                  <h3 className="font-bold text-gray-900 text-[15px] mb-1">{diet.name}</h3>
                  <p className="text-xs font-semibold text-gray-500 mb-2">{diet.desc}</p>
                  <div className="mt-auto pt-2 w-full border-t border-gray-50">
                    <span className="text-xs font-bold text-[#2563eb]">{diet.kcal}</span>
                  </div>
                </div>
              ))}
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
                    {selectedPlan.exercises.map((ex, idx) => (
                      <div key={idx} className="flex justify-between items-center">
                        <span className="text-xs font-bold text-orange-700 bg-white border border-orange-200 px-2.5 py-1 rounded-md shadow-sm whitespace-nowrap">
                          {idx + 1}
                        </span>
                        <span className="text-sm font-bold text-gray-900 text-right ml-4">{ex.title}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="flex items-center space-x-2 mb-3">
                    <Apple className="w-5 h-5 text-green-500" />
                    <h4 className="font-bold text-gray-900">추천 식단</h4>
                  </div>
                  <div className="bg-green-50/50 border border-green-100 rounded-xl p-4 space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-green-700 bg-white border border-green-200 px-2 py-1 rounded-md shadow-sm whitespace-nowrap">아침</span>
                      <span className="text-sm font-bold text-gray-900 text-right ml-4">{selectedPlan.diet.breakfast}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-green-700 bg-white border border-green-200 px-2 py-1 rounded-md shadow-sm whitespace-nowrap">점심</span>
                      <span className="text-sm font-bold text-gray-900 text-right ml-4">{selectedPlan.diet.lunch}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-green-700 bg-white border border-green-200 px-2 py-1 rounded-md shadow-sm whitespace-nowrap">저녁</span>
                      <span className="text-sm font-bold text-gray-900 text-right ml-4">{selectedPlan.diet.dinner}</span>
                    </div>
                  </div>
                </div>
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
