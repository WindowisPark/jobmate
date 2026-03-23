import { useEffect, useRef } from "react";
import { useChatStore } from "@/stores/chatStore";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";

export function MessageList() {
  const activeRoomId = useChatStore((s) => s.activeRoomId);
  const allMessages = useChatStore((s) => s.messages);
  const typingAgents = useChatStore((s) => s.typingAgents);
  const rooms = useChatStore((s) => s.rooms);
  const bottomRef = useRef<HTMLDivElement>(null);

  const messages = allMessages[activeRoomId] ?? [];
  const activeRoom = rooms.find((r) => r.id === activeRoomId);
  const isDM = activeRoom?.type === "dm";

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typingAgents]);

  return (
    <div
      style={{
        flex: 1,
        overflowY: "auto",
        padding: "16px",
        display: "flex",
        flexDirection: "column",
        gap: 4,
      }}
    >
      {messages.length === 0 && (
        <div
          style={{
            color: "#9a9b9d",
            textAlign: "center",
            marginTop: 60,
            fontSize: 14,
            lineHeight: 1.8,
          }}
        >
          <div style={{ fontSize: 32, marginBottom: 8 }}>
            {isDM ? "💬" : "👋"}
          </div>
          <div>
            {isDM
              ? `${activeRoom?.name}와의 대화를 시작하세요.`
              : "안녕! JobMate 팀에 오신 걸 환영해요."}
          </div>
          {!isDM && (
            <div>
              취준 관련 고민이나 힘든 마음을 편하게 이야기해보세요.
              <br />
              <span style={{ color: "#61afef" }}>@이름</span>으로 특정
              멤버를 호출할 수 있어요.
            </div>
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
