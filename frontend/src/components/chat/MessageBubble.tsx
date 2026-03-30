import type { ChatMessage } from "@/types/chat";
import { AGENTS } from "@/types/agent";
import { AgentAvatar } from "@/components/common/AgentAvatar";
import BreathingExercise from "./BreathingExercise";
import MotivationContent from "./MotivationContent";
import type { ToolResult } from "@/stores/chatStore";

interface Props {
  message: ChatMessage;
  toolResults?: ToolResult[];
}

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
            background: "rgba(91,155,213,0.15)",
            color: "var(--accent-link)",
            padding: "1px 5px",
            borderRadius: 4,
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

function renderToolResult(result: ToolResult) {
  switch (result.toolName) {
    case "breathing_exercise":
      return <BreathingExercise key={result.timestamp} data={result.data} />;
    case "get_motivation_content":
      return <MotivationContent key={result.timestamp} data={result.data} />;
    default:
      return null;
  }
}

export function MessageBubble({ message, toolResults }: Props) {
  const isUser = message.senderType === "user";
  const agent = message.agentId ? AGENTS[message.agentId] : null;

  return (
    <div
      style={{
        display: "flex",
        gap: 12,
        padding: isUser ? "10px 20px" : "10px 20px 10px 16px",
        animation: "fadeIn 0.3s ease",
        transition: "background var(--transition-fast)",
        margin: "2px 8px",
        borderRadius: "var(--radius-md)",
        ...(isUser
          ? {}
          : {
              background: "var(--bg-card)",
              borderLeft: `3px solid ${agent?.color ?? "var(--border)"}`,
            }),
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = isUser
          ? "rgba(255,255,255,0.02)"
          : "var(--bg-hover)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = isUser
          ? "transparent"
          : "var(--bg-card)";
      }}
    >
      {/* Avatar */}
      <div style={{ flexShrink: 0, marginTop: 2 }}>
        {isUser ? (
          <div
            style={{
              width: 38,
              height: 38,
              borderRadius: "var(--radius-md)",
              background: "linear-gradient(135deg, var(--accent-blue), #4a8abf)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 14,
              fontWeight: 700,
              color: "#fff",
            }}
          >
            나
          </div>
        ) : message.agentId ? (
          <AgentAvatar agentId={message.agentId} size={38} />
        ) : null}
      </div>

      {/* Content */}
      <div style={{ minWidth: 0, flex: 1 }}>
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            gap: 8,
            marginBottom: 4,
          }}
        >
          <span
            style={{
              fontWeight: 700,
              fontSize: 15,
              color: isUser ? "var(--text-white)" : agent?.color,
            }}
          >
            {isUser ? "나" : agent?.name}
          </span>
          {!isUser && agent && (
            <span
              style={{
                fontSize: 11,
                color: agent.color,
                background: `${agent.color}12`,
                padding: "2px 8px",
                borderRadius: 10,
                fontWeight: 500,
              }}
            >
              {agent.role}
            </span>
          )}
          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
            {new Date(message.createdAt).toLocaleTimeString("ko-KR", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        </div>
        <div
          style={{
            color: "var(--text-primary)",
            fontSize: 15,
            lineHeight: 1.7,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {renderContent(message.content)}
        </div>
        {toolResults?.map((tr) => renderToolResult(tr))}
      </div>
    </div>
  );
}
