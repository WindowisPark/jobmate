import { useState } from "react";
import { ChatRoom } from "@/components/chat/ChatRoom";
import { OfficeView } from "@/components/office/OfficeView";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { AgentProfileModal } from "@/components/common/AgentProfileModal";
import type { AgentId } from "@/types/agent";

export function Layout() {
  const [profileAgentId, setProfileAgentId] = useState<AgentId | null>(null);

  return (
    <div style={{ display: "flex", height: "100vh", background: "var(--bg-primary)" }}>
      <Sidebar onAgentProfileClick={(id) => setProfileAgentId(id as AgentId)} />
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
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
