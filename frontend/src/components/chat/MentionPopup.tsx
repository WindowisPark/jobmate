import { AGENTS, AGENT_IDS } from "@/types/agent";
import type { AgentId } from "@/types/agent";

interface Props {
  filter: string;
  onSelect: (agentId: AgentId) => void;
}

export function MentionPopup({ filter, onSelect }: Props) {
  const filtered = AGENT_IDS.filter((id) => {
    if (!filter) return true;
    const a = AGENTS[id];
    return a.name.includes(filter) || a.role.includes(filter);
  });

  if (filtered.length === 0) return null;

  return (
    <div
      style={{
        position: "absolute",
        bottom: "100%",
        left: 20,
        right: 20,
        background: "var(--bg-hover)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)",
        padding: 6,
        marginBottom: 4,
        boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
        zIndex: 100,
        animation: "slideUp 0.15s ease",
      }}
    >
      <div
        style={{
          fontSize: 11,
          color: "var(--text-secondary)",
          padding: "4px 10px",
          fontWeight: 600,
        }}
      >
        멤버 멘션
      </div>
      {filtered.map((id) => {
        const agent = AGENTS[id];
        return (
          <div
            key={id}
            onClick={() => onSelect(id)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "8px 10px",
              borderRadius: "var(--radius-md)",
              cursor: "pointer",
              transition: "background var(--transition-fast)",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg-tertiary)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
          >
            <div
              style={{
                width: 30,
                height: 30,
                borderRadius: "var(--radius-md)",
                background: `${agent.color}22`,
                border: `1.5px solid ${agent.color}44`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 16,
              }}
            >
              {agent.emoji}
            </div>
            <div>
              <div style={{ fontSize: 14, color: agent.color, fontWeight: 600 }}>
                {agent.name}
              </div>
              <div style={{ fontSize: 11, color: "var(--text-secondary)" }}>
                {agent.role} · {agent.personality}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
