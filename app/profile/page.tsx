"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { User, Edit3, Target, Bell, LogOut, ChevronRight, CheckCircle2 } from 'lucide-react';

export default function ProfilePage() {
  const router = useRouter();
  const [userData, setUserData] = useState<{name: string, goal: string, email?: string} | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem('healthAppUser');
    if (stored) {
      const parsed = JSON.parse(stored);
      // add a mock email if not present
      if (!parsed.email) parsed.email = 'user@example.com';
      setUserData(parsed);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('healthAppUser');
    router.push('/onboarding');
  };

  const menuItems = [
    { title: '내 건강 정보 수정', icon: Edit3, color: 'text-blue-500', bg: 'bg-blue-50' },
    { title: '운동 목표 설정', icon: Target, color: 'text-purple-500', bg: 'bg-purple-50' },
    { title: '알림 설정', icon: Bell, color: 'text-orange-500', bg: 'bg-orange-50' },
  ];

  return (
    <div className="min-h-screen bg-[#f8fafc] text-gray-900 font-sans p-6 pb-28 md:p-8 lg:p-12">
      <div className="max-w-4xl mx-auto space-y-8 pt-4">
        
        {/* Profile Header */}
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight pl-2">내 정보</h1>

        {/* Profile Summary Card */}
        <div className="bg-white rounded-3xl p-6 shadow-[0_8px_30px_-6px_rgba(0,0,0,0.08)] border border-gray-100 flex items-center space-x-5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-50 rounded-full blur-3xl -mr-10 -mt-10 opacity-60"></div>
          
          <div className="w-20 h-20 bg-gradient-to-br from-[#2563eb] to-indigo-600 rounded-2xl flex items-center justify-center text-white shadow-[0_8px_16px_-4px_rgba(37,99,235,0.4)] relative z-10 shrink-0 transform group-hover:scale-105 transition-transform duration-300">
            <User className="w-10 h-10" strokeWidth={1.5} />
          </div>
          
          <div className="flex-1 relative z-10">
            <div className="flex items-center space-x-2 mb-1">
              <h2 className="text-xl font-bold text-gray-900">{userData ? userData.name : '사용자'} 님</h2>
              <CheckCircle2 className="w-4 h-4 text-[#2563eb]" />
            </div>
            <p className="text-sm text-gray-500 font-medium mb-2">{userData?.email}</p>
            <div className="inline-flex items-center bg-blue-50 px-2.5 py-1 rounded-md">
              <span className="text-[11px] font-extrabold text-[#2563eb] tracking-wide">
                목표: {userData ? userData.goal : '건강 유지'}
              </span>
            </div>
          </div>
        </div>

        {/* Menu List */}
        <div className="bg-white rounded-3xl shadow-[0_4px_20px_-6px_rgba(0,0,0,0.06)] border border-gray-100 overflow-hidden">
          {menuItems.map((item, idx) => (
            <button 
              key={idx} 
              className={`w-full flex items-center p-5 hover:bg-gray-50 transition-colors ${idx !== menuItems.length - 1 ? 'border-b border-gray-100' : ''}`}
            >
              <div className={`w-10 h-10 rounded-xl ${item.bg} ${item.color} flex items-center justify-center mr-4`}>
                <item.icon className="w-5 h-5" />
              </div>
              <span className="font-bold text-gray-800 text-[16px] flex-1 text-left">{item.title}</span>
              <ChevronRight className="w-5 h-5 text-gray-400" />
            </button>
          ))}
        </div>

        {/* Logout Button */}
        <div className="pt-2">
          <button 
            onClick={handleLogout}
            className="w-full flex items-center justify-center p-5 bg-white rounded-2xl shadow-[0_4px_16px_-6px_rgba(0,0,0,0.05)] border border-gray-100 text-red-500 hover:bg-red-50 hover:text-red-600 transition-all font-bold group"
          >
            <LogOut className="w-5 h-5 mr-2 group-hover:-translate-x-1 transition-transform" />
            로그아웃
          </button>
        </div>

      </div>
    </div>
  );
}
