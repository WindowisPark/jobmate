// 방(월드) 상태 — 어떤 가구가 열려 있는지, 방이 반응할 신호. 렌더러(MallangRoom)는 이 스토어를 import 하지 않는다.
// M3 에서 GET /api/world/state 의 signals · npc_prompts 가 여기에 들어온다.
import { create } from "zustand";
import type { HotspotId } from "@/components/room/roomLayout";

interface WorldState {
  activeHotspot: HotspotId | null;
  enter: (id: HotspotId) => void;
  exit: () => void;
}

export const useWorldStore = create<WorldState>((set) => ({
  activeHotspot: null,
  enter: (id) => set({ activeHotspot: id }),
  exit: () => set({ activeHotspot: null }),
}));

/** 핫스팟 → 라우트. mental 은 멘탈 케어 DM 으로 간다 */
export const HOTSPOT_ROUTES: Record<HotspotId, string | null> = {
  tracker: "/village/tracker",
  documents: "/village/documents",
  jobs: "/village/jobs",
  mental: "/chat/dm-ha_eun",
  rest: null,   // 준비 중
};
