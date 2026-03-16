"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function OnboardingPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    height: '',
    weight: '',
    goal: '건강 유지',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.age || !formData.height || !formData.weight) {
      alert('모든 정보를 입력해주세요.');
      return;
    }
    
    localStorage.setItem('healthAppUser', JSON.stringify(formData));
    router.push('/');
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-gray-900 font-sans p-6 flex flex-col items-center justify-center">
      <div className="w-full max-w-md space-y-8 bg-white p-8 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] sm:border border-gray-100">
        <header className="text-center space-y-3">
          <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-2 text-[#2563eb]">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">AI 헬스케어</h1>
          <p className="text-gray-500 font-medium text-sm">맞춤형 건강 관리를 위해 정보를 입력해주세요.</p>
        </header>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-1.5">
            <label className="text-sm font-bold text-gray-700 ml-1">이름</label>
            <input 
              type="text" 
              name="name" 
              value={formData.name} 
              onChange={handleChange} 
              className="w-full px-5 py-3.5 rounded-xl bg-gray-50/50 border border-gray-200 focus:outline-none focus:ring-4 focus:ring-[#2563eb]/10 focus:border-[#2563eb] transition-all font-medium placeholder-gray-400"
              placeholder="이름을 입력하세요"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-bold text-gray-700 ml-1">나이</label>
              <div className="relative">
                <input 
                  type="number" 
                  name="age" 
                  value={formData.age} 
                  onChange={handleChange} 
                  className="w-full pl-5 pr-10 py-3.5 rounded-xl bg-gray-50/50 border border-gray-200 focus:outline-none focus:ring-4 focus:ring-[#2563eb]/10 focus:border-[#2563eb] transition-all font-medium"
                  placeholder="25"
                />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 font-medium">세</span>
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-bold text-gray-700 ml-1">키</label>
              <div className="relative">
                <input 
                  type="number" 
                  name="height" 
                  value={formData.height} 
                  onChange={handleChange} 
                  className="w-full pl-5 pr-10 py-3.5 rounded-xl bg-gray-50/50 border border-gray-200 focus:outline-none focus:ring-4 focus:ring-[#2563eb]/10 focus:border-[#2563eb] transition-all font-medium"
                  placeholder="175"
                />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 font-medium">cm</span>
              </div>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-bold text-gray-700 ml-1">몸무게</label>
            <div className="relative">
              <input 
                type="number" 
                name="weight" 
                value={formData.weight} 
                onChange={handleChange} 
                className="w-full pl-5 pr-10 py-3.5 rounded-xl bg-gray-50/50 border border-gray-200 focus:outline-none focus:ring-4 focus:ring-[#2563eb]/10 focus:border-[#2563eb] transition-all font-medium"
                placeholder="70"
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 font-medium">kg</span>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-bold text-gray-700 ml-1">운동 목적</label>
            <div className="relative">
              <select 
                name="goal" 
                value={formData.goal} 
                onChange={handleChange} 
                className="w-full px-5 py-3.5 rounded-xl bg-gray-50/50 border border-gray-200 focus:outline-none focus:ring-4 focus:ring-[#2563eb]/10 focus:border-[#2563eb] transition-all appearance-none font-medium text-gray-700"
              >
                <option value="다이어트">다이어트</option>
                <option value="근력 향상">근력 향상</option>
                <option value="건강 유지">건강 유지</option>
              </select>
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          <div className="pt-4">
            <button 
              type="submit" 
              className="w-full bg-[#2563eb] text-white font-bold text-[17px] py-4 rounded-xl shadow-[0_4px_14px_rgba(37,99,235,0.3)] hover:bg-blue-700 hover:shadow-[0_6px_20px_rgba(37,99,235,0.4)] hover:-translate-y-0.5 active:translate-y-0 active:shadow-none transition-all duration-300"
            >
              시작하기
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
