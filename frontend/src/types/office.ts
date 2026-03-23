import type { AgentId, AgentOfficeState } from "./agent";

export interface OfficeState {
  agents: Record<AgentId, AgentOfficeState>;
}

export interface OfficeTile {
  x: number;
  y: number;
  type: "floor" | "wall" | "door" | "window" | "desk" | "chair" | "sofa" | "plant" | "whiteboard";
}
