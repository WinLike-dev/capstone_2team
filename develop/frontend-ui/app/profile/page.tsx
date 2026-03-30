/* eslint-disable react-hooks/set-state-in-effect */
"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { User, Edit3, Target, Bell, LogOut, ChevronRight, CheckCircle2, HeadphonesIcon, Info, X } from 'lucide-react';
import { motion } from 'framer-motion';

interface UserProfile {
  user_id?: string;
  email?: string;
  name?: string;
  age?: string | number;
  gender?: string;
  height?: string | number;
  weight?: string | number;
  goal?: string;
  activityLevel?: string;
  mbti?: string;
  conditions?: string[];
  allergies?: string[];
  otherAllergy?: string;
  user_instruction?: string;
}

export default function ProfilePage() {
  const router = useRouter();
  const [userData, setUserData] = useState<UserProfile | null>(null);
  
  // Modals state
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isGoalModalOpen, setIsGoalModalOpen] = useState(false);
  const [editForm, setEditForm] = useState<Partial<UserProfile>>({});
  const [editGoal, setEditGoal] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem('healthAppUser');
    if (stored) {
      const parsed = JSON.parse(stored);
      if (!parsed.email) parsed.email = 'user@example.com';
      if (!parsed.user_id) parsed.user_id = parsed.email; // Ensure user_id exists
      if (!parsed.allergies) parsed.allergies = [];
      if (!parsed.conditions) parsed.conditions = [];
      setUserData(parsed);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('healthAppUser');
    router.push('/onboarding');
  };

  const handleOpenEdit = () => {
    setEditForm({
      ...userData,
      conditions: userData?.conditions || [],
      allergies: userData?.allergies || [],
      otherAllergy: userData?.otherAllergy || '',
    });
    setIsEditModalOpen(true);
  };

  const handleOpenGoal = () => {
    setEditGoal(userData?.goal || '');
    setIsGoalModalOpen(true);
  };

  const calculateBMI = (weight: number, height: number) => {
    if (!weight || !height) return 0;
    const heightInMeters = height / 100;
    return Number((weight / (heightInMeters * heightInMeters)).toFixed(1));
  };

  const saveProfileToAPI = async (data: Partial<UserProfile>) => {
    setIsSaving(true);
    try {
      const payload = {
        user_id: data.user_id || data.email || 'unknown',
        mbti: data.mbti || '',
        gender: data.gender || 'male',
        age: Number(data.age) || 0,
        height: Number(data.height) || 0,
        weight: Number(data.weight) || 0,
        bmi: calculateBMI(Number(data.weight), Number(data.height)),
        goal: data.goal || '',
        activity_level: data.activityLevel || '',
        medical_history: data.conditions || [],
        allergies: data.allergies || [],
        user_instruction: data.user_instruction || '',
      };

      const res = await fetch('/api/user/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (!res.ok) {
        console.warn('Failed to save to server, but continuing local update.');
      }
    } catch (error) {
      console.error('API Error:', error);
    } finally {
      setUserData(data);
      localStorage.setItem('healthAppUser', JSON.stringify(data));
      setIsEditModalOpen(false);
      setIsGoalModalOpen(false);
      setIsSaving(false);
    }
  };

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setEditForm((prev: any) => ({ ...prev, [name]: value }));
  };

  const conditionOptions = ['고혈압', '당뇨', '관절염', '천식', '심혈관 질환', '없음'];
  const allergyOptions = ['유제품', '견과류', '갑각류', '밀', '대두', '달걀', '해당 없음'];

  const handleCheckboxChange = (condition: string) => {
    setEditForm((prev: Partial<UserProfile>) => {
      let newConditions: string[] = [...(prev.conditions || [])];
      if (condition === '없음') {
        newConditions = newConditions.includes('없음') ? [] : ['없음'];
      } else {
        newConditions = newConditions.filter((c: string) => c !== '없음');
        if (newConditions.includes(condition)) {
          newConditions = newConditions.filter((c: string) => c !== condition);
        } else {
          newConditions.push(condition);
        }
      }
      return { ...prev, conditions: newConditions };
    });
  };

  const handleAllergyChange = (allergy: string) => {
    setEditForm((prev: Partial<UserProfile>) => {
      let newAllergies: string[] = [...(prev.allergies || [])];
      if (allergy === '해당 없음') {
        newAllergies = newAllergies.includes('해당 없음') ? [] : ['해당 없음'];
        return { ...prev, allergies: newAllergies, otherAllergy: '' };
      } else {
        newAllergies = newAllergies.filter((a: string) => a !== '해당 없음');
        if (newAllergies.includes(allergy)) {
          newAllergies = newAllergies.filter((a: string) => a !== allergy);
        } else {
          newAllergies.push(allergy);
        }
      }
      return { ...prev, allergies: newAllergies };
    });
  };

  const menuItems = [
    { title: '내 정보 수정', icon: Edit3, color: 'text-blue-500', bg: 'bg-blue-50', onClick: handleOpenEdit },
    { title: '운동 목표 설정', icon: Target, color: 'text-purple-500', bg: 'bg-purple-50', onClick: handleOpenGoal },
    { title: '알림 설정', icon: Bell, color: 'text-orange-500', bg: 'bg-orange-50', onClick: () => {} },
    { title: '고객 문의', icon: HeadphonesIcon, color: 'text-green-500', bg: 'bg-green-50', onClick: () => {} },
    { title: '현재 버전 1.0.0', icon: Info, color: 'text-gray-500', bg: 'bg-gray-50', onClick: () => {}, disabled: true },
  ];

  return (
    <div className="min-h-screen h-screen overflow-y-auto bg-[#f8fafc] text-gray-900 font-sans p-6 pb-28 md:p-8 lg:p-12">
      <div className="max-w-4xl mx-auto space-y-8 pt-4 pb-12">
        
        {/* Profile Header */}
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight pl-2">내 정보</h1>

        {/* Profile Summary Card */}
        <div className="bg-white rounded-3xl p-6 shadow-[0_8px_30px_-6px_rgba(0,0,0,0.08)] border border-gray-100 flex items-center space-x-5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-50 rounded-full blur-3xl -mr-10 -mt-10 opacity-60"></div>
          
          <div className="w-20 h-20 bg-gradient-to-br from-[#2563eb] to-indigo-600 rounded-2xl flex items-center justify-center text-white shadow-[0_8px_16px_-4px_rgba(37,99,235,0.4)] relative z-10 shrink-0 transform group-hover:scale-105 transition-transform duration-300">
            <User className="w-10 h-10" strokeWidth={1.5} />
          </div>
          
          <div className="flex-1 relative z-10 w-full">
            <div className="flex items-center space-x-2 mb-1.5">
              <h2 className="text-xl font-bold text-gray-900">{userData ? userData.name : '사용자'}</h2>
              <CheckCircle2 className="w-4 h-4 text-[#2563eb]" />
            </div>
            
            {userData ? (
              <p className="text-[13px] md:text-sm font-semibold text-gray-600 mb-3.5 tracking-tight flex items-center flex-wrap gap-y-1">
                만 {userData.age}세 <span className="text-gray-300 mx-1.5">|</span> 
                {userData.gender} <span className="text-gray-300 mx-1.5">|</span> 
                {userData.height}cm <span className="text-gray-300 mx-1.5">|</span> 
                {userData.weight}kg
              </p>
            ) : (
              <p className="text-sm text-gray-500 font-medium mb-3">user@example.com</p>
            )}
            
            <div className="flex flex-wrap gap-2">
              <div className="inline-flex items-center bg-blue-50 px-2.5 py-1 md:px-3 md:py-1.5 rounded-full border border-blue-100 shadow-sm">
                <span className="text-[10px] md:text-[11px] font-bold text-[#2563eb] tracking-wide">
                  평소 활동량: {userData ? userData.activityLevel : '보통'}
                </span>
              </div>
              <div className="inline-flex items-center bg-purple-50 px-2.5 py-1 md:px-3 md:py-1.5 rounded-full border border-purple-100 shadow-sm">
                <span className="text-[10px] md:text-[11px] font-bold text-purple-600 tracking-wide">
                  목표: {userData ? userData.goal : '건강 유지'}
                </span>
              </div>
              <div className="inline-flex items-center bg-orange-50 px-2.5 py-1 md:px-3 md:py-1.5 rounded-full border border-orange-100 shadow-sm mt-1 md:mt-0">
                <span className="text-[10px] md:text-[11px] font-bold text-orange-600 tracking-wide whitespace-normal">
                  알레르기: {userData && userData.allergies ? (
                    userData.allergies.includes('해당 없음') || (userData.allergies.length === 0 && !userData.otherAllergy)
                      ? '없음'
                      : [
                          ...userData.allergies.filter((a: string) => a !== '기타(직접 입력)' && a !== '해당 없음'),
                          ...(userData.allergies.includes('기타(직접 입력)') && userData.otherAllergy ? [userData.otherAllergy] : [])
                        ].join(', ')
                  ) : '없음'}
                </span>
              </div>
              <div className="inline-flex items-center bg-[#facc15]/15 px-2.5 py-1 md:px-3 md:py-1.5 rounded-full border border-[#facc15]/40 shadow-sm mt-1 md:mt-0">
                <span className="text-[10px] md:text-[11px] font-bold text-[#ca8a04] tracking-wide whitespace-normal">
                  MBTI: {userData?.mbti || '미설정'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Menu List */}
        <div className="bg-white rounded-3xl shadow-[0_4px_20px_-6px_rgba(0,0,0,0.06)] border border-gray-100 overflow-hidden">
          {menuItems.map((item, idx) => (
            <button 
              key={idx} 
              onClick={item.onClick}
              disabled={item.disabled}
              className={`w-full flex items-center p-5 transition-colors ${item.disabled ? 'opacity-60 cursor-not-allowed bg-gray-50' : 'hover:bg-gray-50'} ${idx !== menuItems.length - 1 ? 'border-b border-gray-100' : ''}`}
            >
              <div className={`w-10 h-10 rounded-xl ${item.bg} ${item.color} flex items-center justify-center mr-4`}>
                <item.icon className="w-5 h-5" />
              </div>
              <span className="font-bold text-gray-800 text-[16px] flex-1 text-left">{item.title}</span>
              {!item.disabled && <ChevronRight className="w-5 h-5 text-gray-400" />}
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

      {/* Edit Profile Modal */}
      {isEditModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl w-full max-w-md shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            <div className="flex justify-between items-center p-5 border-b border-gray-100 bg-gray-50/50">
              <h3 className="text-xl font-bold text-gray-900 tracking-tight">내 정보 수정</h3>
              <button onClick={() => setIsEditModalOpen(false)} className="p-2 bg-white rounded-full text-gray-400 hover:text-gray-600 shadow-sm border border-gray-100 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto flex-1 space-y-5 custom-scrollbar max-h-[70vh]">
              <div className="space-y-4 pb-24">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1.5">이름</label>
                  <input type="text" name="name" value={editForm.name || ''} onChange={handleFormChange} className="w-full p-3.5 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all" />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-1.5">나이</label>
                    <input type="number" name="age" value={editForm.age || ''} onChange={handleFormChange} className="w-full p-3.5 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all" />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-1.5">성별</label>
                    <select name="gender" value={editForm.gender || 'male'} onChange={handleFormChange} className="w-full p-3.5 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all appearance-none">
                      <option value="male">남성</option>
                      <option value="female">여성</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-1.5">키 (cm)</label>
                    <input type="number" name="height" value={editForm.height || ''} onChange={handleFormChange} className="w-full p-3.5 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all" />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-1.5">몸무게 (kg)</label>
                    <input type="number" name="weight" value={editForm.weight || ''} onChange={handleFormChange} className="w-full p-3.5 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all" />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1.5">MBTI</label>
                  <select name="mbti" value={editForm.mbti || ''} onChange={handleFormChange} className="w-full p-3.5 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all appearance-none">
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
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1.5">평소 활동량</label>
                  <select name="activityLevel" value={editForm.activityLevel || '보통'} onChange={handleFormChange} className="w-full p-3.5 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all appearance-none">
                    <option value="거의 없음">거의 없음 (주로 앉아서 생활)</option>
                    <option value="가벼운 활동">가벼운 활동 (주 1~3회 가벼운 운동)</option>
                    <option value="보통">보통 (주 3~5회 적당한 운동)</option>
                    <option value="격렬한 활동">격렬한 활동 (매일 심한 운동/스포츠)</option>
                  </select>
                </div>

                {/* Underlying Conditions */}
                <div className="space-y-2.5 pt-1">
                  <label className="text-sm font-bold text-gray-700 mb-1.5 block">기저 질환 <span className="text-gray-400 text-xs font-normal ml-1">(다중 선택 가능)</span></label>
                  <div className="flex flex-wrap gap-2">
                    {conditionOptions.map(condition => (
                      <button
                        type="button"
                        key={condition}
                        onClick={() => handleCheckboxChange(condition)}
                        className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${editForm.conditions?.includes(condition)
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
                  <label className="text-sm font-bold text-gray-700 mb-1.5 block">식품 알레르기 및 주의사항 <span className="text-gray-400 text-xs font-normal ml-1">(다중 선택 가능)</span></label>
                  <div className="flex flex-wrap gap-2">
                    {allergyOptions.map(allergy => (
                      <button
                        type="button"
                        key={allergy}
                        onClick={() => handleAllergyChange(allergy)}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${editForm.allergies?.includes(allergy)
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
                      className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${editForm.allergies?.includes('기타(직접 입력)')
                        ? 'bg-orange-500 text-white shadow-md shadow-orange-500/20 border-transparent'
                        : 'bg-white text-gray-600 border border-gray-200 hover:border-orange-300 hover:bg-orange-50'
                        }`}
                    >
                      기타(직접 입력)
                    </button>
                  </div>

                  {/* Conditional input for 'Other' allergy */}
                  {editForm.allergies?.includes('기타(직접 입력)') && (
                    <motion.div
                      initial={{ opacity: 0, height: 0, marginTop: 0 }}
                      animate={{ opacity: 1, height: 'auto', marginTop: 12 }}
                      className="overflow-hidden"
                    >
                      <input
                        type="text"
                        name="otherAllergy"
                        value={editForm.otherAllergy || ''}
                        onChange={handleFormChange}
                        className="w-full px-5 py-3 rounded-xl bg-orange-50/50 border border-orange-200 focus:outline-none focus:ring-2 focus:ring-orange-500/30 focus:bg-white focus:border-orange-400 transition-all text-sm font-medium placeholder-orange-300 text-gray-900"
                        placeholder="알레르기 정보를 직접 입력해주세요 (예: 복숭아)"
                      />
                    </motion.div>
                  )}
                </div>

              </div>
            </div>

            <div className="p-5 border-t border-gray-100 bg-white">
              <button 
                onClick={() => saveProfileToAPI(editForm)} 
                disabled={isSaving}
                className="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl transition-colors shadow-[0_4px_12px_-4px_rgba(37,99,235,0.4)] disabled:opacity-70 flex justify-center items-center"
              >
                {isSaving ? '저장 중...' : '저장하기'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Goal Modal */}
      {isGoalModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl w-full max-w-sm shadow-2xl overflow-hidden">
            <div className="flex justify-between items-center p-5 border-b border-gray-100 bg-gray-50/50">
              <h3 className="text-xl font-bold text-gray-900 tracking-tight">운동 목표 설정</h3>
              <button onClick={() => setIsGoalModalOpen(false)} className="p-2 bg-white rounded-full text-gray-400 hover:text-gray-600 shadow-sm border border-gray-100 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6">
              <label className="block text-sm font-semibold text-gray-700 mb-2">현재의 건강/운동 목표를 선택해주세요</label>
              <select 
                value={editGoal} 
                onChange={(e) => setEditGoal(e.target.value)} 
                className="w-full p-4 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 transition-all appearance-none"
              >
                <option value="다이어트">🔥 다이어트</option>
                <option value="근력 향상">💪 근력 향상</option>
                <option value="건강 유지">✨ 건강 유지</option>
              </select>
            </div>

            <div className="p-5 border-t border-gray-100 bg-white">
              <button 
                onClick={() => saveProfileToAPI({ ...userData, goal: editGoal })} 
                disabled={isSaving || !editGoal.trim()}
                className="w-full py-4 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-xl transition-colors shadow-[0_4px_12px_-4px_rgba(147,51,234,0.4)] disabled:opacity-70 flex justify-center items-center"
              >
                {isSaving ? '저장 중...' : '목표 저장하기'}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
