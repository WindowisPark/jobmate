import { useState } from "react";
import { MessageList } from "./MessageList";
import { MessageInput } from "./MessageInput";
import { MentionPopup } from "./MentionPopup";
import { useChatStore } from "@/stores/chatStore";
import { AgentAvatar } from "@/components/common/AgentAvatar";
import { useWebSocket } from "@/hooks/useWebSocket";
import { AGENTS } from "@/types/agent";
import type { AgentId } from "@/types/agent";

export function ChatRoom() {
  const [input, setInput] = useState("");
  const [showMention, setShowMention] = useState(false);
  const [mentionFilter, setMentionFilter] = useState("");
  const { activeRoomId, rooms, addMessage } = useChatStore();
  const { sendMessage } = useWebSocket(activeRoomId);

  const activeRoom = rooms.find((r) => r.id === activeRoomId);
  const isDM = activeRoom?.type === "dm";
  const agent = isDM && activeRoom?.agentId ? AGENTS[activeRoom.agentId] : null;

  const handleInputChange = (value: string) => {
    setInput(value);
    const lastAt = value.lastIndexOf("@");
    if (lastAt >= 0 && !value.slice(lastAt + 1).includes(" ")) {
      setShowMention(true);
      setMentionFilter(value.slice(lastAt + 1));
    } else {
      setShowMention(false);
    }
  };

  const handleMentionSelect = (agentId: AgentId) => {
    const name = AGENTS[agentId].name;
    const lastAt = input.lastIndexOf("@");
    setInput(`${input.slice(0, lastAt)}@${name} `);
    setShowMention(false);
  };

  const handleSend = () => {
    const text = input.trim();
    if (!text) return;

    addMessage(activeRoomId, {
      id: crypto.randomUUID(),
      conversationId: activeRoomId,
      senderType: "user",
      content: text,
      createdAt: new Date().toISOString(),
    });

    if (isDM && activeRoom?.agentId) {
      sendMessage(text, "dm", activeRoom.agentId);
    } else {
      sendMessage(text, "group");
    }

    setInput("");
    setShowMention(false);
  };

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        background: "var(--bg-primary)",
        minHeight: 0,
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "10px 20px",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          gap: 10,
        }}
      >
        {isDM && agent ? (
          <>
            <AgentAvatar agentId={agent.id} size={24} />
            <span style={{ color: agent.color, fontWeight: 700, fontSize: "var(--font-lg)" }}>
              {agent.name}
            </span>
            <span
              style={{
                fontSize: 12,
                color: "var(--text-secondary)",
                background: `${agent.color}11`,
                padding: "2px 8px",
                borderRadius: 4,
              }}
            >
              {agent.role}
            </span>
          </>
        ) : (
          <>
            <span style={{ color: "var(--text-muted)", fontSize: 18, fontWeight: 300 }}>#</span>
            <span style={{ color: "var(--text-white)", fontWeight: 700, fontSize: "var(--font-lg)" }}>
              {activeRoom?.name ?? "general"}
            </span>
            <span style={{ fontSize: 12, color: "var(--text-muted)", marginLeft: 4 }}>
              팀 전체 채팅
            </span>
          </>
        )}
      </div>

      <MessageList />

      {/* Mention + Input */}
      <div style={{ position: "relative" }}>
        {showMention && (
          <MentionPopup
            filter={mentionFilter}
            onSelect={handleMentionSelect}
            onClose={() => setShowMention(false)}
          />
        )}
        <MessageInput
          value={input}
          onChange={handleInputChange}
          onSend={handleSend}
          placeholder={
            isDM
              ? `${agent?.name ?? ""}에게 메시지 보내기...`
              : "팀에게 메시지 보내기... (@로 멘션)"
          }
        />
      </div>
    </div>
  );
}
