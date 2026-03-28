import { useState, useEffect } from "react";
import { AGENTS, AGENT_IDS } from "@/types/agent";
import type { AgentId } from "@/types/agent";
import { AgentAvatar } from "@/components/common/AgentAvatar";

interface Props {
  filter: string;
  onSelect: (agentId: AgentId) => void;
  onClose?: () => void;
}

export function MentionPopup({ filter, onSelect, onClose }: Props) {
  const [activeIndex, setActiveIndex] = useState(0);

  const filtered = AGENT_IDS.filter((id) => {
    if (!filter) return true;
    const a = AGENTS[id];
    return a.name.includes(filter) || a.role.includes(filter);
  });

  // 필터 변경 시 인덱스 리셋
  useEffect(() => {
    setActiveIndex(0);
  }, [filter]);

  // 키보드 탐색
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (filtered.length === 0) return;

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setActiveIndex((i) => (i + 1) % filtered.length);
          break;
        case "ArrowUp":
          e.preventDefault();
          setActiveIndex((i) => (i - 1 + filtered.length) % filtered.length);
          break;
        case "Enter": {
          e.preventDefault();
          const selected = filtered[activeIndex];
          if (selected) onSelect(selected);
          break;
        }
        case "Escape":
          e.preventDefault();
          onClose?.();
          break;
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [filtered, activeIndex, onSelect, onClose]);

  if (filtered.length === 0) return null;

  return (
    <div
      style={{
        position: "absolute",
        bottom: "100%",
        left: 20,
        right: 20,
        background: "var(--bg-hover)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)",
        padding: 6,
        marginBottom: 4,
        boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
        zIndex: 100,
        animation: "slideUp 0.15s ease",
      }}
      role="listbox"
      aria-label="멤버 멘션"
    >
      <div
        style={{
          fontSize: 11,
          color: "var(--text-secondary)",
          padding: "4px 10px",
          fontWeight: 600,
        }}
      >
        멤버 멘션
      </div>
      {filtered.map((id, index) => {
        const agent = AGENTS[id];
        const isActive = index === activeIndex;
        return (
          <div
            key={id}
            id={`mention-option-${id}`}
            onClick={() => onSelect(id)}
            role="option"
            aria-selected={isActive}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "8px 10px",
              borderRadius: "var(--radius-md)",
              cursor: "pointer",
              transition: "background var(--transition-fast)",
              background: isActive ? "var(--bg-tertiary)" : "transparent",
            }}
            onMouseEnter={() => setActiveIndex(index)}
          >
            <AgentAvatar agentId={id} size={30} />
            <div>
              <div style={{ fontSize: 14, color: agent.color, fontWeight: 600 }}>
                {agent.name}
              </div>
              <div style={{ fontSize: 11, color: "var(--text-secondary)" }}>
                {agent.role} · {agent.personality}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
