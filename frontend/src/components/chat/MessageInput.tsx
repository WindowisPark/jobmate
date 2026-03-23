interface Props {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  placeholder?: string;
}

export function MessageInput({ value, onChange, onSend, placeholder }: Props) {
  return (
    <div style={{ padding: "8px 16px 16px" }}>
      <div
        style={{
          display: "flex",
          background: "#222529",
          borderRadius: 8,
          border: "1px solid #565856",
          padding: "10px 14px",
          gap: 8,
        }}
      >
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.nativeEvent.isComposing) {
              e.preventDefault();
              onSend();
            }
          }}
          placeholder={placeholder ?? "메시지를 입력하세요..."}
          style={{
            flex: 1,
            background: "transparent",
            border: "none",
            outline: "none",
            color: "#d1d2d3",
            fontSize: 14,
          }}
        />
        <button
          onClick={onSend}
          disabled={!value.trim()}
          style={{
            background: value.trim() ? "#007a5a" : "#383a3f",
            color: value.trim() ? "#fff" : "#616061",
            border: "none",
            borderRadius: 6,
            padding: "6px 16px",
            cursor: value.trim() ? "pointer" : "default",
            fontWeight: 700,
            fontSize: 13,
          }}
        >
          전송
        </button>
      </div>
    </div>
  );
}
