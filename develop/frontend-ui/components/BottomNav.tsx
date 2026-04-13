"use client";

import { Home, MessageSquare, HeartPulse, User } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function BottomNav() {
  const pathname = usePathname();
  const hiddenRoutes = new Set(['/onboarding', '/login', '/signup']);

  // 인증/온보딩 페이지에서는 네비게이션 바 숨김
  if (hiddenRoutes.has(pathname)) return null;

  const navItems = [
    { name: '홈', path: '/', icon: Home },
    { name: 'AI 챗봇', path: '/chat', icon: MessageSquare },
    { name: '건강 추천', path: '/recommend', icon: HeartPulse },
    { name: '내 정보', path: '/profile', icon: User },
  ];

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white/90 backdrop-blur-md border-t border-gray-200/80 shadow-[0_-4px_24px_-8px_rgba(0,0,0,0.08)] z-50 transition-all duration-300">
      <div className="max-w-md mx-auto px-6 h-20 flex justify-between items-center relative">
        {navItems.map((item) => {
          const isActive = pathname === item.path;
          const Icon = item.icon;
          
          return (
            <Link 
              key={item.path} 
              href={item.path}
              className="relative flex flex-col items-center justify-center w-16 h-full group"
            >
              <div className={`flex flex-col items-center justify-center space-y-1.5 transition-all duration-300 ${isActive ? '-translate-y-1 text-[#2563eb]' : 'text-gray-400 group-hover:text-gray-600 group-hover:-translate-y-0.5'}`}>
                {isActive && (
                  <span className="absolute -top-1 w-8 h-1 bg-[#2563eb] rounded-b-full shadow-[0_2px_8px_rgba(37,99,235,0.4)]" />
                )}
                <Icon className={`w-6 h-6 transition-all duration-300 ${isActive ? 'stroke-[2.5px] scale-110 drop-shadow-sm' : 'stroke-2'}`} />
                <span className={`text-[10px] font-bold tracking-wide ${isActive ? 'opacity-100' : 'opacity-70 group-hover:opacity-100'}`}>
                  {item.name}
                </span>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
