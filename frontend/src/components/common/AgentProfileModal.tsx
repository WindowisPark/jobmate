import { useEffect, useRef } from "react";
import { AGENTS } from "@/types/agent";
import type { AgentId } from "@/types/agent";
import { useChatStore } from "@/stores/chatStore";
import { AgentAvatar } from "./AgentAvatar";

interface Props {
  agentId: AgentId;
  onClose: () => void;
}

export function AgentProfileModal({ agentId, onClose }: Props) {
  const agent = AGENTS[agentId];
  const setActiveRoom = useChatStore((s) => s.setActiveRoom);
  const modalRef = useRef<HTMLDivElement>(null);

  // Escape 키로 닫기 + 포커스 트랩
  useEffect(() => {
    const prevFocus = document.activeElement as HTMLElement | null;
    modalRef.current?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }

      // 포커스 트랩
      if (e.key === "Tab" && modalRef.current) {
        const focusable = modalRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusable.length === 0) return;

        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (!first || !last) return;

        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      prevFocus?.focus();
    };
  }, [onClose]);

  const handleDM = () => {
    setActiveRoom(`dm-${agentId}`);
    onClose();
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.6)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        animation: "fadeIn 0.2s ease",
      }}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={`${agent.name} 프로필`}
    >
      <div
        ref={modalRef}
        tabIndex={-1}
        style={{
          background: "var(--bg-hover)",
          borderRadius: 16,
          width: 380,
          maxWidth: "90vw",
          overflow: "hidden",
          boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
          animation: "slideUp 0.25s ease",
          outline: "none",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Banner */}
        <div
          style={{
            height: 80,
            background: `linear-gradient(135deg, ${agent.color}44 0%, ${agent.color}22 100%)`,
            position: "relative",
          }}
        >
          <div
            style={{
              position: "absolute",
              bottom: -32,
              left: 24,
              border: `3px solid var(--bg-hover)`,
              borderRadius: 16,
              overflow: "hidden",
              background: "var(--bg-hover)",
            }}
          >
            <AgentAvatar agentId={agentId} size={64} />
          </div>
        </div>

        {/* Content */}
        <div style={{ padding: "36px 24px 24px" }}>
          {/* Name + role */}
          <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 4 }}>
            <span style={{ fontSize: 22, fontWeight: 800, color: agent.color }}>
              {agent.name}
            </span>
            <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>
              {agent.role}
            </span>
          </div>

          {/* Personality */}
          <div style={{ fontSize: 14, color: "var(--text-secondary)", marginBottom: 16 }}>
            {agent.personality}
          </div>

          {/* Greeting */}
          <div
            style={{
              background: `${agent.color}11`,
              border: `1px solid ${agent.color}22`,
              borderRadius: "var(--radius-lg)",
              padding: "12px 16px",
              marginBottom: 16,
              fontSize: 14,
              color: "var(--text-primary)",
              fontStyle: "italic",
              lineHeight: 1.5,
            }}
          >
            &ldquo;{agent.greeting}&rdquo;
          </div>

          {/* Skills */}
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 8, fontWeight: 600 }}>
              전문 분야
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {agent.skills.map((skill) => (
                <span
                  key={skill}
                  style={{
                    fontSize: 12,
                    padding: "4px 10px",
                    borderRadius: 20,
                    background: `${agent.color}15`,
                    color: agent.color,
                    border: `1px solid ${agent.color}30`,
                  }}
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={handleDM}
              style={{
                flex: 1,
                padding: "10px",
                borderRadius: "var(--radius-md)",
                background: agent.color,
                color: "#fff",
                border: "none",
                fontWeight: 700,
                fontSize: 14,
                cursor: "pointer",
                transition: "opacity var(--transition-fast)",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.85")}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
            >
              메시지 보내기
            </button>
            <button
              onClick={onClose}
              style={{
                padding: "10px 20px",
                borderRadius: "var(--radius-md)",
                background: "var(--bg-tertiary)",
                color: "var(--text-secondary)",
                border: "1px solid var(--border)",
                fontWeight: 600,
                fontSize: 14,
                cursor: "pointer",
              }}
            >
              닫기
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
