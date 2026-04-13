"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Bot,
  Check,
  Loader2,
  Send,
  ThumbsDown,
  ThumbsUp,
  User,
  X,
} from "lucide-react";
import { useRouter } from "next/navigation";

type FeedbackRating = "up" | "down";
type FeedbackReasonCode =
  | "not_helpful"
  | "not_personalized"
  | "incorrect"
  | "too_vague"
  | "tone_issue"
  | "unsafe";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
  clientMessageId?: string;
  sessionId?: string;
  userMessage?: string;
  intent?: string | null;
  feedbackStatus?: "idle" | "submitting" | "submitted" | "error";
  feedbackRating?: FeedbackRating | null;
  feedbackReasonCodes?: FeedbackReasonCode[];
  feedbackComment?: string | null;
};

const CHAT_SESSION_STORAGE_KEY = "healthAppChatSessionId";
const FEEDBACK_REASON_OPTIONS: { code: FeedbackReasonCode; label: string }[] = [
  { code: "not_helpful", label: "도움이 안 됐어요" },
  { code: "not_personalized", label: "내 상황에 안 맞아요" },
  { code: "incorrect", label: "내용이 부정확해요" },
  { code: "too_vague", label: "너무 모호해요" },
  { code: "tone_issue", label: "말투가 별로예요" },
  { code: "unsafe", label: "위험하거나 불편해요" },
];

function getApiBaseUrl() {
  const raw =
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "";
  return raw.endsWith("/") ? raw.slice(0, -1) : raw;
}

function buildApiUrl(path: string) {
  const baseUrl = getApiBaseUrl();
  return baseUrl ? `${baseUrl}${path}` : path;
}

function createClientMessageId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `chat-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
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
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [feedbackModal, setFeedbackModal] = useState<{
    messageId: string;
    selectedReasons: FeedbackReasonCode[];
    comment: string;
    errorMsg: string;
    isSubmitting: boolean;
  } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const storedSessionId = window.sessionStorage.getItem(
      CHAT_SESSION_STORAGE_KEY
    );
    if (storedSessionId) {
      setSessionId(storedSessionId);
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const simulateStreamingResponse = async (
    fullText: string,
    metadata?: Partial<
      Pick<Message, "clientMessageId" | "sessionId" | "userMessage" | "intent">
    >
  ) => {
    const messageId = metadata?.clientMessageId || Date.now().toString();
    setMessages((prev) => [
      ...prev,
      {
        id: messageId,
        role: "assistant",
        content: "",
        isStreaming: true,
        clientMessageId: metadata?.clientMessageId,
        sessionId: metadata?.sessionId,
        userMessage: metadata?.userMessage,
        intent: metadata?.intent ?? null,
        feedbackStatus: metadata?.clientMessageId ? "idle" : undefined,
        feedbackRating: null,
        feedbackReasonCodes: [],
        feedbackComment: null,
      },
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

  const submitFeedback = async (
    message: Message,
    rating: FeedbackRating,
    reasonCodes: FeedbackReasonCode[] = [],
    comment = ""
  ) => {
    if (!message.clientMessageId || !message.sessionId || !message.userMessage) {
      return false;
    }

    const token = localStorage.getItem("healthAppToken");
    if (!token) {
      return false;
    }

    setMessages((prev) =>
      prev.map((item) =>
        item.id === message.id
          ? { ...item, feedbackStatus: "submitting" }
          : item
      )
    );

    try {
      const response = await fetch(buildApiUrl("/api/v1/chat/feedback"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          client_message_id: message.clientMessageId,
          session_id: message.sessionId,
          user_message: message.userMessage,
          assistant_message: message.content,
          rating,
          reason_codes: reasonCodes,
          comment: comment.trim() || null,
          intent: message.intent || null,
        }),
      });

      if (!response.ok) {
        throw new Error("Feedback API request failed.");
      }

      setMessages((prev) =>
        prev.map((item) =>
          item.id === message.id
            ? {
                ...item,
                feedbackStatus: "submitted",
                feedbackRating: rating,
                feedbackReasonCodes: reasonCodes,
                feedbackComment: comment.trim() || null,
              }
            : item
        )
      );
      return true;
    } catch (error) {
      console.error("Chat feedback error:", error);
      setMessages((prev) =>
        prev.map((item) =>
          item.id === message.id
            ? { ...item, feedbackStatus: "error" }
            : item
        )
      );
      return false;
    }
  };

  const handleThumbsUp = async (message: Message) => {
    if (message.feedbackStatus === "submitted") return;
    await submitFeedback(message, "up");
  };

  const openThumbsDownModal = (messageId: string) => {
    const target = messages.find((message) => message.id === messageId);
    if (!target || target.feedbackStatus === "submitted") return;

    setFeedbackModal({
      messageId,
      selectedReasons: target.feedbackReasonCodes || [],
      comment: target.feedbackComment || "",
      errorMsg: "",
      isSubmitting: false,
    });
  };

  const toggleFeedbackReason = (reasonCode: FeedbackReasonCode) => {
    setFeedbackModal((prev) => {
      if (!prev) return prev;

      const exists = prev.selectedReasons.includes(reasonCode);
      return {
        ...prev,
        selectedReasons: exists
          ? prev.selectedReasons.filter((code) => code !== reasonCode)
          : [...prev.selectedReasons, reasonCode],
      };
    });
  };

  const closeFeedbackModal = () => {
    setFeedbackModal(null);
  };

  const handleThumbsDownSubmit = async () => {
    if (!feedbackModal) return;

    const targetMessage = messages.find(
      (message) => message.id === feedbackModal.messageId
    );
    if (!targetMessage) {
      closeFeedbackModal();
      return;
    }

    if (
      feedbackModal.selectedReasons.length === 0 &&
      !feedbackModal.comment.trim()
    ) {
      setFeedbackModal((prev) =>
        prev
          ? {
              ...prev,
              errorMsg: "싫어요 이유를 하나 이상 선택하거나 코멘트를 입력해주세요.",
            }
          : prev
      );
      return;
    }

    setFeedbackModal((prev) =>
      prev
        ? {
            ...prev,
            isSubmitting: true,
            errorMsg: "",
          }
        : prev
    );

    const didSave = await submitFeedback(
      targetMessage,
      "down",
      feedbackModal.selectedReasons,
      feedbackModal.comment
    );

    if (didSave) {
      closeFeedbackModal();
      return;
    }

    setFeedbackModal((prev) =>
      prev
        ? {
            ...prev,
            isSubmitting: false,
            errorMsg: "피드백 저장에 실패했습니다. 다시 시도해주세요.",
          }
        : prev
    );
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        role: "user",
        content: userMessage,
      },
    ]);
    setIsLoading(true);

    try {
      const token = localStorage.getItem("healthAppToken");
      const endpoint = buildApiUrl("/api/v1/chat");

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          message: userMessage,
          ...(sessionId ? { session_id: sessionId } : {}),
        }),
      });

      if (!response.ok) {
        throw new Error("Chat API request failed.");
      }

      const data = await response.json();
      const nextSessionId =
        typeof data.session_id === "string" ? data.session_id : null;
      const effectiveSessionId = nextSessionId || sessionId || null;
      if (nextSessionId) {
        setSessionId(nextSessionId);
        window.sessionStorage.setItem(
          CHAT_SESSION_STORAGE_KEY,
          nextSessionId
        );
      }

      const botText =
        data.response || data.answer || data.message || "응답을 불러오지 못했습니다.";
      const intent = typeof data.intent === "string" ? data.intent : null;

      setIsLoading(false);
      await simulateStreamingResponse(botText, {
        clientMessageId: createClientMessageId(),
        sessionId: effectiveSessionId || undefined,
        userMessage,
        intent,
      });
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
              <p className="text-xs font-semibold text-emerald-600">
                backend-api 연결 중
              </p>
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
                  {message.role === "assistant" &&
                    message.clientMessageId &&
                    !message.isStreaming && (
                      <div className="mt-3 border-t border-gray-100 pt-3">
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-[11px] font-medium text-gray-400">
                            이 답변이 도움이 됐나요?
                          </span>
                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={() => handleThumbsUp(message)}
                              disabled={message.feedbackStatus === "submitting" || message.feedbackStatus === "submitted"}
                              className={`inline-flex items-center justify-center rounded-full border p-2 transition-colors ${
                                message.feedbackRating === "up"
                                  ? "border-emerald-200 bg-emerald-50 text-emerald-600"
                                  : "border-gray-200 bg-white text-gray-400 hover:border-emerald-200 hover:text-emerald-600"
                              } disabled:cursor-not-allowed disabled:opacity-70`}
                              aria-label="좋아요"
                            >
                              <ThumbsUp className="h-3.5 w-3.5" />
                            </button>
                            <button
                              type="button"
                              onClick={() => openThumbsDownModal(message.id)}
                              disabled={message.feedbackStatus === "submitting" || message.feedbackStatus === "submitted"}
                              className={`inline-flex items-center justify-center rounded-full border p-2 transition-colors ${
                                message.feedbackRating === "down"
                                  ? "border-rose-200 bg-rose-50 text-rose-600"
                                  : "border-gray-200 bg-white text-gray-400 hover:border-rose-200 hover:text-rose-600"
                              } disabled:cursor-not-allowed disabled:opacity-70`}
                              aria-label="싫어요"
                            >
                              <ThumbsDown className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        </div>
                        {message.feedbackStatus === "submitted" && (
                          <div className="mt-2 flex items-center gap-1.5 text-[11px] font-semibold text-emerald-600">
                            <Check className="h-3.5 w-3.5" />
                            <span>피드백이 저장되었습니다.</span>
                          </div>
                        )}
                        {message.feedbackStatus === "error" && (
                          <p className="mt-2 text-[11px] font-semibold text-rose-500">
                            피드백 저장에 실패했습니다. 다시 시도해주세요.
                          </p>
                        )}
                      </div>
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

      <AnimatePresence>
        {feedbackModal && (
          <div className="fixed inset-0 z-[120] flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-gray-900/40 backdrop-blur-sm"
              onClick={closeFeedbackModal}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.96, y: 18 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.96, y: 18 }}
              transition={{ type: "spring", damping: 24, stiffness: 280 }}
              className="relative z-10 w-full max-w-md overflow-hidden rounded-3xl border border-gray-100 bg-white shadow-[0_20px_60px_-12px_rgba(0,0,0,0.15)]"
            >
              <div className="flex items-center justify-between border-b border-gray-100 bg-gray-50/70 px-6 py-5">
                <div>
                  <h2 className="text-lg font-bold text-gray-900">
                    싫어요 이유를 알려주세요
                  </h2>
                  <p className="mt-1 text-sm font-medium text-gray-500">
                    답변 개선에만 사용됩니다.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={closeFeedbackModal}
                  className="rounded-full border border-gray-100 bg-white p-2 text-gray-400 transition-colors hover:text-gray-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-5 px-6 py-6">
                <div className="flex flex-wrap gap-2">
                  {FEEDBACK_REASON_OPTIONS.map((reason) => {
                    const isSelected = feedbackModal.selectedReasons.includes(
                      reason.code
                    );

                    return (
                      <button
                        key={reason.code}
                        type="button"
                        onClick={() => toggleFeedbackReason(reason.code)}
                        className={`rounded-full border px-4 py-2 text-sm font-semibold transition-colors ${
                          isSelected
                            ? "border-rose-200 bg-rose-50 text-rose-600"
                            : "border-gray-200 bg-white text-gray-600 hover:border-rose-200 hover:text-rose-600"
                        }`}
                      >
                        {reason.label}
                      </button>
                    );
                  })}
                </div>

                <div>
                  <label className="mb-2 block text-sm font-semibold text-gray-700">
                    추가 의견
                  </label>
                  <textarea
                    value={feedbackModal.comment}
                    onChange={(event) =>
                      setFeedbackModal((prev) =>
                        prev
                          ? {
                              ...prev,
                              comment: event.target.value,
                            }
                          : prev
                      )
                    }
                    rows={4}
                    placeholder="선택 사항입니다. 어떤 점이 아쉬웠는지 알려주세요."
                    className="w-full resize-none rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 transition-all placeholder:text-gray-400 focus:border-rose-300 focus:bg-white focus:outline-none focus:ring-4 focus:ring-rose-100"
                  />
                </div>

                {feedbackModal.errorMsg && (
                  <p className="text-sm font-semibold text-rose-500">
                    {feedbackModal.errorMsg}
                  </p>
                )}
              </div>

              <div className="flex gap-3 border-t border-gray-100 bg-white px-6 py-5">
                <button
                  type="button"
                  onClick={closeFeedbackModal}
                  className="flex-1 rounded-2xl bg-gray-100 py-3 text-sm font-bold text-gray-700 transition-colors hover:bg-gray-200"
                >
                  취소
                </button>
                <button
                  type="button"
                  onClick={handleThumbsDownSubmit}
                  disabled={feedbackModal.isSubmitting}
                  className="flex-1 rounded-2xl bg-rose-500 py-3 text-sm font-bold text-white transition-colors hover:bg-rose-600 disabled:opacity-70"
                >
                  {feedbackModal.isSubmitting ? "저장 중..." : "보내기"}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <div className="relative z-10 border-t border-gray-200/80 bg-white p-4 pb-28 shadow-[0_-4px_30px_rgba(0,0,0,0.04)]">
        <div className="mx-auto max-w-2xl">
          <form onSubmit={handleSubmit} className="flex items-end gap-3">
            <div className="relative flex-1">
              <input
                type="text"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="건강 관련 질문을 입력해주세요"
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
            프론트는 backend-api를 통해 AI 서버와 통신합니다.
          </p>
        </div>
      </div>
    </div>
  );
}
