import { create } from "zustand";
import type { ChatMessage } from "@/types/chat";
import type { AgentId } from "@/types/agent";

interface ChatState {
  messages: ChatMessage[];
  typingAgents: Set<AgentId>;
  activeConversationId: string | null;
  addMessage: (msg: ChatMessage) => void;
  appendToLastMessage: (agentId: AgentId, chunk: string) => void;
  setTyping: (agentId: AgentId, isTyping: boolean) => void;
  setConversation: (id: string) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  typingAgents: new Set(),
  activeConversationId: null,

  addMessage: (msg) =>
    set((state) => ({ messages: [...state.messages, msg] })),

  appendToLastMessage: (agentId, chunk) =>
    set((state) => {
      const msgs = [...state.messages];
      const lastIdx = msgs.findLastIndex(
        (m) => m.agentId === agentId && m.isStreaming
      );
      if (lastIdx >= 0) {
        msgs[lastIdx] = { ...msgs[lastIdx]!, content: msgs[lastIdx]!.content + chunk };
      }
      return { messages: msgs };
    }),

  setTyping: (agentId, isTyping) =>
    set((state) => {
      const next = new Set(state.typingAgents);
      if (isTyping) next.add(agentId);
      else next.delete(agentId);
      return { typingAgents: next };
    }),

  setConversation: (id) => set({ activeConversationId: id }),
  clearMessages: () => set({ messages: [], typingAgents: new Set() }),
}));
