import { create } from "zustand";

interface AuthState {
  accessToken: string | null;
  userId: string | null;
  nickname: string | null;
  setAuth: (token: string, userId: string, nickname: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  userId: null,
  nickname: null,

  setAuth: (token, userId, nickname) =>
    set({ accessToken: token, userId, nickname }),

  clearAuth: () =>
    set({ accessToken: null, userId: null, nickname: null }),
}));
