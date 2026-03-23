import { useChatStore } from "@/stores/chatStore";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";

export function MessageList() {
  const { messages, typingAgents } = useChatStore();

  return (
    <div style={{ flex: 1, overflowY: "auto", padding: "16px" }}>
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      {[...typingAgents].map((agentId) => (
        <TypingIndicator key={agentId} agentId={agentId} />
      ))}
    </div>
  );
}
