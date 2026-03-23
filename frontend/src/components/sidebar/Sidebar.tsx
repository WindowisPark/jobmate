import { AGENTS } from "@/types/agent";
import { useOfficeStore } from "@/stores/officeStore";
import { useChatStore } from "@/stores/chatStore";

const AGENT_COLORS: Record<string, string> = {
  seo_yeon: "#e06c75",
  jun_ho: "#61afef",
  ha_eun: "#98c379",
  min_su: "#e5c07b",
};

export function Sidebar() {
  const officeAgents = useOfficeStore((s) => s.agents);
  const { rooms, activeRoomId, setActiveRoom, messages } = useChatStore();

  const channels = rooms.filter((r) => r.type === "channel");
  const dms = rooms.filter((r) => r.type === "dm");

  return (
    <div
      style={{
        width: 240,
        background: "#19171d",
        borderRight: "1px solid #383a3f",
        display: "flex",
        flexDirection: "column",
        padding: "16px 12px",
        overflowY: "auto",
      }}
    >
      {/* Logo */}
      <div
        style={{
          fontSize: 20,
          fontWeight: 900,
          color: "#fff",
          marginBottom: 24,
          letterSpacing: -0.5,
        }}
      >
        JobMate
      </div>

      {/* Channels */}
      <SectionLabel>Channels</SectionLabel>
      {channels.map((room) => (
        <RoomItem
          key={room.id}
          label={`# ${room.name}`}
          isActive={activeRoomId === room.id}
          hasUnread={false}
          onClick={() => setActiveRoom(room.id)}
        />
      ))}

      {/* DMs */}
      <SectionLabel style={{ marginTop: 20 }}>Direct Messages</SectionLabel>
      {dms.map((room) => {
        const agent = room.agentId ? AGENTS[room.agentId] : null;
        const color = room.agentId ? AGENT_COLORS[room.agentId] ?? "#aaa" : "#aaa";
        const officeState = room.agentId ? officeAgents[room.agentId] : null;
        const isOnline = officeState?.behavior === "typing" || officeState?.behavior === "walking_to_desk";
        const roomMessages = messages[room.id] ?? [];
        const hasUnread = roomMessages.length > 0 && activeRoomId !== room.id;

        return (
          <div
            key={room.id}
            onClick={() => setActiveRoom(room.id)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "7px 10px",
              borderRadius: 6,
              cursor: "pointer",
              background: activeRoomId === room.id ? "#1164a3" : "transparent",
            }}
          >
            <div style={{ position: "relative" }}>
              <div
                style={{
                  width: 26,
                  height: 26,
                  borderRadius: 6,
                  background:
                    activeRoomId === room.id ? "rgba(255,255,255,0.2)" : color + "22",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: activeRoomId === room.id ? "#fff" : color,
                  fontSize: 12,
                  fontWeight: 700,
                }}
              >
                {agent?.name[0]}
              </div>
              <div
                style={{
                  position: "absolute",
                  bottom: -1,
                  right: -1,
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: isOnline ? "#44b700" : "#44b700",
                  border: "2px solid #19171d",
                }}
              />
            </div>
            <div
              style={{
                fontSize: 14,
                color: activeRoomId === room.id ? "#fff" : "#d1d2d3",
                fontWeight: hasUnread ? 700 : 400,
              }}
            >
              {room.name}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function SectionLabel({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: React.CSSProperties;
}) {
  return (
    <div
      style={{
        fontSize: 11,
        color: "#9a9b9d",
        marginBottom: 6,
        fontWeight: 600,
        textTransform: "uppercase",
        letterSpacing: 0.5,
        ...style,
      }}
    >
      {children}
    </div>
  );
}

function RoomItem({
  label,
  isActive,
  hasUnread,
  onClick,
}: {
  label: string;
  isActive: boolean;
  hasUnread: boolean;
  onClick: () => void;
}) {
  return (
    <div
      onClick={onClick}
      style={{
        padding: "6px 10px",
        fontSize: 14,
        color: isActive ? "#fff" : "#d1d2d3",
        fontWeight: hasUnread ? 700 : 400,
        background: isActive ? "#1164a3" : "transparent",
        borderRadius: 6,
        cursor: "pointer",
      }}
    >
      {label}
    </div>
  );
}
