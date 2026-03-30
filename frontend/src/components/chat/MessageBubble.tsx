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
            background: "rgba(29,155,209,0.12)",
            color: "var(--accent-link)",
            padding: "1px 4px",
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
        gap: 10,
        padding: "6px 20px",
        animation: "fadeIn 0.25s ease",
        transition: "background 0.15s",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.02)")}
      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
    >
      {/* Avatar */}
      <div style={{ flexShrink: 0, marginTop: 2 }}>
        {isUser ? (
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: "var(--radius-lg)",
              background: "var(--accent-blue)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 13,
              fontWeight: 700,
              color: "#fff",
            }}
          >
            나
          </div>
        ) : message.agentId ? (
          <AgentAvatar agentId={message.agentId} size={36} />
        ) : null}
      </div>

      {/* Content */}
      <div style={{ minWidth: 0, flex: 1 }}>
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            gap: 8,
            marginBottom: 3,
          }}
        >
          <span
            style={{
              fontWeight: 700,
              fontSize: "var(--font-base)",
              color: isUser ? "var(--text-primary)" : agent?.color,
            }}
          >
            {isUser ? "나" : agent?.name}
          </span>
          {!isUser && agent && (
            <span
              style={{
                fontSize: 11,
                color: "var(--text-muted)",
                background: `${agent.color}11`,
                padding: "1px 6px",
                borderRadius: 3,
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
            lineHeight: 1.65,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {renderContent(message.content)}
        </div>
        {/* 도구 결과 인라인 렌더링 */}
        {toolResults?.map((tr) => renderToolResult(tr))}
      </div>
    </div>
  );
}
