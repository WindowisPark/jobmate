import { useToastStore, type ToastType } from "@/stores/toastStore";

const TYPE_STYLES: Record<ToastType, { bg: string; border: string }> = {
  success: { bg: "rgba(0, 122, 90, 0.95)", border: "#00a67d" },
  error: { bg: "rgba(200, 50, 50, 0.95)", border: "#e06c75" },
  warning: { bg: "rgba(180, 140, 40, 0.95)", border: "#e5c07b" },
  info: { bg: "rgba(18, 100, 163, 0.95)", border: "#61afef" },
};

export function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);
  const removeToast = useToastStore((s) => s.removeToast);

  if (toasts.length === 0) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 16,
        right: 16,
        zIndex: 9999,
        display: "flex",
        flexDirection: "column",
        gap: 8,
        maxWidth: 360,
      }}
      role="region"
      aria-label="알림"
      aria-live="polite"
    >
      {toasts.map((t) => {
        const style = TYPE_STYLES[t.type];
        return (
          <div
            key={t.id}
            style={{
              background: style.bg,
              borderLeft: `3px solid ${style.border}`,
              color: "#fff",
              padding: "10px 14px",
              borderRadius: "var(--radius-md)",
              fontSize: "var(--font-base)",
              animation: "slideUp 0.25s ease",
              display: "flex",
              alignItems: "center",
              gap: 10,
              boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
            }}
            role="alert"
          >
            <span style={{ flex: 1 }}>{t.message}</span>
            <button
              onClick={() => removeToast(t.id)}
              style={{
                background: "none",
                border: "none",
                color: "rgba(255,255,255,0.7)",
                cursor: "pointer",
                fontSize: 16,
                padding: "0 2px",
              }}
              aria-label="알림 닫기"
            >
              ×
            </button>
          </div>
        );
      })}
    </div>
  );
}
