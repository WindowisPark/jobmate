import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AGENTS } from "@/types/agent";
import { useOfficeStore } from "@/stores/officeStore";
import { useChatStore } from "@/stores/chatStore";
import { useAuthStore } from "@/stores/authStore";
import { AgentAvatar } from "@/components/common/AgentAvatar";
import { api } from "@/utils/api";
import styles from "./Sidebar.module.css";

interface Props {
  onAgentProfileClick?: (agentId: string) => void;
  onRoomSelect?: () => void;
}

export function Sidebar({ onAgentProfileClick, onRoomSelect }: Props) {
  const navigate = useNavigate();
  const officeAgents = useOfficeStore((s) => s.agents);
  const { rooms, activeRoomId, setActiveRoom, messages } = useChatStore();
  const { user, isGuest, clearAuth } = useAuthStore();
  const [hoveredRoom, setHoveredRoom] = useState<string | null>(null);

  const handleLogout = async () => {
    try {
      await api.post("/auth/logout");
    } catch {
      // 쿠키 만료 등 무시
    }
    clearAuth();
    navigate("/login");
  };

  const channels = rooms.filter((r) => r.type === "channel");
  const dms = rooms.filter((r) => r.type === "dm");

  return (
    <aside className={styles.sidebar} role="navigation" aria-label="사이드바 네비게이션">
      {/* Header */}
      <div className={styles.header}>
        <span className={styles.logo}>JobMate</span>
        <span className={styles.badge}>BETA</span>
      </div>

      <div className={styles.divider} />

      {/* Channels */}
      <div className={styles.sectionLabel}>Channels</div>
      {channels.map((room) => (
        <div
          key={room.id}
          className={`${styles.roomItem} ${activeRoomId === room.id ? styles.active : ""}`}
          onClick={() => { setActiveRoom(room.id); onRoomSelect?.(); }}
          onMouseEnter={() => setHoveredRoom(room.id)}
          onMouseLeave={() => setHoveredRoom(null)}
        >
          <span className={styles.channelHash}>#</span>
          <span>{room.name}</span>
          {activeRoomId !== room.id && (messages[room.id]?.length ?? 0) > 0 && (
            <span className={styles.unreadDot} />
          )}
        </div>
      ))}

      <div className={styles.divider} />

      {/* Direct Messages */}
      <div className={styles.sectionLabel}>Direct Messages</div>
      {dms.map((room) => {
        const agent = room.agentId ? AGENTS[room.agentId] : null;
        if (!agent) return null;
        const officeState = room.agentId ? officeAgents[room.agentId] : null;
        const isActive = officeState?.behavior === "typing" || officeState?.behavior === "walking_to_desk";
        const isSelected = activeRoomId === room.id;

        return (
          <div
            key={room.id}
            className={`${styles.dmItem} ${isSelected ? styles.active : ""}`}
            onClick={() => { setActiveRoom(room.id); onRoomSelect?.(); }}
            onMouseEnter={() => setHoveredRoom(room.id)}
            onMouseLeave={() => setHoveredRoom(null)}
          >
            {/* Avatar */}
            <div className={styles.dmAvatarWrap}>
              <AgentAvatar agentId={agent.id} size={32} />
              <div
                className={styles.statusDot}
                style={{ background: isActive ? "var(--online-green)" : "#44b700" }}
              />
            </div>

            {/* Info */}
            <div className={styles.dmInfo}>
              <span className={styles.dmName} style={{ color: isSelected ? "#fff" : undefined }}>
                {agent.name}
              </span>
              <span className={styles.dmRole}>{agent.role}</span>
            </div>

            {/* Profile button on hover */}
            {hoveredRoom === room.id && !isSelected && (
              <button
                className={styles.profileBtn}
                onClick={(e) => {
                  e.stopPropagation();
                  onAgentProfileClick?.(agent.id);
                }}
                title="프로필 보기"
              >
                ···
              </button>
            )}
          </div>
        );
      })}

      {/* Footer */}
      <div className={styles.footer}>
        <div className={styles.footerUser}>
          <div className={styles.footerAvatar}>
            {(user?.nickname ?? "게스트").charAt(0)}
          </div>
          <div className={styles.footerInfo}>
            <span className={styles.footerName}>{user?.nickname ?? "게스트"}</span>
            {isGuest && <span className={styles.footerTag}>체험 중</span>}
          </div>
        </div>
        <button className={styles.logoutBtn} onClick={handleLogout} title="로그아웃">
          ↪
        </button>
      </div>
    </aside>
  );
}
