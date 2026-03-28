import { Component, useEffect, useState } from "react";
import type { ErrorInfo, ReactNode } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "@/components/common/Layout";
import { Onboarding } from "@/components/common/Onboarding";
import { LoginPage } from "@/components/auth/LoginPage";
import { RegisterPage } from "@/components/auth/RegisterPage";
import { useAuthStore } from "@/stores/authStore";
import { ToastContainer } from "@/components/common/ToastContainer";
import { api } from "@/utils/api";


function SkeletonBar({ width, height, style }: {
  width: string | number;
  height: number;
  style?: React.CSSProperties;
}) {
  return (
    <div
      style={{
        width,
        height,
        borderRadius: "var(--radius-sm)",
        background: "linear-gradient(90deg, var(--bg-tertiary) 25%, var(--bg-hover) 50%, var(--bg-tertiary) 75%)",
        backgroundSize: "400px 100%",
        animation: "shimmer 1.5s infinite linear",
        ...style,
      }}
    />
  );
}

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
      <div style={{ display: "flex", height: "100vh", background: "var(--bg-primary)" }}>
        {/* 사이드바 스켈레톤 */}
        <div style={{ width: "var(--sidebar-width)", background: "var(--bg-secondary)", padding: 16, borderRight: "1px solid var(--border)" }}>
          <SkeletonBar width="60%" height={24} />
          <div style={{ marginTop: 24 }}>
            <SkeletonBar width="40%" height={12} />
            <SkeletonBar width="80%" height={20} style={{ marginTop: 12 }} />
          </div>
          <div style={{ marginTop: 24 }}>
            <SkeletonBar width="50%" height={12} />
            {[1, 2, 3, 4].map((i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 12 }}>
                <SkeletonBar width={32} height={32} style={{ borderRadius: "var(--radius-md)" }} />
                <div style={{ flex: 1 }}>
                  <SkeletonBar width="60%" height={14} />
                  <SkeletonBar width="40%" height={11} style={{ marginTop: 4 }} />
                </div>
              </div>
            ))}
          </div>
        </div>
        {/* 메인 영역 스켈레톤 */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
          <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--border)" }}>
            <SkeletonBar width="30%" height={20} />
          </div>
          <div style={{ flex: 1, padding: 20 }}>
            {[1, 2, 3].map((i) => (
              <div key={i} style={{ display: "flex", gap: 10, marginBottom: 20 }}>
                <SkeletonBar width={36} height={36} style={{ borderRadius: "var(--radius-md)", flexShrink: 0 }} />
                <div style={{ flex: 1 }}>
                  <SkeletonBar width="20%" height={14} />
                  <SkeletonBar width={`${60 - i * 10}%`} height={16} style={{ marginTop: 6 }} />
                </div>
              </div>
            ))}
          </div>
        </div>
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
      <ToastContainer />
    </ErrorBoundary>
  );
}
