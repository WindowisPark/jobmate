import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "@/utils/api";
import { useAuthStore } from "@/stores/authStore";
import styles from "./Auth.module.css";

export function RegisterPage() {
  const navigate = useNavigate();
  const setUser = useAuthStore((s) => s.setUser);

  const [email, setEmail] = useState("");
  const [emailChecked, setEmailChecked] = useState<boolean | null>(null);
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [nickname, setNickname] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const checkEmail = async () => {
    if (!email.includes("@")) {
      setError("올바른 이메일을 입력해주세요");
      return;
    }
    try {
      await api.post("/auth/check-email", { email });
      setEmailChecked(true);
      setError("");
    } catch (err: any) {
      setEmailChecked(false);
      setError(err.message || "이미 등록된 이메일입니다");
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    if (password.length > 60) {
      setError("비밀번호는 60자 이내로 입력해주세요");
      return;
    }

    if (password !== passwordConfirm) {
      setError("비밀번호가 일치하지 않습니다");
      return;
    }

    setLoading(true);

    try {
      const user = await api.post<{
        id: string;
        email: string;
        nickname: string;
        avatar_url: string | null;
      }>("/auth/register", { email, password, nickname });

      setUser(user);
      navigate("/");
    } catch (err: any) {
      setError(err.message || "회원가입에 실패했습니다");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1 className={styles.title}>JobMate</h1>
        <p className={styles.subtitle}>회원가입</p>

        <form onSubmit={handleSubmit} className={styles.form}>
          <input
            type="text"
            placeholder="닉네임"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            className={styles.input}
            required
            minLength={2}
            maxLength={50}
          />
          <div className={styles.inputRow}>
            <input
              type="email"
              placeholder="이메일"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setEmailChecked(null);
              }}
              className={styles.input}
              required
            />
            <button
              type="button"
              onClick={checkEmail}
              className={styles.checkButton}
              disabled={!email.includes("@")}
            >
              중복확인
            </button>
          </div>
          {emailChecked === true && (
            <p className={styles.success}>사용 가능한 이메일입니다</p>
          )}
          <input
            type="password"
            placeholder="비밀번호 (6~60자)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={styles.input}
            required
            minLength={6}
            maxLength={60}
          />
          <input
            type="password"
            placeholder="비밀번호 확인"
            value={passwordConfirm}
            onChange={(e) => setPasswordConfirm(e.target.value)}
            className={styles.input}
            required
            minLength={6}
            maxLength={60}
          />

          {error && <p className={styles.error}>{error}</p>}

          <button type="submit" className={styles.button} disabled={loading}>
            {loading ? "가입 중..." : "회원가입"}
          </button>
        </form>

        <p className={styles.link}>
          이미 계정이 있으신가요? <Link to="/login">로그인</Link>
        </p>
      </div>
    </div>
  );
}
