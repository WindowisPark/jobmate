import { Component, useEffect, useState } from "react";
import type { ErrorInfo, ReactNode } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "@/components/common/Layout";
import { Onboarding } from "@/components/common/Onboarding";
import { LoginPage } from "@/components/auth/LoginPage";
import { RegisterPage } from "@/components/auth/RegisterPage";
import { useAuthStore } from "@/stores/authStore";
import { api } from "@/utils/api";


class ErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100vh", gap: 16, background: "var(--bg-primary)", color: "var(--text-primary)" }}>
          <h2>오류가 발생했습니다</h2>
          <p style={{ color: "var(--text-secondary)" }}>페이지를 새로고침해주세요.</p>
          <button
            onClick={() => window.location.reload()}
            style={{ padding: "8px 24px", background: "var(--accent-blue)", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer" }}
          >
            새로고침
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, isGuest, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", background: "var(--bg-primary)", color: "var(--text-secondary)" }}>
        로딩 중...
      </div>
    );
  }

  if (!user && !isGuest) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function AppContent() {
  const { user, isGuest } = useAuthStore();

  const [showOnboarding, setShowOnboarding] = useState(() => {
    return !localStorage.getItem("jobmate_onboarded");
  });

  const handleOnboardingComplete = () => {
    localStorage.setItem("jobmate_onboarded", "true");
    setShowOnboarding(false);
  };

  if (showOnboarding && (user || isGuest)) {
    return <Onboarding onComplete={handleOnboardingComplete} />;
  }

  return <Layout />;
}

export default function App() {
  const { setUser, setLoading } = useAuthStore();

  useEffect(() => {
    // 페이지 로드 시 쿠키로 인증 상태 확인
    api
      .get<{ id: string; email: string; nickname: string; avatar_url: string | null }>("/auth/me")
      .then((user) => setUser(user))
      .catch(() => {
        // 쿠키 없음 → 미인증 상태로 유지
        setLoading(false);
      });
  }, [setUser, setLoading]);

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/*"
            element={
              <AuthGuard>
                <AppContent />
              </AuthGuard>
            }
          />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
