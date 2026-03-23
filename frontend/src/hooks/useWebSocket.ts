import { useCallback, useEffect, useRef } from "react";
import { useChatStore } from "@/stores/chatStore";
import { useOfficeStore } from "@/stores/officeStore";
import type { AgentId } from "@/types/agent";

export function useWebSocket(roomId: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const roomIdRef = useRef(roomId);
  const connectingRef = useRef(false);
  roomIdRef.current = roomId;

  const addMessage = useChatStore((s) => s.addMessage);
  const setTyping = useChatStore((s) => s.setTyping);
  const sendToDesk = useOfficeStore((s) => s.sendToDesk);
  const startTyping = useOfficeStore((s) => s.startTyping);
  const finishTyping = useOfficeStore((s) => s.finishTyping);

  useEffect(() => {
    // 이미 연결 중이거나 연결된 상태면 스킵
    if (connectingRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    }

    connectingRef.current = true;
    const ws = new WebSocket(`ws://localhost:8000/ws/chat/${roomId}`);

    ws.onopen = () => {
      wsRef.current = ws;
      connectingRef.current = false;
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const currentRoom = roomIdRef.current;

      switch (data.type) {
        case "agent_typing": {
          const agentId = data.agent_id as AgentId;
          setTyping(agentId, true);
          sendToDesk(agentId);
          setTimeout(() => startTyping(agentId), 800);
          break;
        }

        case "agent_message_chunk": {
          const agentId = data.agent_id as AgentId;
          setTyping(agentId, false);
          addMessage(currentRoom, {
            id: crypto.randomUUID(),
            conversationId: currentRoom,
            senderType: "agent",
            agentId,
            content: data.chunk,
            createdAt: new Date().toISOString(),
          });
          if (data.is_final) {
            setTimeout(() => finishTyping(agentId), 500);
          }
          break;
        }

        case "office_state":
          // 로컬 상태 머신이 처리
          break;

        case "error":
          console.error("Server error:", data.message);
          break;
      }
    };

    ws.onerror = () => {
      connectingRef.current = false;
    };

    ws.onclose = () => {
      connectingRef.current = false;
      if (wsRef.current === ws) {
        wsRef.current = null;
      }
    };

    return () => {
      connectingRef.current = false;
      ws.close();
    };
  }, [roomId, addMessage, setTyping, sendToDesk, startTyping, finishTyping]);

  const sendMessage = useCallback(
    (content: string, mode: "group" | "dm", targetAgent?: string) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            type: "user_message",
            content,
            mode,
            target_agent: targetAgent,
            timestamp: new Date().toISOString(),
          })
        );
      } else {
        console.warn("WebSocket not connected");
      }
    },
    []
  );

  return { sendMessage };
}
