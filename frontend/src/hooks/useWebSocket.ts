import { useCallback, useEffect, useRef } from "react";
import { useChatStore } from "@/stores/chatStore";
import { useOfficeStore } from "@/stores/officeStore";
import type { WSServerEvent } from "@/types/chat";
import type { AgentId } from "@/types/agent";

export function useWebSocket(conversationId: string | null, token: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const { addMessage, appendToLastMessage, setTyping } = useChatStore();
  const { setAgentState } = useOfficeStore();

  useEffect(() => {
    if (!conversationId || !token) return;

    const ws = new WebSocket(
      `ws://localhost:8000/ws/chat/${conversationId}?token=${token}`
    );
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as WSServerEvent;

      switch (data.type) {
        case "agent_typing":
          setTyping(data.agent_id, true);
          setAgentState(data.agent_id, { action: data.office_action as AgentId extends string ? string : never });
          break;

        case "agent_message_chunk":
          if (data.is_final) {
            setTyping(data.agent_id, false);
            setAgentState(data.agent_id, { action: "idle" });
          }
          appendToLastMessage(data.agent_id, data.chunk);
          break;

        case "tool_call_start":
          setAgentState(data.agent_id, { action: data.office_action as AgentId extends string ? string : never });
          break;

        case "tool_call_result":
          setAgentState(data.agent_id, { action: "idle" });
          break;

        case "agent_reaction":
          // TODO: show reaction in chat
          break;
      }
    };

    ws.onclose = () => {
      wsRef.current = null;
    };

    return () => {
      ws.close();
    };
  }, [conversationId, token, addMessage, appendToLastMessage, setTyping, setAgentState]);

  const sendMessage = useCallback((content: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "user_message",
          content,
          timestamp: new Date().toISOString(),
        })
      );
    }
  }, []);

  return { sendMessage };
}
