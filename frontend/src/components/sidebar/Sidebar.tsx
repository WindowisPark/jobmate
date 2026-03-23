import { AGENTS } from "@/types/agent";
import type { AgentId } from "@/types/agent";

export function Sidebar() {
  const agentIds = Object.keys(AGENTS) as AgentId[];

  return (
    <div
      style={{
        width: 260,
        background: "#19171d",
        borderRight: "1px solid #383a3f",
        display: "flex",
        flexDirection: "column",
        padding: 12,
      }}
    >
      <div style={{ fontSize: 18, fontWeight: 900, color: "#fff", marginBottom: 16 }}>
        JobMate
      </div>

      <div style={{ fontSize: 12, color: "#9a9b9d", marginBottom: 8, textTransform: "uppercase" }}>
        Team Members
      </div>

      {agentIds.map((id) => {
        const agent = AGENTS[id];
        return (
          <div
            key={id}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "6px 8px",
              borderRadius: 4,
              cursor: "pointer",
            }}
          >
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: 4,
                background: "#007a5a",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "white",
                fontSize: 12,
                fontWeight: 700,
              }}
            >
              {agent.name[0]}
            </div>
            <div>
              <div style={{ fontSize: 14, color: "#d1d2d3" }}>{agent.name}</div>
              <div style={{ fontSize: 11, color: "#9a9b9d" }}>{agent.role}</div>
            </div>
          </div>
        );
      })}

      <div
        style={{
          fontSize: 12,
          color: "#9a9b9d",
          marginTop: 24,
          marginBottom: 8,
          textTransform: "uppercase",
        }}
      >
        Channels
      </div>
      <div style={{ padding: "6px 8px", color: "#d1d2d3", fontSize: 14 }}>
        # general
      </div>
    </div>
  );
}
