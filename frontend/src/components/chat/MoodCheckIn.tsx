import { useState } from "react";

interface MoodOption {
  emoji: string;
  label: string;
  color: string;
}

const MOODS: MoodOption[] = [
  { emoji: "😊", label: "좋아요", color: "#8dc07a" },
  { emoji: "😐", label: "그저 그래요", color: "#9aa0b0" },
  { emoji: "😰", label: "불안해요", color: "#d98a90" },
  { emoji: "😢", label: "우울해요", color: "#7bb5e0" },
  { emoji: "😤", label: "답답해요", color: "#dfc07a" },
  { emoji: "🤗", label: "희망적이에요", color: "#e8c49a" },
];

interface Props {
  onSelect: (mood: string) => void;
}

export function MoodCheckIn({ onSelect }: Props) {
  const [selected, setSelected] = useState<string | null>(null);
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  const handleSelect = (mood: MoodOption) => {
    setSelected(mood.label);
    onSelect(mood.label);
    setTimeout(() => setDismissed(true), 1500);
  };

  return (
    <div
      style={{
        padding: "16px 20px",
        background: "linear-gradient(135deg, #1e2838 0%, #1b2530 50%, #1e2330 100%)",
        borderBottom: "1px solid var(--border)",
        animation: "fadeIn 0.5s ease",
      }}
    >
      {!selected ? (
        <>
          <div
            style={{
              fontSize: 14,
              color: "var(--text-primary)",
              marginBottom: 12,
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <span style={{
              width: 28,
              height: 28,
              borderRadius: "50%",
              background: "linear-gradient(135deg, var(--agent-ha-eun), #6a9a5a)",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 14,
            }}>
              🌿
            </span>
            오늘 기분이 어떠세요?
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {MOODS.map((mood) => (
              <button
                key={mood.label}
                onClick={() => handleSelect(mood)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "8px 16px",
                  borderRadius: 22,
                  border: "1px solid var(--border)",
                  background: "var(--bg-card)",
                  color: "var(--text-primary)",
                  fontSize: 13,
                  fontWeight: 500,
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = mood.color;
                  e.currentTarget.style.background = `${mood.color}20`;
                  e.currentTarget.style.transform = "translateY(-1px)";
                  e.currentTarget.style.boxShadow = `0 4px 12px ${mood.color}25`;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "var(--border)";
                  e.currentTarget.style.background = "var(--bg-card)";
                  e.currentTarget.style.transform = "translateY(0)";
                  e.currentTarget.style.boxShadow = "none";
                }}
              >
                <span style={{ fontSize: 18 }}>{mood.emoji}</span>
                {mood.label}
              </button>
            ))}
          </div>
        </>
      ) : (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            animation: "fadeIn 0.3s ease",
            padding: "4px 0",
          }}
        >
          <span style={{ fontSize: 20 }}>
            {MOODS.find((m) => m.label === selected)?.emoji}
          </span>
          <span style={{ fontSize: 14, color: "var(--agent-ha-eun)", fontWeight: 500 }}>
            오늘의 기분을 공유해주셔서 고마워요. 편하게 이야기해주세요.
          </span>
        </div>
      )}
    </div>
  );
}
