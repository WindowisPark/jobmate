import type { ChatMessage } from "@/types/chat";
import { AGENTS } from "@/types/agent";
interface Props {
  message: ChatMessage;
}

const AGENT_COLORS: Record<string, string> = {
  seo_yeon: "#e06c75",
  jun_ho: "#61afef",
  ha_eun: "#98c379",
  min_su: "#e5c07b",
};

const AGENT_NAMES = Object.values(AGENTS).map((a) => a.name);
const MENTION_RE = new RegExp(`(@(?:${AGENT_NAMES.join("|")}))`, "g");

function renderContent(text: string) {
  const parts = text.split(MENTION_RE);
  return parts.map((part, i) => {
    if (part.startsWith("@") && AGENT_NAMES.some((n) => part === `@${n}`)) {
      return (
        <span
          key={i}
          style={{
            background: "rgba(29,155,209,0.15)",
            color: "#1d9bd1",
            padding: "0 3px",
            borderRadius: 3,
            fontWeight: 600,
          }}
        >
          {part}
        </span>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

export function MessageBubble({ message }: Props) {
  const isUser = message.senderType === "user";
  const agent = message.agentId ? AGENTS[message.agentId] : null;
  const nameColor = message.agentId
    ? AGENT_COLORS[message.agentId] ?? "#d1d2d3"
    : "#d1d2d3";

  return (
    <div
      style={{
        display: "flex",
        gap: 10,
        padding: "6px 0",
        alignItems: "flex-start",
      }}
    >
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: 6,
          background: isUser ? "#1264a3" : nameColor + "33",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 14,
          fontWeight: 700,
          color: isUser ? "#fff" : nameColor,
          flexShrink: 0,
          marginTop: 2,
        }}
      >
        {isUser ? "나" : agent?.name[0] ?? "?"}
      </div>

      <div style={{ minWidth: 0, flex: 1 }}>
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            gap: 8,
            marginBottom: 2,
          }}
        >
          <span
            style={{
              fontWeight: 700,
              fontSize: 14,
              color: isUser ? "#d1d2d3" : nameColor,
            }}
          >
            {isUser ? "나" : agent?.name}
          </span>
          {!isUser && agent && (
            <span style={{ fontSize: 11, color: "#9a9b9d" }}>
              {agent.role}
            </span>
          )}
          <span style={{ fontSize: 11, color: "#616061" }}>
            {new Date(message.createdAt).toLocaleTimeString("ko-KR", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        </div>
        <div
          style={{
            color: "#d1d2d3",
            fontSize: 15,
            lineHeight: 1.6,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {renderContent(message.content)}
        </div>
      </div>
    </div>
  );
}
