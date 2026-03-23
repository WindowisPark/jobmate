import type { ChatMessage } from "@/types/chat";
import { AGENTS } from "@/types/agent";

interface Props {
  message: ChatMessage;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.senderType === "user";
  const agent = message.agentId ? AGENTS[message.agentId] : null;

  return (
    <div style={{ display: "flex", gap: 8, marginBottom: 12, alignItems: "flex-start" }}>
      {!isUser && agent && (
        <img
          src={agent.avatarUrl}
          alt={agent.name}
          style={{ width: 36, height: 36, borderRadius: 4 }}
        />
      )}
      <div>
        {!isUser && agent && (
          <div style={{ fontSize: 13, fontWeight: 700, color: "#d1d2d3", marginBottom: 2 }}>
            {agent.name}
            <span style={{ fontWeight: 400, color: "#9a9b9d", marginLeft: 6, fontSize: 11 }}>
              {agent.role}
            </span>
          </div>
        )}
        <div
          style={{
            background: isUser ? "#1264a3" : "transparent",
            color: "#d1d2d3",
            padding: isUser ? "8px 12px" : "4px 0",
            borderRadius: isUser ? 8 : 0,
            fontSize: 15,
            lineHeight: 1.5,
          }}
        >
          {message.content}
        </div>
      </div>
    </div>
  );
}
