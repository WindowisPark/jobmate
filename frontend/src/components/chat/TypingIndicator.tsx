import type { AgentId } from "@/types/agent";
import { AGENTS } from "@/types/agent";

interface Props {
  agentId: AgentId;
}

export function TypingIndicator({ agentId }: Props) {
  const agent = AGENTS[agentId];

  return (
    <div
      style={{
        display: "flex",
        gap: 10,
        padding: "6px 20px",
        alignItems: "center",
        animation: "fadeIn 0.2s ease",
      }}
    >
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: "var(--radius-lg)",
          background: `${agent.color}22`,
          border: `1.5px solid ${agent.color}44`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 18,
          opacity: 0.7,
        }}
      >
        {agent.emoji}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ color: agent.color, fontSize: 13, fontWeight: 600 }}>
          {agent.name}
        </span>
        <div style={{ display: "flex", gap: 3 }}>
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: agent.color,
                animation: `typingDots 1.2s ${i * 0.2}s infinite`,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
