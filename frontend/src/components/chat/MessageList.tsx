import { useCallback, useEffect, useRef, useState } from "react";
import { useChatStore } from "@/stores/chatStore";
import { AGENTS } from "@/types/agent";
import { api } from "@/utils/api";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";
import { AgentAvatar } from "@/components/common/AgentAvatar";
import type { ChatMessage } from "@/types/chat";

export function MessageList() {
  const activeRoomId = useChatStore((s) => s.activeRoomId);
  const allMessages = useChatStore((s) => s.messages);
  const typingAgents = useChatStore((s) => s.typingAgents);
  const rooms = useChatStore((s) => s.rooms);
  const prependMessages = useChatStore((s) => s.prependMessages);

  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const prevRoomRef = useRef(activeRoomId);

  const messages = allMessages[activeRoomId] ?? [];
  const activeRoom = rooms.find((r) => r.id === activeRoomId);
  const isDM = activeRoom?.type === "dm";
  const agent = isDM && activeRoom?.agentId ? AGENTS[activeRoom.agentId] : null;

  // 방 변경 시 리셋
  useEffect(() => {
    if (prevRoomRef.current !== activeRoomId) {
      setHasMore(true);
      prevRoomRef.current = activeRoomId;
    }
  }, [activeRoomId]);

  // 새 메시지가 오면 하단으로 스크롤
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, typingAgents]);

  // 스크롤 상단 도달 시 이전 메시지 로드
  const loadOlderMessages = useCallback(async () => {
    if (loadingMore || !hasMore || messages.length === 0) return;

    const oldest = messages[0];
    if (!oldest) return;

    setLoadingMore(true);
    const container = containerRef.current;
    const prevScrollHeight = container?.scrollHeight ?? 0;

    try {
      const data = await api.get<{
        messages: Array<{
          id: string;
          sender_type: string;
          agent_id: string | null;
          content: string;
          tool_calls: any;
          tool_results: any;
          emotion_tag: string | null;
          created_at: string;
        }>;
        has_more: boolean;
      }>(`/conversations/${activeRoomId}/messages?before=${oldest.createdAt}&limit=30`);

      if (data.messages.length > 0) {
        const mapped: ChatMessage[] = data.messages.map((m) => ({
          id: m.id,
          conversationId: activeRoomId,
          senderType: m.sender_type as "user" | "agent",
          agentId: (m.agent_id ?? undefined) as ChatMessage["agentId"],
          content: m.content,
          createdAt: m.created_at,
        }));
        prependMessages(activeRoomId, mapped);

        // 스크롤 위치 보존
        requestAnimationFrame(() => {
          if (container) {
            container.scrollTop = container.scrollHeight - prevScrollHeight;
          }
        });
      }

      setHasMore(data.has_more);
    } catch {
      // toast가 api.ts에서 자동 처리
    } finally {
      setLoadingMore(false);
    }
  }, [loadingMore, hasMore, messages, activeRoomId, prependMessages]);

  const handleScroll = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;
    if (container.scrollTop < 60) {
      loadOlderMessages();
    }
  }, [loadOlderMessages]);

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
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
      {/* 이전 메시지 로딩 표시 */}
      {loadingMore && (
        <div style={{
          textAlign: "center",
          padding: "8px 0",
          color: "var(--text-muted)",
          fontSize: 13,
        }}>
          이전 메시지 불러오는 중...
        </div>
      )}

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
                &ldquo;{agent.greeting}&rdquo;
              </div>
            </>
          ) : (
            <>
              <div style={{ fontSize: 48, marginBottom: 12 }}>&#x1F44B;</div>
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
