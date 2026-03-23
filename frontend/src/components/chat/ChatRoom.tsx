import { useState } from "react";
import { MessageList } from "./MessageList";
import { MessageInput } from "./MessageInput";

export function ChatRoom() {
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    // TODO: send via WebSocket
    setInput("");
  };

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", background: "#1a1d21" }}>
      <MessageList />
      <MessageInput value={input} onChange={setInput} onSend={handleSend} />
    </div>
  );
}
