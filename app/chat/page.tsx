export default function ChatPage() {
  return (
    <div className="min-h-screen bg-[#f8fafc] text-gray-900 font-sans p-6 pb-24 md:p-8 lg:p-12">
      <div className="max-w-4xl mx-auto space-y-8">
        <header className="flex flex-col space-y-2 pt-4">
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">AI 챗봇</h1>
          <p className="text-gray-600 font-medium">건강에 대한 궁금증을 AI에게 물어보세요.</p>
        </header>
        <div className="bg-white p-6 rounded-2xl shadow-[0_2px_12px_-4px_rgba(0,0,0,0.06)] border border-gray-100/60 min-h-[400px] flex items-center justify-center">
          <p className="text-gray-500">채팅 인터페이스가 들어갈 자리입니다.</p>
        </div>
      </div>
    </div>
  );
}
