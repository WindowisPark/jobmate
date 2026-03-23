import { useEffect, useRef } from "react";
import { useChatStore } from "@/stores/chatStore";
import { AGENTS } from "@/types/agent";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";
import { AgentAvatar } from "@/components/common/AgentAvatar";

export function MessageList() {
  const activeRoomId = useChatStore((s) => s.activeRoomId);
  const allMessages = useChatStore((s) => s.messages);
  const typingAgents = useChatStore((s) => s.typingAgents);
  const rooms = useChatStore((s) => s.rooms);
  const bottomRef = useRef<HTMLDivElement>(null);

  const messages = allMessages[activeRoomId] ?? [];
  const activeRoom = rooms.find((r) => r.id === activeRoomId);
  const isDM = activeRoom?.type === "dm";
  const agent = isDM && activeRoom?.agentId ? AGENTS[activeRoom.agentId] : null;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typingAgents]);

  return (
    <div
      style={{
        flex: 1,
        overflowY: "auto",
        paddingTop: 16,
        paddingBottom: 8,
        display: "flex",
        flexDirection: "column",
        gap: 2,
      }}
    >
      {messages.length === 0 && (
        <div
          style={{
            textAlign: "center",
            marginTop: 80,
            animation: "fadeIn 0.5s ease",
          }}
        >
          {isDM && agent ? (
            <>
              <div style={{ margin: "0 auto 12px", width: 80 }}>
                <AgentAvatar agentId={agent.id} size={80} />
              </div>
              <div style={{ color: agent.color, fontWeight: 700, fontSize: 18, marginBottom: 4 }}>
                {agent.name}
              </div>
              <div style={{ color: "var(--text-secondary)", fontSize: 14, marginBottom: 8 }}>
                {agent.role} · {agent.personality}
              </div>
              <div style={{ color: "var(--text-muted)", fontSize: 14, fontStyle: "italic" }}>
                "{agent.greeting}"
              </div>
            </>
          ) : (
            <>
              <div style={{ fontSize: 48, marginBottom: 12 }}>👋</div>
              <div style={{ color: "var(--text-primary)", fontSize: 18, fontWeight: 600, marginBottom: 6 }}>
                JobMate 팀에 오신 걸 환영해요!
              </div>
              <div style={{ color: "var(--text-secondary)", fontSize: 14, lineHeight: 1.8 }}>
                취준 관련 고민이나 힘든 마음을 편하게 이야기해보세요.
                <br />
                <span style={{ color: "var(--accent-link)" }}>@이름</span>으로
                특정 멤버를 호출할 수 있어요.
              </div>
            </>
          )}
        </div>
      )}
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      {typingAgents.map((agentId) => (
        <TypingIndicator key={agentId} agentId={agentId} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
