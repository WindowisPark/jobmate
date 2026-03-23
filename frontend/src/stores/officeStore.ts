import { create } from "zustand";
import type { AgentId, AgentOfficeState } from "@/types/agent";

interface OfficeStoreState {
  agents: Record<string, AgentOfficeState>;
  setAgentState: (agentId: AgentId, state: Partial<AgentOfficeState>) => void;
  setAllAgentStates: (states: Record<string, AgentOfficeState>) => void;
}

const DEFAULT_STATES: Record<AgentId, AgentOfficeState> = {
  seo_yeon: { action: "idle", position: { x: 3, y: 2 } },
  jun_ho: { action: "idle", position: { x: 7, y: 2 } },
  ha_eun: { action: "idle", position: { x: 3, y: 6 } },
  min_su: { action: "idle", position: { x: 9, y: 6 } },
};

export const useOfficeStore = create<OfficeStoreState>((set) => ({
  agents: DEFAULT_STATES,

  setAgentState: (agentId, partial) =>
    set((state) => ({
      agents: {
        ...state.agents,
        [agentId]: { ...state.agents[agentId]!, ...partial },
      },
    })),

  setAllAgentStates: (states) => set({ agents: states }),
}));
