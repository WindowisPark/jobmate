// update_application_status 결과 — 채팅에서 상태를 바꿨을 때.
// ambiguous 가 오면 무엇도 바꾸지 않은 것이므로 그렇게 보여준다.
interface Props {
  data: {
    status?: string;
    company?: string;
    status_label?: string;
    message?: string;
    celebration?: boolean;
    error?: string;
    ambiguous?: { company?: string; position?: string; status_label?: string }[];
  };
}

export default function StatusChangeResult({ data }: Props) {
  if (data.ambiguous?.length) {
    return (
      <Box tone="var(--accent-warm)">
        <b>어느 지원인지 알려주세요</b>
        <ul style={{ margin: "6px 0 0", paddingLeft: 16, fontSize: 12, color: "var(--text-secondary)" }}>
          {data.ambiguous.map((a, i) => (
            <li key={i}>
              {a.company} {a.position} <span style={{ color: "var(--text-muted)" }}>{a.status_label}</span>
            </li>
          ))}
        </ul>
      </Box>
    );
  }

  if (data.error) return <Box tone="var(--danger)">{data.error}</Box>;
  if (data.status !== "updated") return null;

  return (
    <Box tone={data.celebration ? "var(--agent-seo-yeon)" : "var(--accent-green)"}>
      {data.celebration ? "🎉 " : ""}
      {data.message ?? `${data.company} 상태를 ${data.status_label}로 바꿨어요`}
    </Box>
  );
}

function Box({ tone, children }: { tone: string; children: React.ReactNode }) {
  return (
    <div
      style={{
        margin: "10px 0 2px",
        padding: "9px 12px",
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--border)",
        borderLeft: `3px solid ${tone}`,
        background: "var(--bg-card)",
        fontSize: 13,
        lineHeight: 1.6,
        color: "var(--text-primary)",
      }}
    >
      {children}
    </div>
  );
}
