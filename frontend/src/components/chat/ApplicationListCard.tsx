// get_my_applications 결과 카드 — 에이전트가 조회한 내 지원 현황.
// 색은 전부 토큰이라 방 안 패널의 따뜻한 팔레트를 그대로 잇는다.
interface Item {
  application_id?: string;
  company?: string;
  position?: string;
  status_label?: string;
  d_day?: number | null;
  deadline_at?: string | null;
  next_action?: string | null;
  documents?: string[];
}

interface Props {
  data: { total?: number; active_count?: number; items?: Item[]; summary_line?: string };
}

function ddayTone(d: number | null | undefined) {
  if (d === null || d === undefined) return "var(--text-muted)";
  if (d < 0) return "var(--text-muted)";
  if (d <= 3) return "var(--danger)";
  if (d <= 7) return "var(--accent-warm)";
  return "var(--text-secondary)";
}

export default function ApplicationListCard({ data }: Props) {
  const items = data.items ?? [];
  if (!items.length) return null;

  return (
    <div
      style={{
        margin: "10px 0 2px",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-md)",
        background: "var(--bg-card)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          padding: "10px 14px 8px",
          fontSize: 12,
          fontWeight: 700,
          color: "var(--text-white)",
          borderBottom: "1px solid var(--border)",
        }}
      >
        내 지원 현황{" "}
        <span style={{ color: "var(--text-muted)", fontWeight: 500 }}>
          {data.summary_line ?? `${items.length}건`}
        </span>
      </div>

      <ul style={{ margin: 0, padding: "6px 0", listStyle: "none" }}>
        {items.map((it, i) => (
          <li
            key={it.application_id ?? i}
            style={{
              padding: "7px 14px",
              display: "flex",
              alignItems: "baseline",
              gap: 8,
              flexWrap: "wrap",
              fontSize: 13,
            }}
          >
            <span style={{ fontWeight: 700, color: "var(--text-primary)" }}>{it.company}</span>
            <span style={{ color: "var(--text-secondary)", fontSize: 12 }}>{it.position}</span>
            <span
              style={{
                fontSize: 10,
                fontWeight: 600,
                color: "var(--accent-link)",
                background: "rgba(126,184,224,0.14)",
                padding: "1px 7px",
                borderRadius: 9,
              }}
            >
              {it.status_label}
            </span>
            {it.d_day !== null && it.d_day !== undefined && (
              <span style={{ marginLeft: "auto", fontSize: 11, fontWeight: 700, color: ddayTone(it.d_day) }}>
                {it.d_day < 0 ? "마감 지남" : it.d_day === 0 ? "D-DAY" : `D-${it.d_day}`}
              </span>
            )}
            {it.next_action && (
              <div style={{ flexBasis: "100%", fontSize: 11, color: "var(--accent-warm)" }}>
                {it.next_action}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
