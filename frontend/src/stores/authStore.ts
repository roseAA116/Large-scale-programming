import { create } from "zustand";

import { AuthSession, User, setApiAccessToken } from "../api/client";

const TOKEN_KEY = "course_agent_access_token";
const USER_KEY = "course_agent_user";

type AuthState = {
  accessToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  setSession: (session: AuthSession) => void;
  updateUser: (user: User) => void;
  clearSession: () => void;
};

function readInitialToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(TOKEN_KEY);
}

function readInitialUser(): User | null {
  if (typeof window === "undefined") {
    return null;
  }

  const rawUser = window.localStorage.getItem(USER_KEY);
  if (!rawUser) {
    return null;
  }

  try {
    return JSON.parse(rawUser) as User;
  } catch {
    window.localStorage.removeItem(USER_KEY);
    return null;
  }
}

const initialToken = readInitialToken();
setApiAccessToken(initialToken);

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: initialToken,
  user: readInitialUser(),
  isAuthenticated: Boolean(initialToken),
  setSession: (session) => {
    window.localStorage.setItem(TOKEN_KEY, session.access_token);
    window.localStorage.setItem(USER_KEY, JSON.stringify(session.user));
    setApiAccessToken(session.access_token);
    set({
      accessToken: session.access_token,
      user: session.user,
      isAuthenticated: true
    });
  },
  updateUser: (user) => {
    window.localStorage.setItem(USER_KEY, JSON.stringify(user));
    set({ user });
  },
  clearSession: () => {
    window.localStorage.removeItem(TOKEN_KEY);
    window.localStorage.removeItem(USER_KEY);
    setApiAccessToken(null);
    set({ accessToken: null, user: null, isAuthenticated: false });
  }
}));
