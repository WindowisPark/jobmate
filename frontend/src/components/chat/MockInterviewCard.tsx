// 첨삭이의 모의 면접 질문 카드. mock_interview 결과도 화면이 버리고 있었다(결함 수정).
interface Question {
  question?: string;
  category?: string;
  tip?: string;
}

interface Props {
  data: { questions?: Question[]; general_tips?: string[] };
}

export default function MockInterviewCard({ data }: Props) {
  const questions = (data.questions ?? []).filter((q) => q.question);
  const tips = data.general_tips ?? [];
  if (!questions.length && !tips.length) return null;

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
      <div style={{ padding: "12px 14px 8px", fontSize: 13, fontWeight: 700, color: "var(--text-white)" }}>
        모의 면접 질문 {questions.length > 0 && <span style={{ color: "var(--text-muted)", fontWeight: 500 }}>{questions.length}개</span>}
      </div>

      <ol style={{ margin: 0, padding: "0 14px 12px 30px", display: "flex", flexDirection: "column", gap: 10 }}>
        {questions.map((q, i) => (
          <li key={i} style={{ fontSize: 13, lineHeight: 1.6, color: "var(--text-primary)" }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 6, flexWrap: "wrap" }}>
              <span style={{ fontWeight: 600 }}>{q.question}</span>
              {q.category && (
                <span
                  style={{
                    fontSize: 10, fontWeight: 600, color: "var(--accent-link)",
                    background: "rgba(126,184,224,0.14)", padding: "1px 7px", borderRadius: 9,
                  }}
                >
                  {q.category}
                </span>
              )}
            </div>
            {q.tip && (
              <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 3 }}>{q.tip}</div>
            )}
          </li>
        ))}
      </ol>

      {tips.length > 0 && (
        <div style={{ padding: "10px 14px", borderTop: "1px solid var(--border)" }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "var(--accent-warm)", marginBottom: 6 }}>기억할 것</div>
          <ul style={{ margin: 0, paddingLeft: 16, display: "flex", flexDirection: "column", gap: 4 }}>
            {tips.map((t, i) => (
              <li key={i} style={{ fontSize: 12, lineHeight: 1.6, color: "var(--text-secondary)" }}>{t}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
