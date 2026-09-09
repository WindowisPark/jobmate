import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "@/utils/api";
import { useAuthStore } from "@/stores/authStore";
import type { UserInfo } from "@/stores/authStore";
import styles from "./Auth.module.css";

export function LoginPage() {
  const navigate = useNavigate();
  const setUser = useAuthStore((s) => s.setUser);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const user = await api.post<UserInfo>("/auth/login", { email, password });

      setUser(user);
      navigate("/");
    } catch (err: any) {
      setError(err.message || "로그인에 실패했습니다");
    } finally {
      setLoading(false);
    }
  };

  const handleGuest = async () => {
    setError("");
    setLoading(true);
    try {
      // 게스트도 서버 계정을 받는다 — 지원 내역 등 개인 데이터가 다른 게스트와 섞이지 않게
      const user = await api.post<UserInfo>("/auth/guest");
      setUser(user);
      navigate("/");
    } catch (err: any) {
      setError(err.message || "게스트 시작에 실패했습니다");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1 className={styles.title}>JobMate</h1>
        <p className={styles.subtitle}>취준생 멘탈 케어 그룹챗</p>

        <form onSubmit={handleSubmit} className={styles.form}>
          <input
            type="email"
            placeholder="이메일"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={styles.input}
            required
          />
          <input
            type="password"
            placeholder="비밀번호"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={styles.input}
            required
          />

          {error && <p className={styles.error}>{error}</p>}

          <button type="submit" className={styles.button} disabled={loading}>
            {loading ? "로그인 중..." : "로그인"}
          </button>
        </form>

        <div className={styles.divider}>
          <span>또는</span>
        </div>

        <button onClick={handleGuest} className={styles.guestButton} disabled={loading}>
          게스트로 체험하기
        </button>

        <p className={styles.link}>
          계정이 없으신가요? <Link to="/register">회원가입</Link>
        </p>
      </div>
    </div>
  );
}
