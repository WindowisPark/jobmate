import { useState, useEffect } from "react";
import { ChatRoom } from "@/components/chat/ChatRoom";
import { OfficeView } from "@/components/office/OfficeView";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { AgentProfileModal } from "@/components/common/AgentProfileModal";
import type { AgentId } from "@/types/agent";

const MOBILE_BREAKPOINT = 768;

export function Layout() {
  const [profileAgentId, setProfileAgentId] = useState<AgentId | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= MOBILE_BREAKPOINT);

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth <= MOBILE_BREAKPOINT);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  // 모바일에서 방 선택 시 사이드바 닫기
  const handleRoomSelect = () => {
    if (isMobile) setSidebarOpen(false);
  };

  return (
    <div style={{ display: "flex", height: "100vh", background: "var(--bg-primary)", position: "relative" }}>
      {/* 모바일 오버레이 */}
      {isMobile && sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.5)",
            zIndex: 99,
          }}
        />
      )}

      {/* 사이드바 */}
      <div
        style={isMobile ? {
          position: "fixed",
          top: 0,
          left: 0,
          bottom: 0,
          width: "var(--sidebar-width)",
          zIndex: 100,
          transform: sidebarOpen ? "translateX(0)" : "translateX(-100%)",
          transition: "transform var(--transition-normal)",
        } : undefined}
      >
        <Sidebar
          onAgentProfileClick={(id) => setProfileAgentId(id as AgentId)}
          onRoomSelect={handleRoomSelect}
        />
      </div>

      {/* 메인 컨텐츠 */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {/* 모바일 헤더 */}
        {isMobile && (
          <div style={{
            display: "flex",
            alignItems: "center",
            padding: "8px 12px",
            borderBottom: "1px solid var(--border)",
            background: "var(--bg-secondary)",
          }}>
            <button
              onClick={() => setSidebarOpen(true)}
              style={{
                background: "none",
                border: "none",
                color: "var(--text-primary)",
                fontSize: 22,
                cursor: "pointer",
                padding: "4px 8px",
              }}
              aria-label="메뉴 열기"
            >
              ☰
            </button>
            <span style={{ fontWeight: 700, color: "var(--text-white)", marginLeft: 8 }}>
              JobMate
            </span>
          </div>
        )}
        <OfficeView />
        <ChatRoom />
      </div>

      {profileAgentId && (
        <AgentProfileModal
          agentId={profileAgentId}
          onClose={() => setProfileAgentId(null)}
        />
      )}
    </div>
  );
}
