import { create } from "zustand";
import type { ChatMessage } from "@/types/chat";
import type { AgentId } from "@/types/agent";

export type ChatRoom = {
  id: string;
  type: "channel" | "dm";
  name: string;
  agentId?: AgentId; // DM일 때 대상 에이전트
};

interface ChatState {
  rooms: ChatRoom[];
  activeRoomId: string;
  messages: Record<string, ChatMessage[]>; // roomId → messages
  typingAgents: AgentId[];

  setActiveRoom: (roomId: string) => void;
  addMessage: (roomId: string, msg: ChatMessage) => void;
  appendToLastMessage: (agentId: AgentId, chunk: string) => void;
  finalizeMessage: (agentId: AgentId) => void;
  setTyping: (agentId: AgentId, isTyping: boolean) => void;
}

const DEFAULT_ROOMS: ChatRoom[] = [
  { id: "general", type: "channel", name: "general" },
  { id: "dm-seo_yeon", type: "dm", name: "김서연", agentId: "seo_yeon" },
  { id: "dm-jun_ho", type: "dm", name: "박준호", agentId: "jun_ho" },
  { id: "dm-ha_eun", type: "dm", name: "이하은", agentId: "ha_eun" },
  { id: "dm-min_su", type: "dm", name: "정민수", agentId: "min_su" },
];

export const useChatStore = create<ChatState>((set) => ({
  rooms: DEFAULT_ROOMS,
  activeRoomId: "general",
  messages: {},
  typingAgents: [],

  setActiveRoom: (roomId) => set({ activeRoomId: roomId }),

  addMessage: (roomId, msg) =>
    set((state) => {
      const prev = state.messages[roomId] ?? [];
      return {
        messages: { ...state.messages, [roomId]: [...prev, msg] },
      };
    }),

  appendToLastMessage: (agentId, chunk) =>
    set((state) => {
      const roomId = state.activeRoomId;
      const msgs = [...(state.messages[roomId] ?? [])];
      const lastIdx = msgs.findLastIndex(
        (m) => m.agentId === agentId && m.isStreaming
      );
      if (lastIdx >= 0) {
        msgs[lastIdx] = {
          ...msgs[lastIdx]!,
          content: msgs[lastIdx]!.content + chunk,
        };
      }
      return { messages: { ...state.messages, [roomId]: msgs } };
    }),

  finalizeMessage: (agentId) =>
    set((state) => {
      const roomId = state.activeRoomId;
      const msgs = (state.messages[roomId] ?? []).map((m) =>
        m.agentId === agentId && m.isStreaming ? { ...m, isStreaming: false } : m
      );
      return { messages: { ...state.messages, [roomId]: msgs } };
    }),

  setTyping: (agentId, isTyping) =>
    set((state) => {
      const next = isTyping
        ? [...state.typingAgents.filter((id) => id !== agentId), agentId]
        : state.typingAgents.filter((id) => id !== agentId);
      return { typingAgents: next };
    }),
}));
