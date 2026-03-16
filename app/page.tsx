"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Calendar, CheckSquare, Plus, Trash2, X } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const [userData, setUserData] = useState<{name: string, goal: string} | null>(null);
  const [isClient, setIsClient] = useState(false);
  const [isPlannerOpen, setIsPlannerOpen] = useState(false);
  const [todos, setTodos] = useState<{id: number, text: string, completed: boolean}[]>([
    { id: 1, text: '아침 스트레칭 10분', completed: false },
    { id: 2, text: '물 2L 마시기', completed: false }
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
    <div className="min-h-screen bg-[#f8fafc] text-gray-900 font-sans p-6 pb-26 md:p-8 lg:p-12 md:pb-28 lg:pb-32">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <header className="flex justify-between items-start pt-4">
          <div className="flex flex-col space-y-2">
            <p className="text-sm font-semibold text-gray-500 tracking-wide">{currentDate}</p>
            {isClient && userData ? (
              <>
                <h1 className="text-3xl font-bold text-gray-900 tracking-tight">
                  <span className="text-[#2563eb]">{userData.name}</span> 님,
                </h1>
                <p className="text-gray-600 text-base font-medium">오늘은 <span className="text-[#2563eb] font-bold">{userData.goal}</span>을 목표로 달려봐요!</p>
              </>
            ) : (
              <div className="h-[72px]"></div>
            )}
          </div>
          <button 
            onClick={() => setIsPlannerOpen(true)}
            className="px-3 py-3 bg-white rounded-2xl shadow-[0_2px_12px_-4px_rgba(0,0,0,0.06)] border border-gray-100/60 text-[#2563eb] hover:bg-blue-50 hover:-translate-y-0.5 transition-all flex flex-col items-center justify-center min-w-[76px]"
          >
            <Calendar className="w-6 h-6 mb-1" />
            <span className="text-[10px] font-bold">나의 플래너</span>
          </button>
        </header>

        {/* Dashboard Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Steps Card */}
          <div className="bg-white p-6 rounded-2xl shadow-[0_2px_12px_-4px_rgba(0,0,0,0.06)] border border-gray-100/60 flex flex-col justify-between hover:shadow-[0_8px_24px_-4px_rgba(37,99,235,0.12)] hover:-translate-y-1 transition-all duration-300">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div className="w-11 h-11 rounded-xl bg-blue-50 flex items-center justify-center text-[#2563eb]">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h2 className="text-base font-bold text-gray-800 tracking-wide">오늘의 걸음 수</h2>
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
          <div className="bg-white p-6 rounded-2xl shadow-[0_2px_12px_-4px_rgba(0,0,0,0.06)] border border-gray-100/60 flex flex-col justify-between hover:shadow-[0_8px_24px_-4px_rgba(37,99,235,0.12)] hover:-translate-y-1 transition-all duration-300">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div className="w-11 h-11 rounded-xl bg-orange-50 flex items-center justify-center text-orange-500">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" />
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
                <div className="w-full bg-gray-100 rounded-full h-1.5 flex-1 max-w-[120px]">
                  <div className="bg-orange-500 h-1.5 rounded-full" style={{ width: '60%' }}></div>
                </div>
                <p className="text-sm text-gray-500 font-semibold ml-2">60% 달성</p>
              </div>
            </div>
          </div>

          {/* Sleep Card */}
          <div className="bg-white p-6 rounded-2xl shadow-[0_2px_12px_-4px_rgba(0,0,0,0.06)] border border-gray-100/60 flex flex-col justify-between hover:shadow-[0_8px_24px_-4px_rgba(37,99,235,0.12)] hover:-translate-y-1 transition-all duration-300">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div className="w-11 h-11 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-500">
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
        </div>

        {/* Weekly Chart Placeholder */}
        <section className="bg-white p-6 md:p-8 rounded-2xl shadow-[0_2px_12px_-4px_rgba(0,0,0,0.06)] border border-gray-100/60 mt-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-bold text-gray-900 tracking-wide">주간 활동량</h2>
            <button className="text-sm font-bold text-[#2563eb] hover:text-white hover:bg-[#2563eb] transition-all bg-blue-50 px-4 py-2 rounded-xl">자세히 보기</button>
          </div>

          <div className="w-full h-[280px] bg-gradient-to-br from-gray-50/80 to-gray-100/30 rounded-2xl border border-dashed border-gray-200 flex items-center justify-center relative overflow-hidden group">
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9InJnYmEoMjI2LCAyMzIsIDI0MCwgMC40KSIvPjwvc3ZnPg==')] [mask-image:linear-gradient(to_bottom,white,transparent)]"></div>

            <div className="text-center relative z-10 p-6 bg-white/90 backdrop-blur-md rounded-2xl shadow-sm border border-gray-100 transition-transform group-hover:scale-105 duration-300">
              <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-4 text-[#2563eb] shadow-inner">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <p className="text-gray-900 font-bold mb-1 tracking-wide">주간 차트 영역</p>
              <p className="text-gray-500 text-sm font-medium">데이터를 연결하여 활동량 추이를 확인하세요</p>
            </div>

            {/* Decorative background blocks to look like a placeholder chart */}
            <div className="absolute bottom-0 left-0 right-0 px-10 pt-8 flex justify-between items-end h-full opacity-[0.08] pointer-events-none">
              <div className="w-10 bg-[#2563eb] rounded-t-lg h-[40%]"></div>
              <div className="w-10 bg-[#2563eb] rounded-t-lg h-[65%]"></div>
              <div className="w-10 bg-[#2563eb] rounded-t-lg h-[35%]"></div>
              <div className="w-10 bg-[#2563eb] rounded-t-lg h-[85%]"></div>
              <div className="w-10 bg-[#2563eb] rounded-t-lg h-[55%]"></div>
              <div className="w-10 bg-[#2563eb] rounded-t-lg h-[95%]"></div>
              <div className="w-10 bg-[#2563eb] rounded-t-lg h-[75%]"></div>
            </div>
          </div>
        </section>
      </div>

      {/* Planner Modal */}
      {isPlannerOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-gray-900/40 backdrop-blur-sm" onClick={() => setIsPlannerOpen(false)}></div>
          <div className="bg-white rounded-3xl shadow-[0_20px_60px_-12px_rgba(0,0,0,0.15)] w-full max-w-sm overflow-hidden z-10 animate-in fade-in zoom-in-95 duration-200">
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
          </div>
        </div>
      )}
    </div>
  );
}
