interface Props {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
}

export function MessageInput({ value, onChange, onSend }: Props) {
  return (
    <div style={{ padding: "12px 16px", borderTop: "1px solid #383a3f" }}>
      <div
        style={{
          display: "flex",
          background: "#222529",
          borderRadius: 8,
          border: "1px solid #383a3f",
          padding: "8px 12px",
        }}
      >
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSend()}
          placeholder="메시지를 입력하세요..."
          style={{
            flex: 1,
            background: "transparent",
            border: "none",
            outline: "none",
            color: "#d1d2d3",
            fontSize: 15,
          }}
        />
        <button
          onClick={onSend}
          style={{
            background: value.trim() ? "#007a5a" : "#383a3f",
            color: "white",
            border: "none",
            borderRadius: 4,
            padding: "4px 12px",
            cursor: value.trim() ? "pointer" : "default",
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
