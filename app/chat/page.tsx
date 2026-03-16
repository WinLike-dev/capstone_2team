"use client";

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, ArrowLeft, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;
};

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: '안녕하세요! AI 건강 비서입니다. 식단, 운동, 건강 관리에 대해 무엇이든 물어보세요.'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Simulate streaming response
  const simulateStreamingResponse = async (fullText: string) => {
    const messageId = Date.now().toString();
    
    // Add empty message first
    setMessages(prev => [...prev, { id: messageId, role: 'assistant', content: '', isStreaming: true }]);
    
    let currentText = '';
    const chars = fullText.split('');
    
    for (let i = 0; i < chars.length; i++) {
      // Simulate typing delay (faster for spaces, random for chars)
      const delay = chars[i] === ' ' ? 20 : Math.random() * 30 + 10;
      await new Promise(resolve => setTimeout(resolve, delay));
      
      currentText += chars[i];
      setMessages(prev => prev.map(msg => 
        msg.id === messageId ? { ...msg, content: currentText } : msg
      ));
    }
    
    // Finish streaming
    setMessages(prev => prev.map(msg => 
      msg.id === messageId ? { ...msg, isStreaming: false } : msg
    ));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = input.trim();
    setInput('');
    
    // Add user message
    setMessages(prev => [...prev, { id: Date.now().toString(), role: 'user', content: userMsg }]);
    
    // Show loading state
    setIsLoading(true);
    
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    setIsLoading(false);
    
    // Generate dummy contextual response based on keywords
    let responseText = "어떤 말씀인지 잘 이해하지 못했어요. 운동이나 식단에 대해 물어보시면 더 자세히 답변해드릴 수 있습니다.";
    if (userMsg.includes('운동') || userMsg.includes('유산소')) {
      responseText = "오늘의 운동으로는 가벼운 조깅이나 걷기 30분을 추천해 드립니다. 처음부터 무리하지 마시고 점진적으로 강도를 높이는 것이 중요해요!";
    } else if (userMsg.includes('식단') || userMsg.includes('칼로리') || userMsg.includes('먹')) {
      responseText = "식단 관리는 단백질 위주의 식사와 수분 섭취가 핵심입니다. 오늘 저녁은 닭가슴살 샐러드나 탄수화물을 줄인 식단은 어떨까요?";
    } else if (userMsg.includes('안녕')) {
      responseText = "반갑습니다! 오늘 컨디션은 어떠신가요? 건강한 하루를 위해 제가 곁에서 도와드릴게요.";
    }

    // Start streaming effect
    await simulateStreamingResponse(responseText);
  };

  return (
    <div className="flex flex-col h-screen bg-[#f8fafc] font-sans">
      {/* Header */}
      <header className="flex-none pt-12 pb-4 px-6 bg-white/90 backdrop-blur-md border-b border-gray-200/50 shadow-sm z-10 sticky top-0">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => router.push('/')}
              className="p-2 -ml-2 rounded-full hover:bg-gray-100 transition-colors text-gray-600 focus:outline-none focus:ring-2 focus:ring-[#2563eb]/20"
            >
              <ArrowLeft className="w-6 h-6" />
            </button>
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-xl flex items-center justify-center shadow-inner relative">
                <Bot className="w-5 h-5 text-[#2563eb]" />
                <span className="absolute -top-1 -right-1 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
                </span>
              </div>
              <div>
                <h1 className="text-xl font-extrabold text-gray-900 tracking-tight">AI 건강 비서</h1>
                <p className="text-xs font-semibold text-emerald-600 flex items-center">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5"></span>
                  온라인
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-6 md:p-8 custom-scrollbar pb-32">
        <div className="max-w-2xl mx-auto space-y-6 flex flex-col justify-end min-h-full">
          <AnimatePresence initial={false}>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 15, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.3, type: "spring", stiffness: 300, damping: 25 }}
                className={`flex gap-3 max-w-[85%] ${message.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}
              >
                {/* Avatar */}
                <div className={`flex-shrink-0 mt-auto w-8 h-8 rounded-full flex items-center justify-center shadow-sm ${
                  message.role === 'user' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-white border border-gray-200 text-[#2563eb]'
                }`}>
                  {message.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                {/* Message Bubble */}
                <div className={`p-4 rounded-2xl md:rounded-[24px] text-[15px] leading-relaxed relative ${
                  message.role === 'user'
                    ? 'bg-[#2563eb] text-white rounded-br-sm shadow-[0_4px_20px_rgba(37,99,235,0.25)]'
                    : 'bg-white text-gray-800 rounded-bl-sm shadow-[0_4px_20px_rgba(0,0,0,0.06)] border border-gray-100/60'
                }`}>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  
                  {/* Blinking cursor during streaming */}
                  {message.isStreaming && (
                    <motion.span 
                      animate={{ opacity: [1, 0] }} 
                      transition={{ duration: 0.8, repeat: Infinity }}
                      className="inline-block w-1.5 h-4 ml-1 align-middle bg-[#2563eb]"
                    />
                  )}
                </div>
              </motion.div>
            ))}
            
            {/* Loading Indicator */}
            {isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="flex gap-3 max-w-[85%] mr-auto"
              >
                <div className="flex-shrink-0 mt-auto w-8 h-8 rounded-full flex items-center justify-center bg-white border border-gray-200 text-[#2563eb] shadow-sm">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="px-5 py-4 rounded-2xl bg-white rounded-bl-sm shadow-[0_4px_20px_rgba(0,0,0,0.06)] border border-gray-100/60 flex items-center space-x-1.5">
                  <motion.div animate={{ y: [0, -5, 0] }} transition={{ duration: 0.6, repeat: Infinity, delay: 0 }} className="w-2 h-2 rounded-full bg-blue-400" />
                  <motion.div animate={{ y: [0, -5, 0] }} transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }} className="w-2 h-2 rounded-full bg-blue-500" />
                  <motion.div animate={{ y: [0, -5, 0] }} transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }} className="w-2 h-2 rounded-full bg-blue-600" />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} className="h-4" />
        </div>
      </div>

      {/* Input Area */}
      <div className="flex-none bg-white border-t border-gray-200/80 p-4 pb-24 md:pb-6 z-10 shadow-[0_-4px_30px_rgba(0,0,0,0.04)] relative">
        <div className="max-w-2xl mx-auto">
          <form onSubmit={handleSubmit} className="flex gap-3 relative items-end">
            <div className="relative flex-1">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="건강 관련 질문을 자유롭게 남겨주세요..."
                className="w-full bg-gray-50/80 border border-gray-200 rounded-2xl md:rounded-[24px] pl-5 pr-14 py-4 focus:outline-none focus:ring-4 focus:ring-[#2563eb]/15 focus:bg-white focus:border-[#2563eb] transition-all font-medium text-[15px] shadow-inner text-gray-900 placeholder-gray-400"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2.5 bg-[#2563eb] text-white rounded-xl md:rounded-[18px] shadow-[0_4px_12px_rgba(37,99,235,0.3)] hover:bg-blue-700 hover:shadow-[0_6px_16px_rgba(37,99,235,0.4)] disabled:opacity-50 disabled:shadow-none transition-all duration-300 focus:outline-none group"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                )}
              </button>
            </div>
          </form>
          <p className="text-center mt-3 text-[11px] font-medium text-gray-400">
            AI 비서의 조언은 의료 전문가의 진단을 대신할 수 없습니다.
          </p>
        </div>
      </div>
    </div>
  );
}
