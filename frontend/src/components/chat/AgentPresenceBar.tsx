import { useOfficeStore } from "@/stores/officeStore";
import { AGENTS, AGENT_IDS } from "@/types/agent";
import type { AgentId } from "@/types/agent";
import { AgentAvatar } from "@/components/common/AgentAvatar";
import { useChatStore } from "@/stores/chatStore";

const BEHAVIOR_LABELS: Record<string, string> = {
  wandering: "대기 중",
  walking_to: "이동 중",
  walking_to_desk: "이동 중",
  typing: "응답 작성 중",
  searching: "채용공고 검색 중",
  analyzing: "시장 분석 중",
  reading: "이력서 검토 중",
  breathing: "호흡 가이드 중",
  interview_prep: "면접 준비 중",
  collaborating: "협업 중",
  idle_at_spot: "대기 중",
  drinking: "잠시 쉬는 중",
  chatting: "대화 중",
};

const BEHAVIOR_ICONS: Record<string, string> = {
  typing: "✍️",
  searching: "🔍",
  analyzing: "📊",
  reading: "📄",
  breathing: "🌿",
  interview_prep: "🎯",
  collaborating: "🤝",
};

function isActive(behavior: string): boolean {
  return !["wandering", "idle_at_spot", "drinking"].includes(behavior);
}

function AgentChip({ agentId }: { agentId: AgentId }) {
  const agent = AGENTS[agentId];
  const officeAgent = useOfficeStore((s) => s.agents[agentId]);
  const typingAgents = useChatStore((s) => s.typingAgents);
  const behavior = officeAgent?.behavior || "wandering";
  const isTyping = typingAgents.includes(agentId);
  const active = isActive(behavior) || isTyping;

  const statusLabel = isTyping
    ? "응답 작성 중"
    : BEHAVIOR_LABELS[behavior] || "대기 중";
  const statusIcon = isTyping
    ? "✍️"
    : BEHAVIOR_ICONS[behavior] || "";

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "8px 14px",
        borderRadius: "var(--radius-md)",
        background: active
          ? `linear-gradient(135deg, ${agent.color}18, ${agent.color}08)`
          : "var(--bg-card)",
        border: active
          ? `1px solid ${agent.color}40`
          : "1px solid var(--border)",
        transition: "all var(--transition-normal)",
        minWidth: 0,
        flex: "1 1 0",
        boxShadow: active
          ? `0 0 12px ${agent.color}20, inset 0 1px 0 ${agent.color}15`
          : "none",
      }}
    >
      {/* 아바타 + 상태링 */}
      <div style={{ position: "relative", flexShrink: 0 }}>
        <div
          style={{
            borderRadius: "50%",
            padding: 2,
            border: active
              ? `2px solid ${agent.color}80`
              : "2px solid transparent",
            transition: "border-color var(--transition-normal)",
            animation: active ? "breathe 2.5s ease-in-out infinite" : "none",
          }}
        >
          <AgentAvatar agentId={agentId} size={30} />
        </div>
        {/* 상태 도트 */}
        <div
          style={{
            position: "absolute",
            bottom: 0,
            right: 0,
            width: 10,
            height: 10,
            borderRadius: "50%",
            background: active ? agent.color : "var(--text-muted)",
            border: "2px solid var(--bg-primary)",
          }}
        />
      </div>

      <div style={{ minWidth: 0, overflow: "hidden" }}>
        <div
          style={{
            fontSize: 12,
            fontWeight: 700,
            color: active ? agent.color : "var(--text-secondary)",
            lineHeight: 1.3,
          }}
        >
          {agent.name}
        </div>
        <div
          style={{
            fontSize: 10,
            color: active ? "var(--text-primary)" : "var(--text-muted)",
            lineHeight: 1.4,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            transition: "color var(--transition-fast)",
          }}
        >
          {statusIcon && <span style={{ marginRight: 3 }}>{statusIcon}</span>}
          {statusLabel}
        </div>
      </div>
    </div>
  );
}

export function AgentPresenceBar() {
  return (
    <div
      style={{
        display: "flex",
        gap: 6,
        padding: "10px 16px",
        background: "var(--bg-secondary)",
        borderBottom: "1px solid var(--border)",
      }}
    >
      {AGENT_IDS.map((id) => (
        <AgentChip key={id} agentId={id} />
      ))}
    </div>
  );
}
