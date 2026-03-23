export type AgentId = "seo_yeon" | "jun_ho" | "ha_eun" | "min_su";

export interface AgentProfile {
  id: AgentId;
  name: string;
  role: string;
  avatarUrl: string;
}

export type OfficeAction =
  | "idle"
  | "typing"
  | "thinking"
  | "searching"
  | "reading"
  | "walking"
  | "drinking"
  | "meditating"
  | "talking";

export interface AgentOfficeState {
  action: OfficeAction;
  position: { x: number; y: number };
}

export const AGENTS: Record<AgentId, AgentProfile> = {
  seo_yeon: {
    id: "seo_yeon",
    name: "김서연",
    role: "커리어 코치",
    avatarUrl: "/assets/agents/seo-yeon.png",
  },
  jun_ho: {
    id: "jun_ho",
    name: "박준호",
    role: "취업 리서처",
    avatarUrl: "/assets/agents/jun-ho.png",
  },
  ha_eun: {
    id: "ha_eun",
    name: "이하은",
    role: "멘탈 케어",
    avatarUrl: "/assets/agents/ha-eun.png",
  },
  min_su: {
    id: "min_su",
    name: "정민수",
    role: "현직자 멘토",
    avatarUrl: "/assets/agents/min-su.png",
  },
};
