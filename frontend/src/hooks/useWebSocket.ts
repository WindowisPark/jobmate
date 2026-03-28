import { useCallback, useEffect, useRef } from "react";
import { useChatStore } from "@/stores/chatStore";
import { useOfficeStore } from "@/stores/officeStore";
import type { AgentId } from "@/types/agent";
import { toast } from "@/stores/toastStore";
import { WS_BASE_URL } from "@/utils/constants";

const MAX_RECONNECT_ATTEMPTS = 5;
const BASE_RECONNECT_DELAY = 1000; // ms
const MAX_QUEUE_SIZE = 50;

interface QueuedMessage {
  content: string;
  mode: "group" | "dm";
  targetAgent?: string;
  timestamp: string;
}

export function useWebSocket(roomId: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const roomIdRef = useRef(roomId);
  const connectingRef = useRef(false);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const unmountedRef = useRef(false);
  const messageQueueRef = useRef<QueuedMessage[]>([]);
  roomIdRef.current = roomId;

  const addMessage = useChatStore((s) => s.addMessage);
  const setTyping = useChatStore((s) => s.setTyping);
  const sendToDesk = useOfficeStore((s) => s.sendToDesk);
  const startTyping = useOfficeStore((s) => s.startTyping);
  const finishTyping = useOfficeStore((s) => s.finishTyping);

  const flushQueue = useCallback((ws: WebSocket) => {
    while (messageQueueRef.current.length > 0 && ws.readyState === WebSocket.OPEN) {
      const msg = messageQueueRef.current.shift()!;
      ws.send(
        JSON.stringify({
          type: "user_message",
          content: msg.content,
          mode: msg.mode,
          target_agent: msg.targetAgent,
          timestamp: msg.timestamp,
        })
      );
    }
  }, []);

  const connect = useCallback(() => {
    if (connectingRef.current || unmountedRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    }

    connectingRef.current = true;
    const ws = new WebSocket(`${WS_BASE_URL}/chat/${roomIdRef.current}`);

    ws.onopen = () => {
      wsRef.current = ws;
      connectingRef.current = false;
      reconnectAttemptsRef.current = 0;

      // 재연결 시 큐에 쌓인 메시지 전송
      flushQueue(ws);
    };

    ws.onmessage = (event) => {
      let data: any;
      try {
        data = JSON.parse(event.data);
      } catch {
        console.error("Failed to parse WebSocket message");
        return;
      }

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
          break;

        case "error":
          toast.error(data.message || "서버 오류가 발생했습니다");
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

      // 자동 재연결 (지수 백오프)
      if (!unmountedRef.current && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttemptsRef.current);
        reconnectAttemptsRef.current += 1;
        console.log(`WebSocket reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})`);
        reconnectTimerRef.current = setTimeout(connect, delay);
      }
    };

    return ws;
  }, [addMessage, setTyping, sendToDesk, startTyping, finishTyping, flushQueue]);

  useEffect(() => {
    unmountedRef.current = false;
    reconnectAttemptsRef.current = 0;
    messageQueueRef.current = [];
    const ws = connect();

    return () => {
      unmountedRef.current = true;
      connectingRef.current = false;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      ws?.close();
    };
  }, [roomId, connect]);

  const sendMessage = useCallback(
    (content: string, mode: "group" | "dm", targetAgent?: string) => {
      const msg: QueuedMessage = {
        content,
        mode,
        targetAgent,
        timestamp: new Date().toISOString(),
      };

      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            type: "user_message",
            content: msg.content,
            mode: msg.mode,
            target_agent: msg.targetAgent,
            timestamp: msg.timestamp,
          })
        );
      } else {
        // 연결 끊김 시 큐에 저장 후 재연결 시도
        if (messageQueueRef.current.length < MAX_QUEUE_SIZE) {
          messageQueueRef.current.push(msg);
        }
        reconnectAttemptsRef.current = 0;
        connect();
      }
    },
    [connect]
  );

  return { sendMessage };
}
