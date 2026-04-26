export const AUTH_TOKEN_STORAGE_KEY = "healthAppToken";
export const AUTH_USER_STORAGE_KEY = "healthAppUser";
export const CHAT_SESSION_STORAGE_KEY = "healthAppChatSessionId";
export const CHAT_MESSAGES_STORAGE_KEY = "healthAppChatMessages";

export function clearClientAuthState() {
  if (typeof window === "undefined") return;

  localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
  localStorage.removeItem(AUTH_USER_STORAGE_KEY);
  sessionStorage.removeItem(CHAT_SESSION_STORAGE_KEY);
  sessionStorage.removeItem(CHAT_MESSAGES_STORAGE_KEY);
}

export function redirectToLoginForExpiredSession() {
  if (typeof window === "undefined") return;

  clearClientAuthState();

  const loginUrl = "/login?reason=session-expired";
  if (window.location.pathname !== "/login") {
    window.location.replace(loginUrl);
  }
}
