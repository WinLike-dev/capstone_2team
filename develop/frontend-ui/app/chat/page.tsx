"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Bot, Loader2, Send, User } from "lucide-react";
import { useRouter } from "next/navigation";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
};

function getApiBaseUrl() {
  const raw =
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "";
  return raw.endsWith("/") ? raw.slice(0, -1) : raw;
}

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "안녕하세요. 건강, 식단, 운동 계획에 대해 편하게 물어보세요.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const simulateStreamingResponse = async (fullText: string) => {
    const messageId = Date.now().toString();
    setMessages((prev) => [
      ...prev,
      { id: messageId, role: "assistant", content: "", isStreaming: true },
    ]);

    let currentText = "";
    const chars = fullText.split("");

    for (let i = 0; i < chars.length; i += 1) {
      const delay = chars[i] === " " ? 20 : Math.random() * 30 + 10;
      await new Promise((resolve) => setTimeout(resolve, delay));
      currentText += chars[i];
      setMessages((prev) =>
        prev.map((message) =>
          message.id === messageId
            ? { ...message, content: currentText }
            : message
        )
      );
    }

    setMessages((prev) =>
      prev.map((message) =>
        message.id === messageId
          ? { ...message, isStreaming: false }
          : message
      )
    );
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), role: "user", content: userMessage },
    ]);
    setIsLoading(true);

    try {
      const token = localStorage.getItem("healthAppToken");
      const endpoint = getApiBaseUrl()
        ? `${getApiBaseUrl()}/api/v1/chat`
        : "/api/v1/chat";

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          message: userMessage,
        }),
      });

      if (!response.ok) {
        throw new Error("Chat API request failed.");
      }

      const data = await response.json();
      const botText =
        data.response || data.answer || data.message || "응답을 불러오지 못했습니다.";

      setIsLoading(false);
      await simulateStreamingResponse(botText);
    } catch (error) {
      console.error("Chat API Error:", error);
      setIsLoading(false);
      await simulateStreamingResponse(
        "메시지를 보내는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
      );
    }
  };

  return (
    <div className="flex h-[100dvh] flex-col bg-[#f8fafc] font-sans">
      <header className="sticky top-0 z-10 border-b border-gray-200/60 bg-white/90 px-6 pb-4 pt-12 shadow-sm backdrop-blur-md">
        <div className="mx-auto flex max-w-2xl items-center gap-4">
          <button
            onClick={() => router.push("/")}
            className="rounded-full p-2 text-gray-600 transition-colors hover:bg-gray-100"
          >
            <ArrowLeft className="h-6 w-6" />
          </button>
          <div className="flex items-center gap-3">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-100 to-indigo-100 shadow-inner">
              <Bot className="h-5 w-5 text-[#2563eb]" />
              <span className="absolute -right-1 -top-1 inline-flex h-3 w-3 rounded-full bg-emerald-500" />
            </div>
            <div>
              <h1 className="text-xl font-extrabold tracking-tight text-gray-900">
                AI 건강 비서
              </h1>
              <p className="text-xs font-semibold text-emerald-600">backend-api 경유 연결</p>
            </div>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-6 py-6 pb-32 md:px-8">
        <div className="mx-auto flex min-h-full max-w-2xl flex-col gap-6">
          <AnimatePresence initial={false}>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 12, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.2 }}
                className={`flex max-w-[85%] gap-3 ${
                  message.role === "user"
                    ? "ml-auto flex-row-reverse"
                    : "mr-auto"
                }`}
              >
                <div
                  className={`mt-auto flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full shadow-sm ${
                    message.role === "user"
                      ? "bg-blue-600 text-white"
                      : "border border-gray-200 bg-white text-[#2563eb]"
                  }`}
                >
                  {message.role === "user" ? (
                    <User className="h-4 w-4" />
                  ) : (
                    <Bot className="h-4 w-4" />
                  )}
                </div>

                <div
                  className={`rounded-2xl p-4 text-[15px] leading-relaxed ${
                    message.role === "user"
                      ? "rounded-br-sm bg-[#2563eb] text-white shadow-[0_4px_20px_rgba(37,99,235,0.25)]"
                      : "rounded-bl-sm border border-gray-100/70 bg-white text-gray-800 shadow-[0_4px_20px_rgba(0,0,0,0.06)]"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  {message.isStreaming && (
                    <motion.span
                      animate={{ opacity: [1, 0] }}
                      transition={{ duration: 0.8, repeat: Infinity }}
                      className="ml-1 inline-block h-4 w-1.5 align-middle bg-[#2563eb]"
                    />
                  )}
                </div>
              </motion.div>
            ))}

            {isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mr-auto flex max-w-[85%] gap-3"
              >
                <div className="mt-auto flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border border-gray-200 bg-white text-[#2563eb] shadow-sm">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="flex items-center space-x-2 rounded-2xl rounded-bl-sm border border-gray-100/60 bg-white px-5 py-4 shadow-[0_4px_20px_rgba(0,0,0,0.06)]">
                  <Loader2 className="h-4 w-4 animate-spin text-[#2563eb]" />
                  <span className="text-sm font-medium text-gray-500">
                    응답 생성 중
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} className="h-4" />
        </div>
      </div>

      <div className="relative z-10 border-t border-gray-200/80 bg-white p-4 pb-28 shadow-[0_-4px_30px_rgba(0,0,0,0.04)]">
        <div className="mx-auto max-w-2xl">
          <form onSubmit={handleSubmit} className="flex items-end gap-3">
            <div className="relative flex-1">
              <input
                type="text"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="건강 관련 질문을 입력하세요"
                className="w-full rounded-2xl border border-gray-200 bg-gray-50/80 py-4 pl-5 pr-14 text-[15px] text-gray-900 shadow-inner transition-all placeholder:text-gray-400 focus:border-[#2563eb] focus:bg-white focus:outline-none focus:ring-4 focus:ring-[#2563eb]/15"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="absolute right-2 top-1/2 -translate-y-1/2 rounded-xl bg-[#2563eb] p-2.5 text-white shadow-[0_4px_12px_rgba(37,99,235,0.3)] transition-all hover:bg-blue-700 disabled:opacity-50"
              >
                {isLoading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <Send className="h-5 w-5" />
                )}
              </button>
            </div>
          </form>
          <p className="mt-3 text-center text-[11px] font-medium text-gray-400">
            프론트는 직접 AI 서버가 아니라 backend-api를 통해 연결됩니다.
          </p>
        </div>
      </div>
    </div>
  );
}
