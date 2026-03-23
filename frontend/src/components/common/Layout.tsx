import { ChatRoom } from "@/components/chat/ChatRoom";
import { OfficeView } from "@/components/office/OfficeView";
import { Sidebar } from "@/components/sidebar/Sidebar";

export function Layout() {
  return (
    <div style={{ display: "flex", height: "100vh", background: "#1a1d21" }}>
      <Sidebar />
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <OfficeView />
        <ChatRoom />
      </div>
    </div>
  );
}
