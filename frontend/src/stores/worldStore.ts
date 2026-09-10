// 방(월드) 상태 — 지원 데이터가 만든 신호. 렌더러(MallangRoom)는 이 스토어를 import 하지 않는다.
// 계산은 전부 서버(GET /api/world/state)가 한다. 여기서는 받아서 들고 있기만 한다.
import { create } from "zustand";
import type { HotspotId, RoomAgentId } from "@/components/room/roomLayout";
import { api } from "@/utils/api";

export interface NpcPrompt {
  id: string;
  agent_id: RoomAgentId;
  kind: string;
  priority: number;
  text: string;
  suggested_reply?: string;
  application_id?: string;
  approach_player?: boolean;
}

export interface BuildingSignal {
  id: string;
  lit: boolean;
  badge: number;
  label: string | null;
  celebrating: boolean;
}

interface WorldSignals {
  urgent_deadlines: unknown[];
  overdue: unknown[];
  rejection_streak_14d: number;
  active_count: number;
  celebration: { application_id: string; title: string } | null;
}

interface AcceptResult {
  room_id: string;
  agent_id: RoomAgentId;
  text: string;
  suggested_reply: string;
}

interface WorldState {
  activeHotspot: HotspotId | null;
  enter: (id: HotspotId) => void;
  exit: () => void;

  signals: WorldSignals | null;
  buildings: BuildingSignal[];
  prompts: NpcPrompt[];
  loading: boolean;

  refresh: () => Promise<void>;
  accept: (id: string) => Promise<AcceptResult | null>;
  dismiss: (id: string) => Promise<void>;
  ackCelebration: (applicationId: string) => Promise<void>;
}

interface WorldResponse {
  signals: WorldSignals;
  buildings: BuildingSignal[];
  npc_prompts: NpcPrompt[];
}

export const useWorldStore = create<WorldState>((set, get) => ({
  activeHotspot: null,
  enter: (id) => set({ activeHotspot: id }),
  exit: () => set({ activeHotspot: null }),

  signals: null,
  buildings: [],
  prompts: [],
  loading: false,

  refresh: async () => {
    if (get().loading) return;
    set({ loading: true });
    try {
      const w = await api.get<WorldResponse>("/world/state");
      set({ signals: w.signals, buildings: w.buildings, prompts: w.npc_prompts });
    } catch {
      // 방은 신호 없이도 서 있어야 한다. 실패해도 조용히 둔다.
    } finally {
      set({ loading: false });
    }
  },

  accept: async (id) => {
    // 낙관적으로 먼저 지운다 — 누른 말풍선이 잠깐 남아 있으면 두 번 누르게 된다
    set({ prompts: get().prompts.filter((p) => p.id !== id) });
    try {
      return await api.post<AcceptResult>(`/world/prompts/${encodeURIComponent(id)}/accept`);
    } catch {
      return null;
    }
  },

  dismiss: async (id) => {
    set({ prompts: get().prompts.filter((p) => p.id !== id) });
    try {
      await api.post(`/world/prompts/${encodeURIComponent(id)}/dismiss`);
    } catch {
      // 다음 새로고침에 다시 뜨는 정도의 실패다
    }
  },

  ackCelebration: async (applicationId) => {
    try {
      await api.post(`/world/celebrations/${applicationId}/ack`);
    } catch {
      /* 무시 */
    }
    await get().refresh();
  },
}));

/** 책상 등 가구의 신호를 꺼내 쓴다 */
export const selectBuilding = (id: string) => (st: WorldState) =>
  st.buildings.find((b) => b.id === id) ?? null;

/** 핫스팟 → 라우트. 채팅은 방 안 패널(/village/chat/dm-*)로 열린다 */
export const HOTSPOT_ROUTES: Record<HotspotId, string | null> = {
  tracker: "/village/tracker",
  documents: "/village/documents",
  jobs: "/village/jobs",
  mental: "/village/chat/dm-ha_eun",
  rest: null, // 준비 중
};

/** 친구(NPC)를 탭하면 그 친구와의 DM 패널 */
export const npcChatRoute = (agent: RoomAgentId) => `/village/chat/dm-${agent}`;
