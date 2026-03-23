import { useState } from "react";
import { MessageList } from "./MessageList";
import { MessageInput } from "./MessageInput";
import { MentionPopup } from "./MentionPopup";
import { useChatStore } from "@/stores/chatStore";
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
  const roomTitle = isDM ? activeRoom?.name ?? "" : `# ${activeRoom?.name ?? ""}`;

  const handleInputChange = (value: string) => {
    setInput(value);

    // @ 감지
    const lastAt = value.lastIndexOf("@");
    if (lastAt >= 0) {
      const afterAt = value.slice(lastAt + 1);
      // 스페이스 없으면 멘션 모드
      if (!afterAt.includes(" ")) {
        setShowMention(true);
        setMentionFilter(afterAt);
        return;
      }
    }
    setShowMention(false);
  };

  const handleMentionSelect = (agentId: AgentId) => {
    const name = AGENTS[agentId].name;
    const lastAt = input.lastIndexOf("@");
    const before = input.slice(0, lastAt);
    setInput(`${before}@${name} `);
    setShowMention(false);
  };

  const handleSend = () => {
    const text = input.trim();
    if (!text) return;

    // 사용자 메시지 UI 추가
    addMessage(activeRoomId, {
      id: crypto.randomUUID(),
      conversationId: activeRoomId,
      senderType: "user",
      content: text,
      createdAt: new Date().toISOString(),
    });

    // 전송
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
        background: "#1a1d21",
        minHeight: 0,
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "10px 16px",
          borderBottom: "1px solid #383a3f",
          display: "flex",
          alignItems: "center",
          gap: 8,
        }}
      >
        <span style={{ color: "#fff", fontWeight: 700, fontSize: 16 }}>
          {roomTitle}
        </span>
        {isDM && activeRoom?.agentId && (
          <span style={{ color: "#9a9b9d", fontSize: 13 }}>
            {AGENTS[activeRoom.agentId].role}
          </span>
        )}
      </div>

      <MessageList />

      {/* Mention Popup */}
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
              ? `${activeRoom?.name ?? ""}에게 메시지 보내기...`
              : "팀에게 메시지 보내기... (@로 멘션)"
          }
        />
      </div>
    </div>
  );
}
