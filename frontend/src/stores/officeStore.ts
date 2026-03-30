import { create } from "zustand";
import type { AgentId } from "@/types/agent";
import type { AgentBehavior, AgentOfficeFull, OfficeLocation } from "@/types/office";
import {
  TILE_SIZE,
  AGENT_DESK_POSITIONS,
  OFFICE_LOCATIONS,
  ACTION_TO_BEHAVIOR,
} from "@/types/office";

function randomWalkableSpot(): { x: number; y: number } {
  const candidates = [
    { col: 5, row: 4 }, { col: 6, row: 5 }, { col: 7, row: 4 },
    { col: 8, row: 5 }, { col: 1, row: 3 }, { col: 12, row: 3 },
    { col: 1, row: 5 }, { col: 12, row: 5 }, { col: 6, row: 2 },
    { col: 7, row: 2 }, { col: 6, row: 7 }, { col: 7, row: 7 },
  ];
  const spot = candidates[Math.floor(Math.random() * candidates.length)]!;
  return { x: spot.col * TILE_SIZE, y: spot.row * TILE_SIZE };
}

function initAgent(id: AgentId): AgentOfficeFull {
  const pos = AGENT_DESK_POSITIONS[id];
  const start = randomWalkableSpot();
  return {
    id,
    x: start.x,
    y: start.y,
    targetX: start.x,
    targetY: start.y,
    behavior: "wandering",
    direction: "down",
    frameIndex: 0,
    deskTile: pos.desk,
    chairTile: pos.chair,
  };
}

/** 행동에 맞는 목표 위치를 계산한다 */
function getTargetForBehavior(
  agent: AgentOfficeFull,
  behavior: AgentBehavior,
  location?: OfficeLocation
): { x: number; y: number } {
  const loc = location || "desk";

  if (loc === "desk" || behavior === "typing" || behavior === "searching" || behavior === "reading") {
    return { x: agent.chairTile.col * TILE_SIZE, y: agent.chairTile.row * TILE_SIZE };
  }

  const coords = OFFICE_LOCATIONS[loc];
  if (coords && coords.col > 0) {
    return { x: coords.col * TILE_SIZE, y: coords.row * TILE_SIZE };
  }

  return { x: agent.chairTile.col * TILE_SIZE, y: agent.chairTile.row * TILE_SIZE };
}

// 정적 행동 (도착 후 이동하지 않는 행동들)
const STATIONARY_BEHAVIORS = new Set<AgentBehavior>([
  "typing", "searching", "analyzing", "reading", "breathing",
  "interview_prep", "collaborating", "idle_at_spot",
]);

interface OfficeStoreState {
  agents: Record<AgentId, AgentOfficeFull>;
  currentEmotion: string;

  // 새로운 통합 행동 설정 (Phase 4)
  setAgentBehavior: (agentId: AgentId, action: string, location?: OfficeLocation) => void;
  setEmotion: (emotion: string) => void;

  // 기존 인터페이스 (하위 호환)
  sendToDesk: (agentId: AgentId) => void;
  startTyping: (agentId: AgentId) => void;
  finishTyping: (agentId: AgentId) => void;

  // 애니메이션 틱
  tick: () => void;

  // 하위 호환
  setAgentState: (agentId: AgentId, state: { action?: string }) => void;
  setAllAgentStates: (states: Record<string, { action: string; position: { x: number; y: number } }>) => void;
}

const MOVE_SPEED = 1.5;
const WANDER_INTERVAL = 3000;
let lastWanderTime = 0;

export const useOfficeStore = create<OfficeStoreState>((set, get) => ({
  agents: {
    seo_yeon: initAgent("seo_yeon"),
    jun_ho: initAgent("jun_ho"),
    ha_eun: initAgent("ha_eun"),
    min_su: initAgent("min_su"),
  },
  currentEmotion: "neutral",

  setAgentBehavior: (agentId, action, location) =>
    set((state) => {
      const agent = state.agents[agentId];
      const behavior = ACTION_TO_BEHAVIOR[action] || "typing";
      const target = getTargetForBehavior(agent, behavior, location);

      return {
        agents: {
          ...state.agents,
          [agentId]: {
            ...agent,
            behavior: "walking_to" as AgentBehavior,
            targetX: target.x,
            targetY: target.y,
            // 도착 후 전환할 행동을 frameIndex에 임시 저장하지 않고,
            // _pendingBehavior를 별도 관리하기 어려우므로
            // walking_to 도착 시 tick에서 판단
          },
        },
        // _pendingBehaviors를 state에 넣는 대신, behavior 이름으로 판단
        _pendingBehaviors: {
          ...(state as any)._pendingBehaviors,
          [agentId]: behavior,
        },
      } as any;
    }),

  setEmotion: (emotion) => set({ currentEmotion: emotion }),

  sendToDesk: (agentId) =>
    set((state) => {
      const agent = state.agents[agentId];
      const chairPos = agent.chairTile;
      return {
        agents: {
          ...state.agents,
          [agentId]: {
            ...agent,
            behavior: "walking_to_desk" as AgentBehavior,
            targetX: chairPos.col * TILE_SIZE,
            targetY: chairPos.row * TILE_SIZE,
          },
        },
      };
    }),

  startTyping: (agentId) =>
    set((state) => {
      const agent = state.agents[agentId];
      return {
        agents: {
          ...state.agents,
          [agentId]: {
            ...agent,
            behavior: "typing" as AgentBehavior,
            x: agent.chairTile.col * TILE_SIZE,
            y: agent.chairTile.row * TILE_SIZE,
            targetX: agent.chairTile.col * TILE_SIZE,
            targetY: agent.chairTile.row * TILE_SIZE,
          },
        },
      };
    }),

  finishTyping: (agentId) =>
    set((state) => {
      const agent = state.agents[agentId];
      const spot = randomWalkableSpot();
      return {
        agents: {
          ...state.agents,
          [agentId]: {
            ...agent,
            behavior: "wandering" as AgentBehavior,
            targetX: spot.x,
            targetY: spot.y,
          },
        },
        _pendingBehaviors: {
          ...(state as any)._pendingBehaviors,
          [agentId]: undefined,
        },
      } as any;
    }),

  tick: () =>
    set((state) => {
      const now = Date.now();
      const newAgents = { ...state.agents };
      const pending = { ...((state as any)._pendingBehaviors || {}) };

      for (const id of Object.keys(newAgents) as AgentId[]) {
        const agent = { ...newAgents[id]! };
        newAgents[id] = agent;

        // 애니메이션 프레임 업데이트
        agent.frameIndex = (agent.frameIndex + 1) % 60;

        // 정적 행동 중이면 이동 안함
        if (STATIONARY_BEHAVIORS.has(agent.behavior)) {
          continue;
        }

        // 이동 로직
        const dx = agent.targetX - agent.x;
        const dy = agent.targetY - agent.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist > 2) {
          const moveX = (dx / dist) * MOVE_SPEED;
          const moveY = (dy / dist) * MOVE_SPEED;
          agent.x += moveX;
          agent.y += moveY;

          if (Math.abs(dx) > Math.abs(dy)) {
            agent.direction = dx > 0 ? "right" : "left";
          } else {
            agent.direction = dy > 0 ? "down" : "up";
          }
        } else {
          // 목표 도착
          agent.x = agent.targetX;
          agent.y = agent.targetY;

          if (agent.behavior === "walking_to_desk") {
            agent.behavior = "typing";
          } else if (agent.behavior === "walking_to") {
            // pending behavior로 전환
            const pendingBehavior = pending[id];
            if (pendingBehavior && STATIONARY_BEHAVIORS.has(pendingBehavior)) {
              agent.behavior = pendingBehavior;
            } else {
              agent.behavior = "typing";
            }
          } else if (agent.behavior === "wandering") {
            if (now - lastWanderTime > WANDER_INTERVAL) {
              const spot = randomWalkableSpot();
              agent.targetX = spot.x;
              agent.targetY = spot.y;
            }
          }
        }
      }

      if (now - lastWanderTime > WANDER_INTERVAL) {
        lastWanderTime = now;
        for (const id of Object.keys(newAgents) as AgentId[]) {
          const agent = newAgents[id]!;
          if (agent.behavior === "wandering" && Math.abs(agent.x - agent.targetX) < 3 && Math.abs(agent.y - agent.targetY) < 3) {
            const spot = randomWalkableSpot();
            newAgents[id] = { ...agent, targetX: spot.x, targetY: spot.y };
          }
        }
      }

      return { agents: newAgents, _pendingBehaviors: pending } as any;
    }),

  setAgentState: (agentId, partial) => {
    const action = partial.action ?? "idle";
    if (action === "idle") {
      get().finishTyping(agentId);
    } else {
      get().setAgentBehavior(agentId, action);
    }
  },

  setAllAgentStates: (states) => {
    const store = get();
    for (const [id, s] of Object.entries(states)) {
      if (s.action === "idle") {
        store.finishTyping(id as AgentId);
      } else {
        store.setAgentBehavior(id as AgentId, s.action);
      }
    }
  },
}));
