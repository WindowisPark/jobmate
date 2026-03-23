export type AgentId = "seo_yeon" | "jun_ho" | "ha_eun" | "min_su";

export interface AgentProfile {
  id: AgentId;
  name: string;
  role: string;
  avatarUrl: string;
  color: string;
  emoji: string;
  personality: string;
  skills: string[];
  greeting: string;
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
    color: "#e06c75",
    emoji: "📝",
    personality: "따뜻하지만 직설적",
    skills: ["이력서 첨삭", "면접 코칭", "자소서 피드백"],
    greeting: "이력서든 면접이든, 같이 준비하자!",
  },
  jun_ho: {
    id: "jun_ho",
    name: "박준호",
    role: "취업 리서처",
    avatarUrl: "/assets/agents/jun-ho.png",
    color: "#61afef",
    emoji: "🔍",
    personality: "데이터 중심, 꼼꼼",
    skills: ["채용공고 검색", "시장 분석", "트렌드 리포트"],
    greeting: "데이터로 보여줄게, 어떤 직무가 궁금해?",
  },
  ha_eun: {
    id: "ha_eun",
    name: "이하은",
    role: "멘탈 케어",
    avatarUrl: "/assets/agents/ha-eun.png",
    color: "#98c379",
    emoji: "🌿",
    personality: "공감형, 차분",
    skills: ["감정 케어", "호흡 운동", "루틴 관리"],
    greeting: "힘들 때 편하게 이야기해, 항상 여기 있어.",
  },
  min_su: {
    id: "min_su",
    name: "정민수",
    role: "현직자 멘토",
    avatarUrl: "/assets/agents/min-su.png",
    color: "#e5c07b",
    emoji: "💡",
    personality: "유머 + 현실 조언",
    skills: ["업계 인사이트", "동기부여", "현실 조언"],
    greeting: "형이 알려주는 진짜 얘기, 편하게 물어봐 ㅋㅋ",
  },
};

export const AGENT_IDS = Object.keys(AGENTS) as AgentId[];
