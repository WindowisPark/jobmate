// 첨삭이의 이력서/자소서 첨삭 결과 카드.
// resume_feedback 은 구조화된 JSON 을 돌려주는데 화면이 그걸 버리고 있었다(결함 수정).
interface Props {
  data: {
    overall_score?: number;
    strengths?: string[];
    improvements?: string[];
    rewritten_sections?: string[];
  };
}

const MAX_SCORE = 10;

export default function ResumeFeedbackCard({ data }: Props) {
  const score = typeof data.overall_score === "number" ? data.overall_score : null;
  const strengths = data.strengths ?? [];
  const improvements = data.improvements ?? [];
  const rewrites = data.rewritten_sections ?? [];
  if (score === null && !strengths.length && !improvements.length) return null;

  const pct = score === null ? 0 : Math.max(0, Math.min(1, score / MAX_SCORE)) * 100;
  const tone = score !== null && score >= 8 ? "var(--accent-green)"
    : score !== null && score >= 5 ? "var(--accent-warm)" : "var(--danger)";

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
      <div style={{ padding: "12px 14px", borderBottom: "1px solid var(--border)" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 8 }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: "var(--text-white)" }}>첨삭 결과</span>
          {score !== null && (
            <span style={{ fontSize: 13, fontWeight: 700, color: tone }}>
              {score}
              <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 500 }}>{` / ${MAX_SCORE}`}</span>
            </span>
          )}
        </div>
        <div style={{ height: 6, borderRadius: 3, background: "var(--bg-input)", overflow: "hidden" }}>
          <div style={{ width: `${pct}%`, height: "100%", background: tone, transition: "width var(--transition-normal)" }} />
        </div>
      </div>

      <Section title="잘한 점" color="var(--accent-green)" items={strengths} />
      <Section title="고칠 점" color="var(--accent-warm)" items={improvements} />
      <Section title="이렇게 바꿔보면" color="var(--accent-link)" items={rewrites} quoted />
    </div>
  );
}

function Section({ title, color, items, quoted }: { title: string; color: string; items: string[]; quoted?: boolean }) {
  if (!items.length) return null;
  return (
    <div style={{ padding: "10px 14px", borderTop: "1px solid var(--border)" }}>
      <div style={{ fontSize: 11, fontWeight: 700, color, marginBottom: 6 }}>{title}</div>
      <ul style={{ margin: 0, paddingLeft: 16, display: "flex", flexDirection: "column", gap: 5 }}>
        {items.map((it, i) => (
          <li
            key={i}
            style={{
              fontSize: 13, lineHeight: 1.6, color: "var(--text-primary)",
              fontStyle: quoted ? "italic" : "normal",
            }}
          >
            {it}
          </li>
        ))}
      </ul>
    </div>
  );
}
