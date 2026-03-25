import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "@/components/common/Layout";
import { Onboarding } from "@/components/common/Onboarding";
import { LoginPage } from "@/components/auth/LoginPage";
import { RegisterPage } from "@/components/auth/RegisterPage";
import { useAuthStore } from "@/stores/authStore";
import { api } from "@/utils/api";

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
  const { setUser, setGuest, setLoading } = useAuthStore();

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
  );
}
