"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';

const conditionOptions = ['고혈압', '당뇨', '관절염', '천식', '심혈관 질환', '없음'];
const allergyOptions = ['유제품', '견과류', '갑각류', '밀', '대두', '계란', '해당 없음'];
const otherAllergyLabel = '기타(직접 입력)';

type FormState = {
  age: string;
  gender: '남성' | '여성';
  height: string;
  weight: string;
  goal: '다이어트' | '근력 향상' | '건강 유지';
  activityLevel: '거의 없음' | '가벼운 운동' | '보통' | '격렬한 운동';
  mbti: string;
  conditions: string[];
  allergies: string[];
  otherAllergy: string;
};

export default function OnboardingPage() {
  const router = useRouter();
  const [formData, setFormData] = useState<FormState>({
    age: '',
    gender: '남성',
    height: '',
    weight: '',
    goal: '건강 유지',
    activityLevel: '보통',
    mbti: '',
    conditions: [],
    allergies: [],
    otherAllergy: '',
  });

  const [errorMsg, setErrorMsg] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    if (!formData.age || Number(formData.age) <= 0) {
      return setErrorMsg('올바른 나이를 입력해주세요.');
    }
    if (!formData.height || Number(formData.height) <= 0) {
      return setErrorMsg('올바른 키를 입력해주세요.');
    }
    if (!formData.weight || Number(formData.weight) <= 0) {
      return setErrorMsg('올바른 몸무게를 입력해주세요.');
    }
    if (!formData.mbti) {
      return setErrorMsg('MBTI를 선택해주세요.');
    }
    if (formData.conditions.length === 0) {
      return setErrorMsg('기저 질환을 하나 이상 선택해주세요. 해당 사항이 없으면 "없음"을 선택하세요.');
    }
    if (
      formData.allergies.length === 0 &&
      !formData.otherAllergy.trim() &&
      !formData.allergies.includes(otherAllergyLabel)
    ) {
      return setErrorMsg('알레르기 정보를 선택해주세요. 해당 사항이 없으면 "해당 없음"을 선택하세요.');
    }

    setIsSubmitting(true);

    try {
      const storedUserRaw = localStorage.getItem('healthAppUser');
      const storedUser = storedUserRaw ? JSON.parse(storedUserRaw) : {};
      const actualUserId = storedUser.user_id || 'unknown';

      const selectedAllergies = formData.allergies.includes(otherAllergyLabel)
        ? [
            ...formData.allergies.filter((item) => item !== otherAllergyLabel),
            ...(formData.otherAllergy.trim() ? [formData.otherAllergy.trim()] : []),
          ]
        : formData.allergies;

      const payload = {
        user_id: actualUserId,
        mbti: formData.mbti,
        gender: formData.gender === '남성' ? 'male' : 'female',
        age: parseInt(formData.age, 10),
        height: parseFloat(formData.height),
        weight: parseFloat(formData.weight),
        bmi: 0,
        goal: formData.goal,
        activity_level: formData.activityLevel,
        medical_history: formData.conditions,
        allergies: selectedAllergies,
      };

      const rawApiUrl = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || '';
      if (!rawApiUrl) {
        console.error('API 주소가 설정되지 않았습니다.');
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
          Authorization: `Bearer ${localStorage.getItem('healthAppToken')}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error('API 연동에 실패했습니다.');
      }

      const responseData = await response.json();
      const finalData = {
        ...formData,
        allergies: selectedAllergies,
        bmi: responseData?.data?.bmi ?? responseData?.bmi ?? 0,
      };

      alert('등록이 완료되었습니다.');
      localStorage.setItem('healthAppUser', JSON.stringify({ ...storedUser, ...finalData }));
      router.push('/');
    } catch (error) {
      console.error(error);
      setErrorMsg('프로필 저장에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleConditionChange = (condition: string) => {
    setFormData((prev) => {
      let nextConditions = [...prev.conditions];

      if (condition === '없음') {
        nextConditions = prev.conditions.includes('없음') ? [] : ['없음'];
      } else {
        nextConditions = nextConditions.filter((item) => item !== '없음');
        nextConditions = nextConditions.includes(condition)
          ? nextConditions.filter((item) => item !== condition)
          : [...nextConditions, condition];
      }

      return { ...prev, conditions: nextConditions };
    });
  };

  const handleAllergyChange = (allergy: string) => {
    setFormData((prev) => {
      let nextAllergies = [...prev.allergies];

      if (allergy === '해당 없음') {
        nextAllergies = prev.allergies.includes('해당 없음') ? [] : ['해당 없음'];
        return { ...prev, allergies: nextAllergies, otherAllergy: '' };
      }

      nextAllergies = nextAllergies.filter((item) => item !== '해당 없음');
      nextAllergies = nextAllergies.includes(allergy)
        ? nextAllergies.filter((item) => item !== allergy)
        : [...nextAllergies, allergy];

      if (!nextAllergies.includes(otherAllergyLabel)) {
        return { ...prev, allergies: nextAllergies, otherAllergy: '' };
      }

      return { ...prev, allergies: nextAllergies };
    });
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#f8fafc] p-6 py-12 font-sans text-gray-900">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md space-y-6 rounded-[32px] border border-gray-100 bg-white p-8 shadow-[0_8px_40px_rgba(0,0,0,0.06)]"
      >
        <header className="mb-6 space-y-3 text-center">
          <div className="mx-auto mb-3 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50/80 text-[#2563eb] shadow-sm">
            <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2.5}
                d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
              />
            </svg>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-gray-900">AI 프로필 설정</h1>
          <p className="text-sm font-medium text-gray-500">
            보다 정확한 맞춤형 관리를 위해
            <br />
            추가 정보를 입력해주세요.
          </p>
        </header>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-1.5">
            <label className="ml-1 text-sm font-bold transition-colors">성별</label>
            <div className="relative">
              <select
                name="gender"
                value={formData.gender}
                onChange={handleChange}
                className="w-full appearance-none rounded-xl border border-gray-200 bg-gray-50/80 px-5 py-3.5 font-medium text-gray-900 transition-all focus:border-[#2563eb] focus:bg-white focus:outline-none focus:ring-4 focus:ring-[#2563eb]/15"
              >
                <option value="남성">남성</option>
                <option value="여성">여성</option>
              </select>
              <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="ml-1 text-sm font-bold transition-colors">나이</label>
              <div className="relative">
                <input
                  type="number"
                  name="age"
                  value={formData.age}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-gray-200 bg-gray-50/80 py-3.5 pl-5 pr-10 font-medium text-gray-900 transition-all focus:border-[#2563eb] focus:bg-white focus:outline-none focus:ring-4 focus:ring-[#2563eb]/15"
                  placeholder="25"
                />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 font-medium text-gray-400">세</span>
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="ml-1 text-sm font-bold transition-colors">키</label>
              <div className="relative">
                <input
                  type="number"
                  name="height"
                  value={formData.height}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-gray-200 bg-gray-50/80 py-3.5 pl-5 pr-10 font-medium text-gray-900 transition-all focus:border-[#2563eb] focus:bg-white focus:outline-none focus:ring-4 focus:ring-[#2563eb]/15"
                  placeholder="175"
                />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 font-medium text-gray-400">cm</span>
              </div>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="ml-1 text-sm font-bold transition-colors">몸무게</label>
            <div className="relative">
              <input
                type="number"
                name="weight"
                value={formData.weight}
                onChange={handleChange}
                className="w-full rounded-xl border border-gray-200 bg-gray-50/80 py-3.5 pl-5 pr-10 font-medium text-gray-900 transition-all focus:border-[#2563eb] focus:bg-white focus:outline-none focus:ring-4 focus:ring-[#2563eb]/15"
                placeholder="70"
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 font-medium text-gray-400">kg</span>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="ml-1 text-sm font-bold transition-colors">운동 목적</label>
            <div className="relative">
              <select
                name="goal"
                value={formData.goal}
                onChange={handleChange}
                className="w-full appearance-none rounded-xl border border-gray-200 bg-gray-50/80 px-5 py-3.5 font-medium text-gray-900 transition-all focus:border-[#2563eb] focus:bg-white focus:outline-none focus:ring-4 focus:ring-[#2563eb]/15"
              >
                <option value="다이어트">다이어트</option>
                <option value="근력 향상">근력 향상</option>
                <option value="건강 유지">건강 유지</option>
              </select>
              <div className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="ml-1 text-sm font-bold transition-colors">평소 활동량</label>
            <div className="relative">
              <select
                name="activityLevel"
                value={formData.activityLevel}
                onChange={handleChange}
                className="w-full appearance-none rounded-xl border border-gray-200 bg-gray-50/80 px-5 py-3.5 font-medium text-gray-900 transition-all focus:border-[#2563eb] focus:bg-white focus:outline-none focus:ring-4 focus:ring-[#2563eb]/15"
              >
                <option value="거의 없음">거의 없음 (주로 앉아서 생활)</option>
                <option value="가벼운 운동">가벼운 운동 (주 1~3회 가벼운 운동)</option>
                <option value="보통">보통 (주 3~5회 중간 강도 운동)</option>
                <option value="격렬한 운동">격렬한 운동 (매일 강도 높은 운동)</option>
              </select>
              <div className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="ml-1 text-sm font-bold transition-colors">MBTI</label>
            <div className="relative">
              <select
                name="mbti"
                value={formData.mbti}
                onChange={handleChange}
                className="w-full appearance-none rounded-xl border border-gray-200 bg-gray-50/80 px-5 py-3.5 font-medium text-gray-900 transition-all focus:border-[#2563eb] focus:bg-white focus:outline-none focus:ring-4 focus:ring-[#2563eb]/15"
              >
                <option value="" disabled>
                  선택해주세요
                </option>
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
              <div className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          <div className="space-y-2.5 pt-1">
            <label className="ml-1 text-sm font-bold text-gray-700">
              기저 질환
              <span className="ml-1 text-xs font-normal text-gray-400">(복수 선택 가능)</span>
            </label>
            <div className="flex flex-wrap gap-2">
              {conditionOptions.map((condition) => (
                <button
                  type="button"
                  key={condition}
                  onClick={() => handleConditionChange(condition)}
                  className={`rounded-xl px-4 py-2 text-sm font-medium transition-all ${
                    formData.conditions.includes(condition)
                      ? 'border-transparent bg-[#2563eb] text-white shadow-md shadow-blue-500/20'
                      : 'border border-gray-200 bg-white text-gray-600 hover:border-blue-300 hover:bg-blue-50'
                  }`}
                >
                  {condition}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2.5 pt-1">
            <label className="ml-1 text-sm font-bold text-gray-700">
              식품 알레르기 및 주의사항
              <span className="ml-1 text-xs font-normal text-gray-400">(복수 선택 가능)</span>
            </label>
            <div className="flex flex-wrap gap-2">
              {allergyOptions.map((allergy) => (
                <button
                  type="button"
                  key={allergy}
                  onClick={() => handleAllergyChange(allergy)}
                  className={`rounded-full px-4 py-2 text-sm font-medium transition-all ${
                    formData.allergies.includes(allergy)
                      ? 'border-transparent bg-orange-500 text-white shadow-md shadow-orange-500/20'
                      : 'border border-gray-200 bg-white text-gray-600 hover:border-orange-300 hover:bg-orange-50'
                  }`}
                >
                  {allergy}
                </button>
              ))}
              <button
                type="button"
                onClick={() => handleAllergyChange(otherAllergyLabel)}
                className={`rounded-full px-4 py-2 text-sm font-medium transition-all ${
                  formData.allergies.includes(otherAllergyLabel)
                    ? 'border-transparent bg-orange-500 text-white shadow-md shadow-orange-500/20'
                    : 'border border-gray-200 bg-white text-gray-600 hover:border-orange-300 hover:bg-orange-50'
                }`}
              >
                {otherAllergyLabel}
              </button>
            </div>

            {formData.allergies.includes(otherAllergyLabel) && (
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
                  className="w-full rounded-xl border border-orange-200 bg-orange-50/50 px-5 py-3 text-sm font-medium text-gray-900 placeholder-orange-300 transition-all focus:border-orange-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-orange-500/30"
                  placeholder="알레르기 정보를 직접 입력해주세요"
                />
              </motion.div>
            )}
          </div>

          {errorMsg && (
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center space-x-2 rounded-xl border border-red-100 bg-red-50 p-3 text-red-600"
            >
              <svg className="h-5 w-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm font-bold">{errorMsg}</span>
            </motion.div>
          )}

          <div className="pt-6">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-xl bg-[#2563eb] py-4 text-lg font-bold text-white shadow-[0_4px_14px_rgba(37,99,235,0.3)] transition-all duration-300 hover:-translate-y-0.5 hover:bg-blue-700 hover:shadow-[0_8px_24px_rgba(37,99,235,0.4)] active:translate-y-0 active:shadow-[0_2px_8px_rgba(37,99,235,0.3)] disabled:cursor-not-allowed disabled:opacity-70"
            >
              {isSubmitting ? '저장 중...' : '시작하기'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}
