import { useRef, useEffect, useCallback } from "react";

const MAX_LENGTH = 2000;

interface Props {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  placeholder?: string;
}

export function MessageInput({ value, onChange, onSend, placeholder }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const sendingRef = useRef(false);

  const handleSend = useCallback(() => {
    if (sendingRef.current || !value.trim()) return;
    sendingRef.current = true;
    onSend();
    setTimeout(() => { sendingRef.current = false; }, 500);
  }, [value, onSend]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  return (
    <div style={{ padding: "8px 20px 20px" }}>
      <div
        style={{
          display: "flex",
          background: "var(--bg-input)",
          borderRadius: "var(--radius-lg)",
          border: "1px solid var(--border-input)",
          padding: "10px 14px",
          gap: 8,
          transition: "border-color var(--transition-fast)",
        }}
        onFocus={(e) => (e.currentTarget.style.borderColor = "var(--accent-blue)")}
        onBlur={(e) => (e.currentTarget.style.borderColor = "var(--border-input)")}
      >
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => {
            if (e.target.value.length <= MAX_LENGTH) onChange(e.target.value);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.nativeEvent.isComposing) {
              e.preventDefault();
              handleSend();
            }
          }}
          maxLength={MAX_LENGTH}
          placeholder={placeholder ?? "메시지를 입력하세요..."}
          style={{
            flex: 1,
            background: "transparent",
            border: "none",
            outline: "none",
            color: "var(--text-primary)",
            fontSize: "var(--font-base)",
          }}
        />
        <button
          onClick={handleSend}
          disabled={!value.trim()}
          style={{
            background: value.trim() ? "var(--accent-green)" : "var(--bg-hover)",
            color: value.trim() ? "#fff" : "var(--text-muted)",
            border: "none",
            borderRadius: "var(--radius-md)",
            padding: "6px 18px",
            cursor: value.trim() ? "pointer" : "default",
            fontWeight: 700,
            fontSize: 13,
            transition: "all var(--transition-fast)",
          }}
        >
          전송
        </button>
      </div>
    </div>
  );
}
