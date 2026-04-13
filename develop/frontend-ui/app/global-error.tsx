'use client';

import { useEffect } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('Global Error caught:', error);
  }, [error]);

  const isChunkError = error.message.includes('Failed to find Server Action') || 
                       error.message.includes('Loading chunk') ||
                       error.message.includes('fetch');

  return (
    <html>
      <body>
        <div className="flex min-h-[100dvh] flex-col items-center justify-center bg-[#f8fafc] p-6 text-center font-sans mt-0 mb-0">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-rose-100 text-rose-500 mb-6 drop-shadow-sm">
            <AlertTriangle className="h-8 w-8" />
          </div>
          <h2 className="mb-3 text-2xl font-extrabold text-gray-900 tracking-tight">
            일시적인 문제가 발생했습니다.
          </h2>
          <p className="mb-8 max-w-sm text-[15px] font-medium leading-relaxed text-gray-500">
            {isChunkError 
              ? '앱의 새로운 업데이트가 배포되어 화면을 새로고침해야 합니다.'
              : '원인을 알 수 없는 에러가 발생했습니다. 잠시 후 다시 시도해주세요.'}
          </p>
          <button
            onClick={
              () => isChunkError ? window.location.reload() : reset()
            }
            className="flex items-center justify-center gap-2 rounded-2xl bg-[#2563eb] px-6 py-3.5 font-bold text-white shadow-[0_8px_20px_rgba(37,99,235,0.25)] transition-all hover:-translate-y-0.5 hover:bg-blue-700 hover:shadow-[0_12px_25px_rgba(37,99,235,0.35)]"
          >
            <RefreshCw className="h-5 w-5" />
            <span>새로고침</span>
          </button>
        </div>
      </body>
    </html>
  );
}
