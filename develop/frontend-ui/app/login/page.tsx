'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { HeartPulse, Loader2, ArrowRight } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [loginId, setLoginId] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginId || !password) {
      setErrorMsg('아이디와 비밀번호를 모두 입력해주세요.');
      return;
    }

    setErrorMsg('');
    setIsLoading(true);

    try {
      const rawApiUrl = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || '';
      const baseUrl = rawApiUrl.endsWith('/') ? rawApiUrl.slice(0, -1) : rawApiUrl;
      const endpoint = baseUrl ? `${baseUrl}/api/v1/auth/login` : '/api/v1/auth/login';

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true',
        },
        body: JSON.stringify({
          login_id: loginId,
          password: password,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || '아이디 또는 비밀번호가 올바르지 않습니다.');
      }

      // Save token to localStorage
      if (data.token) {
        localStorage.setItem('healthAppToken', data.token);
      }

      // Save minimal user details for client side quick access
      if (data.user) {
        localStorage.setItem('healthAppUser', JSON.stringify({
          user_id: data.user.user_id,
          login_id: data.user.login_id,
          nickname: data.user.nickname,
          email: data.user.email,
        }));
      }

      // Successfully logged in, bypass loop safely
      if (data.user && data.user.has_health_profile === false) {
        router.push('/onboarding');
      } else {
        router.push('/');
      }
    } catch (err: any) {
      console.error('Login error:', err);
      setErrorMsg(err.message || '로그인 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] flex flex-col items-center justify-center p-4 sm:p-6 relative overflow-hidden">
      {/* Decorative Background Elements */}
      <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
      <div className="absolute top-[-10%] right-[-10%] w-96 h-96 bg-indigo-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{ animationDelay: '2s' }}></div>
      <div className="absolute bottom-[-20%] left-[20%] w-96 h-96 bg-emerald-300 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse" style={{ animationDelay: '4s' }}></div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="w-full max-w-md z-10"
      >
        <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.08)] border border-gray-100 p-8 sm:p-10">
          <div className="text-center mb-10">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
              className="w-16 h-16 bg-gradient-to-tr from-blue-600 to-indigo-500 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-[0_8px_20px_rgba(37,99,235,0.25)]"
            >
              <HeartPulse className="w-8 h-8 text-white" />
            </motion.div>
            <h1 className="text-3xl font-extrabold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent tracking-tight">
              Health-mate
            </h1>
            <p className="text-gray-500 mt-2 font-medium">당신의 건강 메이트에 오신 것을 환영합니다</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-1.5" htmlFor="loginId">
                아이디
              </label>
              <input
                id="loginId"
                type="text"
                value={loginId}
                onChange={(e) => setLoginId(e.target.value)}
                placeholder="아이디를 입력해주세요"
                className="w-full px-4 py-3.5 bg-gray-50 border border-gray-200 rounded-2xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 focus:bg-white transition-all duration-200"
                autoComplete="username"
                disabled={isLoading}
              />
            </div>
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-1.5" htmlFor="password">
                비밀번호
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="비밀번호를 입력해주세요"
                className="w-full px-4 py-3.5 bg-gray-50 border border-gray-200 rounded-2xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 focus:bg-white transition-all duration-200"
                autoComplete="current-password"
                disabled={isLoading}
              />
            </div>

            {errorMsg && (
              <motion.p
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="text-sm text-red-500 font-medium text-center bg-red-50 py-2 rounded-xl"
              >
                {errorMsg}
              </motion.p>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-4 mt-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold rounded-2xl shadow-[0_8px_20px_rgba(37,99,235,0.25)] hover:shadow-[0_12px_25px_rgba(37,99,235,0.35)] hover:-translate-y-0.5 transition-all duration-300 disabled:opacity-70 disabled:hover:translate-y-0 disabled:hover:shadow-none flex items-center justify-center space-x-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>로그인 중...</span>
                </>
              ) : (
                <>
                  <span>로그인</span>
                  <ArrowRight className="w-4 h-4 ml-1" />
                </>
              )}
            </button>
          </form>

          <div className="mt-8 text-center text-sm">
            <span className="text-gray-500">아직 회원이 아니신가요? </span>
            <button 
              onClick={() => router.push('/signup')}
              className="text-blue-600 font-bold hover:underline transition-all"
            >
              회원가입 하기
            </button>
          </div>
        </div>
      </motion.div>
      <div className="mt-12 text-center text-sm font-medium text-gray-400 relative z-10">
        © 2026 Health-mate. All rights reserved.
      </div>
    </div>
  );
}
