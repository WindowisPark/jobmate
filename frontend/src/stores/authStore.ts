import { create } from "zustand";

interface UserInfo {
  id: string;
  email: string;
  nickname: string;
  avatar_url: string | null;
}

interface AuthState {
  user: UserInfo | null;
  isGuest: boolean;
  isLoading: boolean;

  setUser: (user: UserInfo) => void;
  setGuest: () => void;
  clearAuth: () => void;
  setLoading: (v: boolean) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isGuest: false,
  isLoading: true,

  setUser: (user) => set({ user, isGuest: false, isLoading: false }),
  setGuest: () => set({ user: null, isGuest: true, isLoading: false }),
  clearAuth: () => set({ user: null, isGuest: false, isLoading: false }),
  setLoading: (v) => set({ isLoading: v }),
}));
