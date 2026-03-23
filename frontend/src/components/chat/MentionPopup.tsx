import { AGENTS } from "@/types/agent";
import type { AgentId } from "@/types/agent";

const AGENT_COLORS: Record<string, string> = {
  seo_yeon: "#e06c75",
  jun_ho: "#61afef",
  ha_eun: "#98c379",
  min_su: "#e5c07b",
};

interface Props {
  filter: string;
  onSelect: (agentId: AgentId) => void;
  onClose?: () => void;
}

export function MentionPopup({ filter, onSelect }: Props) {
  const agentIds = (Object.keys(AGENTS) as AgentId[]).filter((id) => {
    if (!filter) return true;
    return AGENTS[id].name.includes(filter) || AGENTS[id].role.includes(filter);
  });

  if (agentIds.length === 0) return null;

  return (
    <div
      style={{
        position: "absolute",
        bottom: "100%",
        left: 16,
        right: 16,
        background: "#2b2d31",
        border: "1px solid #383a3f",
        borderRadius: 8,
        padding: 6,
        marginBottom: 4,
        boxShadow: "0 4px 16px rgba(0,0,0,0.4)",
        zIndex: 100,
      }}
    >
      <div
        style={{
          fontSize: 11,
          color: "#9a9b9d",
          padding: "4px 8px",
          fontWeight: 600,
        }}
      >
        멤버 멘션
      </div>
      {agentIds.map((id) => {
        const agent = AGENTS[id];
        const color = AGENT_COLORS[id] ?? "#aaa";
        return (
          <div
            key={id}
            onClick={() => onSelect(id)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "8px 10px",
              borderRadius: 4,
              cursor: "pointer",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.background = "#383a3f")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.background = "transparent")
            }
          >
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: 6,
                background: color + "22",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color,
                fontSize: 13,
                fontWeight: 700,
              }}
            >
              {agent.name[0]}
            </div>
            <div>
              <div style={{ fontSize: 14, color: "#d1d2d3", fontWeight: 500 }}>
                {agent.name}
              </div>
              <div style={{ fontSize: 11, color: "#9a9b9d" }}>
                {agent.role}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
