"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';

export default function OnboardingPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    gender: '남성',
    height: '',
    weight: '',
    goal: '건강 유지',
    activityLevel: '보통',
    mbti: '',
    conditions: [] as string[],
    allergies: [] as string[],
    otherAllergy: '',
  });

  const [errorMsg, setErrorMsg] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const conditionOptions = ['고혈압', '당뇨', '관절염', '천식', '심혈관 질환', '없음'];
  const allergyOptions = ['유제품', '견과류', '갑각류', '밀', '대두', '달걀', '해당 없음'];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    if (!formData.name.trim()) return setErrorMsg('이름을 입력해주세요.');
    if (!formData.age || Number(formData.age) <= 0) return setErrorMsg('올바른 나이를 입력해주세요.');
    if (!formData.height || Number(formData.height) <= 0) return setErrorMsg('올바른 키를 입력해주세요.');
    if (!formData.weight || Number(formData.weight) <= 0) return setErrorMsg('올바른 몸무게를 입력해주세요.');
    if (!formData.mbti) return setErrorMsg('MBTI를 선택해주세요.');
    if (formData.conditions.length === 0) return setErrorMsg('기저 질환을 하나 이상 선택해주세요 (해당 없으면 "없음" 선택).');
    if (formData.allergies.length === 0 && !formData.otherAllergy.trim() && !formData.allergies.includes('기타(직접 입력)')) return setErrorMsg('알레르기 정보를 선택해주세요 (해당 없으면 "해당 없음" 선택).');

    setIsSubmitting(true);
    try {
      const height = parseFloat(formData.height);
      const weight = parseFloat(formData.weight);
      let bmi = 0;
      if (height > 0) {
        bmi = Math.round((weight / ((height / 100) * (height / 100))) * 10) / 10;
      }

      const genderStr = formData.gender === '남성' ? 'male' : 'female';

      const payload = {
        user_id: formData.name, // 로그인 구현 전이라 이름을 id로 임시 사용
        mbti: formData.mbti,
        gender: genderStr,
        age: parseInt(formData.age, 10),
        height,
        weight,
        bmi,
        goal: formData.goal,
        activity_level: formData.activityLevel,
        medical_history: formData.conditions,
        allergies: formData.allergies,
        user_instruction: formData.otherAllergy ? `기타 알레르기: ${formData.otherAllergy}` : ''
      };

      const rawApiUrl = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || '';
      if (!rawApiUrl) {
        console.error('API 주소가 설정되지 않았습니다');
      }

      const baseUrl = rawApiUrl.endsWith('/') ? rawApiUrl.slice(0, -1) : rawApiUrl;
      const endpoint = baseUrl.endsWith('/api/v1') 
        ? `${baseUrl}/users/profile` 
        : `${baseUrl}/api/v1/users/profile`;

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error('API 연동 실패');
      }

      alert('등록이 완료되었습니다.');
      localStorage.setItem('healthAppUser', JSON.stringify(formData));
      router.push('/');
    } catch (error) {
      console.error(error);
      setErrorMsg('프로필 저장에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleCheckboxChange = (condition: string) => {
    setFormData(prev => {
      let newConditions = [...prev.conditions];

      if (condition === '없음') {
        newConditions = prev.conditions.includes('없음') ? [] : ['없음'];
      } else {
        newConditions = newConditions.filter(c => c !== '없음');
        if (newConditions.includes(condition)) {
          newConditions = newConditions.filter(c => c !== condition);
        } else {
          newConditions.push(condition);
        }
      }
      return { ...prev, conditions: newConditions };
    });
  };

  const handleAllergyChange = (allergy: string) => {
    setFormData(prev => {
      let newAllergies = [...prev.allergies];

      if (allergy === '해당 없음') {
        newAllergies = prev.allergies.includes('해당 없음') ? [] : ['해당 없음'];
        return { ...prev, allergies: newAllergies, otherAllergy: '' };
      } else {
        newAllergies = newAllergies.filter(a => a !== '해당 없음');
        if (newAllergies.includes(allergy)) {
          newAllergies = newAllergies.filter(a => a !== allergy);
        } else {
          newAllergies.push(allergy);
        }
      }
      return { ...prev, allergies: newAllergies };
    });
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-gray-900 font-sans p-6 py-12 flex flex-col items-center justify-center">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md space-y-6 bg-white p-8 rounded-[32px] shadow-[0_8px_40px_rgba(0,0,0,0.06)] border border-gray-100"
      >
        <header className="text-center space-y-3 mb-6">
          <div className="w-16 h-16 bg-blue-50/80 rounded-2xl flex items-center justify-center mx-auto mb-3 text-[#2563eb] shadow-sm">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          </div>
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">AI 헬스케어</h1>
          <p className="text-gray-500 font-medium text-sm">보다 정확한 맞춤형 관리를 위해<br />추가 정보를 입력해주세요.</p>
        </header>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Name & Gender */}
          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-2 space-y-1.5 focus-within:text-[#2563eb] transition-colors">
              <label className="text-sm font-bold ml-1 transition-colors">이름</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className="w-full px-5 py-3.5 rounded-xl bg-gray-50/80 border border-gray-200 focus:outline-none focus:ring-4 focus:ring-[#2563eb]/15 focus:bg-white focus:border-[#2563eb] transition-all font-medium placeholder-gray-400 text-gray-900"
                placeholder="홍길동"
              />
            </div>
            <div className="col-span-1 space-y-1.5 focus-within:text-[#2563eb] transition-colors">
              <label className="text-sm font-bold ml-1 transition-colors">성별</label>
              <div className="relative">
                <select
                  name="gender"
                  value={formData.gender}
                  onChange={handleChange}
                  className="w-full px-5 py-3.5 rounded-xl bg-gray-50/80 border border-gray-200 focus:outline-none focus:ring-4 focus:ring-[#2563eb]/15 focus:bg-white focus:border-[#2563eb] transition-all appearance-none font-medium text-gray-900"
                >
                  <option value="남성">남성</option>
                  <option value="여성">여성</option>
                </select>
                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          {/* Age & Height */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5 focus-within:text-[#2563eb]">
              <label className="text-sm font-bold ml-1 transition-colors">나이</label>
              <div className="relative">
                <input
                  type="number"
                  name="age"
                  value={formData.age}
                  onChange={handleChange}
                  className="w-full pl-5 pr-10 py-3.5 rounded-xl bg-gray-50/80 border border-gray-200 focus:outline-none focus:ring-4 focus:ring-[#2563eb]/15 focus:bg-white focus:border-[#2563eb] transition-all font-medium text-gray-900"
                  placeholder="25"
                />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 font-medium">세</span>
              </div>
            </div>
            <div className="space-y-1.5 focus-within:text-[#2563eb]">
              <label className="text-sm font-bold ml-1 transition-colors">키</label>
              <div className="relative">
                <input
                  type="number"
                  name="height"
                  value={formData.height}
                  onChange={handleChange}
                  className="w-full pl-5 pr-10 py-3.5 rounded-xl bg-gray-50/80 border border-gray-200 focus:outline-none focus:ring-4 focus:ring-[#2563eb]/15 focus:bg-white focus:border-[#2563eb] transition-all font-medium text-gray-900"
                  placeholder="175"
                />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 font-medium">cm</span>
              </div>
            </div>
          </div>

          {/* Weight */}
          <div className="space-y-1.5 focus-within:text-[#2563eb]">
            <label className="text-sm font-bold ml-1 transition-colors">몸무게</label>
            <div className="relative">
              <input
                type="number"
                name="weight"
                value={formData.weight}
                onChange={handleChange}
                className="w-full pl-5 pr-10 py-3.5 rounded-xl bg-gray-50/80 border border-gray-200 focus:outline-none focus:ring-4 focus:ring-[#2563eb]/15 focus:bg-white focus:border-[#2563eb] transition-all font-medium text-gray-900"
                placeholder="70"
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 font-medium">kg</span>
            </div>
          </div>

          {/* Goal */}
          <div className="space-y-1.5 focus-within:text-[#2563eb]">
            <label className="text-sm font-bold ml-1 transition-colors">운동 목적</label>
            <div className="relative">
              <select
                name="goal"
                value={formData.goal}
                onChange={handleChange}
                className="w-full px-5 py-3.5 rounded-xl bg-gray-50/80 border border-gray-200 focus:outline-none focus:ring-4 focus:ring-[#2563eb]/15 focus:bg-white focus:border-[#2563eb] transition-all appearance-none font-medium text-gray-900"
              >
                <option value="다이어트">🔥 다이어트</option>
                <option value="근력 향상">💪 근력 향상</option>
                <option value="건강 유지">✨ 건강 유지</option>
              </select>
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          {/* Activity Level */}
          <div className="space-y-1.5 focus-within:text-[#2563eb]">
            <label className="text-sm font-bold ml-1 transition-colors">평소 활동량</label>
            <div className="relative">
              <select
                name="activityLevel"
                value={formData.activityLevel}
                onChange={handleChange}
                className="w-full px-5 py-3.5 rounded-xl bg-gray-50/80 border border-gray-200 focus:outline-none focus:ring-4 focus:ring-[#2563eb]/15 focus:bg-white focus:border-[#2563eb] transition-all appearance-none font-medium text-gray-900"
              >
                <option value="거의 없음">거의 없음 (주로 앉아서 생활)</option>
                <option value="가벼운 활동">가벼운 활동 (주 1~3회 가벼운 운동)</option>
                <option value="보통">보통 (주 3~5회 적당한 운동)</option>
                <option value="격렬한 활동">격렬한 활동 (매일 심한 운동/스포츠)</option>
              </select>
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>
          {/* MBTI */}
          <div className="space-y-1.5 focus-within:text-[#2563eb]">
            <label className="text-sm font-bold ml-1 transition-colors">MBTI</label>
            <div className="relative">
              <select
                name="mbti"
                value={formData.mbti}
                onChange={handleChange}
                className="w-full px-5 py-3.5 rounded-xl bg-gray-50/80 border border-gray-200 focus:outline-none focus:ring-4 focus:ring-[#2563eb]/15 focus:bg-white focus:border-[#2563eb] transition-all appearance-none font-medium text-gray-900"
              >
                <option value="" disabled>선택해주세요</option>
                <option value="INFP">INFP</option>
                <option value="INFJ">INFJ</option>
                <option value="INTP">INTP</option>
                <option value="INTJ">INTJ</option>
                <option value="ISFP">ISFP</option>
                <option value="ISFJ">ISFJ</option>
                <option value="ISTP">ISTP</option>
                <option value="ISTJ">ISTJ</option>
                <option value="ENFP">ENFP</option>
                <option value="ENFJ">ENFJ</option>
                <option value="ENTP">ENTP</option>
                <option value="ENTJ">ENTJ</option>
                <option value="ESFP">ESFP</option>
                <option value="ESFJ">ESFJ</option>
                <option value="ESTP">ESTP</option>
                <option value="ESTJ">ESTJ</option>
              </select>
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          {/* Underlying Conditions */}
          <div className="space-y-2.5 pt-1">
            <label className="text-sm font-bold text-gray-700 ml-1">기저 질환 <span className="text-gray-400 text-xs font-normal ml-1">(다중 선택 가능)</span></label>
            <div className="flex flex-wrap gap-2">
              {conditionOptions.map(condition => (
                <button
                  type="button"
                  key={condition}
                  onClick={() => handleCheckboxChange(condition)}
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${formData.conditions.includes(condition)
                    ? 'bg-[#2563eb] text-white shadow-md shadow-blue-500/20 border-transparent'
                    : 'bg-white text-gray-600 border border-gray-200 hover:border-blue-300 hover:bg-blue-50'
                    }`}
                >
                  {condition}
                </button>
              ))}
            </div>
          </div>

          {/* Allergies */}
          <div className="space-y-2.5 pt-1">
            <label className="text-sm font-bold text-gray-700 ml-1">식품 알레르기 및 주의사항 <span className="text-gray-400 text-xs font-normal ml-1">(다중 선택 가능)</span></label>
            <div className="flex flex-wrap gap-2">
              {allergyOptions.map(allergy => (
                <button
                  type="button"
                  key={allergy}
                  onClick={() => handleAllergyChange(allergy)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${formData.allergies.includes(allergy)
                    ? 'bg-orange-500 text-white shadow-md shadow-orange-500/20 border-transparent'
                    : 'bg-white text-gray-600 border border-gray-200 hover:border-orange-300 hover:bg-orange-50'
                    }`}
                >
                  {allergy}
                </button>
              ))}
              <button
                type="button"
                onClick={() => handleAllergyChange('기타(직접 입력)')}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${formData.allergies.includes('기타(직접 입력)')
                  ? 'bg-orange-500 text-white shadow-md shadow-orange-500/20 border-transparent'
                  : 'bg-white text-gray-600 border border-gray-200 hover:border-orange-300 hover:bg-orange-50'
                  }`}
              >
                기타(직접 입력)
              </button>
            </div>

            {/* Conditional input for 'Other' allergy */}
            {formData.allergies.includes('기타(직접 입력)') && (
              <motion.div
                initial={{ opacity: 0, height: 0, marginTop: 0 }}
                animate={{ opacity: 1, height: 'auto', marginTop: 12 }}
                className="overflow-hidden"
              >
                <input
                  type="text"
                  name="otherAllergy"
                  value={formData.otherAllergy}
                  onChange={handleChange}
                  className="w-full px-5 py-3 rounded-xl bg-orange-50/50 border border-orange-200 focus:outline-none focus:ring-2 focus:ring-orange-500/30 focus:bg-white focus:border-orange-400 transition-all text-sm font-medium placeholder-orange-300 text-gray-900"
                  placeholder="알레르기 정보를 직접 입력해주세요 (예: 복숭아)"
                />
              </motion.div>
            )}
          </div>

          {/* Error Message Container */}
          {errorMsg && (
            <motion.div
              initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }}
              className="p-3 bg-red-50 border border-red-100 rounded-xl flex items-center space-x-2 text-red-600"
            >
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              <span className="text-sm font-bold">{errorMsg}</span>
            </motion.div>
          )}

          <div className="pt-6">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-[#2563eb] text-white font-bold text-lg py-4 rounded-xl shadow-[0_4px_14px_rgba(37,99,235,0.3)] hover:bg-blue-700 hover:shadow-[0_8px_24px_rgba(37,99,235,0.4)] hover:-translate-y-0.5 active:translate-y-0 active:shadow-[0_2px_8px_rgba(37,99,235,0.3)] transition-all duration-300 disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isSubmitting ? '저장 중...' : '시작하기'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}
