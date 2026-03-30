import type { AgentId } from "./agent";

export interface ChatMessage {
  id: string;
  conversationId: string;
  senderType: "user" | "agent";
  agentId?: AgentId;
  content: string;
  emotionTag?: string;
  createdAt: string;
  isStreaming?: boolean;
}

export interface UserMessagePayload {
  type: "user_message";
  content: string;
  timestamp: string;
}

export interface AgentTypingEvent {
  type: "agent_typing";
  agent_id: AgentId;
  office_action: string;
}

export interface AgentMessageChunk {
  type: "agent_message_chunk";
  agent_id: AgentId;
  chunk: string;
  is_final: boolean;
}

export interface ToolCallStartEvent {
  type: "tool_call_start";
  agent_id: AgentId;
  tool_name: string;
  office_action: string;
}

export interface ToolCallResultEvent {
  type: "tool_call_result";
  agent_id: AgentId;
  tool_name: string;
  result_summary: string;
  office_action: string;
}

export interface AgentReactionEvent {
  type: "agent_reaction";
  agent_id: AgentId;
  emoji: string;
}

export interface ToolResultEvent {
  type: "tool_result";
  agent_id: AgentId;
  tool_name: string;
  data: Record<string, unknown>;
}

export interface OfficeStateEvent {
  type: "office_state";
  agents: Record<string, unknown>;
  emotion?: string;
}

export type WSServerEvent =
  | AgentTypingEvent
  | AgentMessageChunk
  | ToolCallStartEvent
  | ToolCallResultEvent
  | ToolResultEvent
  | OfficeStateEvent
  | AgentReactionEvent;
