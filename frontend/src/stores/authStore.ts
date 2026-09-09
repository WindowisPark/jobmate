import { create } from "zustand";

export interface UserInfo {
  id: string;
  email: string;
  nickname: string;
  avatar_url: string | null;
  /** 게스트도 서버에 진짜 계정이 있다(/api/auth/guest). UI 표기용 플래그 */
  is_guest?: boolean;
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

  setUser: (user) => set({ user, isGuest: !!user.is_guest, isLoading: false }),
  setGuest: () => set({ user: null, isGuest: true, isLoading: false }),
  clearAuth: () => set({ user: null, isGuest: false, isLoading: false }),
  setLoading: (v) => set({ isLoading: v }),
}));
