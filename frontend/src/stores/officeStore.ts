import { create } from "zustand";
import type { AgentId } from "@/types/agent";
import type { AgentBehavior, AgentOfficeFull } from "@/types/office";
import {
  TILE_SIZE,
  AGENT_DESK_POSITIONS,
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

interface OfficeStoreState {
  agents: Record<AgentId, AgentOfficeFull>;
  // WebSocket에서 호출: 에이전트를 책상으로 보냄
  sendToDesk: (agentId: AgentId) => void;
  // WebSocket에서 호출: 에이전트 타이핑 시작
  startTyping: (agentId: AgentId) => void;
  // WebSocket에서 호출: 에이전트 응답 완료 → 돌아다님
  finishTyping: (agentId: AgentId) => void;
  // 애니메이션 틱
  tick: () => void;
  // 하위 호환
  setAgentState: (agentId: AgentId, state: { action?: string }) => void;
  setAllAgentStates: (states: Record<string, { action: string; position: { x: number; y: number } }>) => void;
}

const MOVE_SPEED = 1.5;
const WANDER_INTERVAL = 3000; // ms
let lastWanderTime = 0;

export const useOfficeStore = create<OfficeStoreState>((set, get) => ({
  agents: {
    seo_yeon: initAgent("seo_yeon"),
    jun_ho: initAgent("jun_ho"),
    ha_eun: initAgent("ha_eun"),
    min_su: initAgent("min_su"),
  },

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
      };
    }),

  tick: () =>
    set((state) => {
      const now = Date.now();
      const newAgents = { ...state.agents };

      for (const id of Object.keys(newAgents) as AgentId[]) {
        const agent = { ...newAgents[id]! };
        newAgents[id] = agent;

        // 애니메이션 프레임 업데이트
        agent.frameIndex = (agent.frameIndex + 1) % 60;

        if (agent.behavior === "typing") {
          // 타이핑 중이면 움직이지 않음
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

          // 방향 결정
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
          } else if (agent.behavior === "wandering") {
            // 주기적으로 새 목적지 설정
            if (now - lastWanderTime > WANDER_INTERVAL) {
              const spot = randomWalkableSpot();
              agent.targetX = spot.x;
              agent.targetY = spot.y;
            }
          }
        }
      }

      // 전체 wander 타이밍
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

      return { agents: newAgents };
    }),

  // 하위 호환 (WebSocket 이벤트에서 호출)
  setAgentState: (agentId, partial) => {
    const action = partial.action ?? "idle";
    if (action === "thinking" || action === "talking" || action === "typing") {
      get().sendToDesk(agentId);
    } else if (action === "idle") {
      get().finishTyping(agentId);
    }
  },

  setAllAgentStates: (states) => {
    const store = get();
    for (const [id, s] of Object.entries(states)) {
      if (s.action === "idle") {
        // 모든 에이전트가 idle이면 finishTyping 처리는 이미 됨
      } else if (s.action === "talking" || s.action === "typing" || s.action === "thinking") {
        store.sendToDesk(id as AgentId);
      }
    }
  },
}));
