import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "@/utils/api";
import { useAuthStore } from "@/stores/authStore";
import styles from "./Auth.module.css";

function getPasswordStrength(pw: string): { level: number; label: string; color: string } {
  if (pw.length === 0) return { level: 0, label: "", color: "transparent" };
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[a-z]/.test(pw)) score++;
  if (/\d/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;

  if (score <= 2) return { level: 1, label: "약함", color: "#e06c75" };
  if (score <= 4) return { level: 2, label: "보통", color: "#e5c07b" };
  return { level: 3, label: "강함", color: "#98c379" };
}

function getPasswordErrors(pw: string): string[] {
  const errors: string[] = [];
  if (pw.length > 0 && pw.length < 8) errors.push("8자 이상");
  if (pw.length > 60) errors.push("60자 이내");
  if (pw.length > 0 && !/[A-Za-z]/.test(pw)) errors.push("영문자 포함");
  if (pw.length > 0 && !/\d/.test(pw)) errors.push("숫자 포함");
  return errors;
}

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

  const passwordStrength = getPasswordStrength(password);
  const passwordErrors = getPasswordErrors(password);
  const nicknameError = nickname.length > 0 && nickname.trim().length < 2 ? "닉네임은 2자 이상이어야 합니다" : "";
  const confirmError = passwordConfirm.length > 0 && password !== passwordConfirm ? "비밀번호가 일치하지 않습니다" : "";

  const isFormValid =
    nickname.trim().length >= 2 &&
    emailChecked === true &&
    password.length >= 8 &&
    passwordErrors.length === 0 &&
    password === passwordConfirm;

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
    if (!isFormValid) return;
    setError("");
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
          {/* 닉네임 */}
          <input
            type="text"
            placeholder="닉네임 (2~50자)"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            className={styles.input}
            required
            maxLength={50}
            aria-label="닉네임"
          />
          {nicknameError && <p className={styles.error} style={{ marginTop: -4 }}>{nicknameError}</p>}

          {/* 이메일 */}
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
              aria-label="이메일"
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

          {/* 비밀번호 */}
          <input
            type="password"
            placeholder="비밀번호 (8자 이상, 영문+숫자)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={styles.input}
            required
            maxLength={60}
            aria-label="비밀번호"
          />

          {/* 비밀번호 강도 표시 */}
          {password.length > 0 && (
            <div style={{ marginTop: -4, marginBottom: 4 }}>
              <div style={{ display: "flex", gap: 4, marginBottom: 4 }}>
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    style={{
                      flex: 1,
                      height: 3,
                      borderRadius: 2,
                      background: i <= passwordStrength.level ? passwordStrength.color : "var(--border)",
                      transition: "background 0.2s",
                    }}
                  />
                ))}
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                <span style={{ color: passwordStrength.color }}>{passwordStrength.label}</span>
                {passwordErrors.length > 0 && (
                  <span style={{ color: "#e06c75" }}>
                    {passwordErrors.join(" · ")}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* 비밀번호 확인 */}
          <input
            type="password"
            placeholder="비밀번호 확인"
            value={passwordConfirm}
            onChange={(e) => setPasswordConfirm(e.target.value)}
            className={styles.input}
            required
            maxLength={60}
            aria-label="비밀번호 확인"
          />
          {confirmError && <p className={styles.error} style={{ marginTop: -4 }}>{confirmError}</p>}

          {error && <p className={styles.error}>{error}</p>}

          <button
            type="submit"
            className={styles.button}
            disabled={loading || !isFormValid}
            style={{ opacity: isFormValid && !loading ? 1 : 0.5 }}
          >
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
