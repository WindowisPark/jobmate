import type { AgentId } from "@/types/agent";
import { AGENTS } from "@/types/agent";

interface Props {
  agentId: AgentId;
}

export function TypingIndicator({ agentId }: Props) {
  const agent = AGENTS[agentId];

  return (
    <div style={{ display: "flex", gap: 8, marginBottom: 8, alignItems: "center" }}>
      <img
        src={agent.avatarUrl}
        alt={agent.name}
        style={{ width: 36, height: 36, borderRadius: 4, opacity: 0.7 }}
      />
      <div style={{ color: "#9a9b9d", fontSize: 13 }}>
        {agent.name}님이 입력 중...
      </div>
    </div>
  );
}
