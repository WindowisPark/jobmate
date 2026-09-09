// 채팅은 별도 앱이 아니라 방의 한 패널 — 소파나 친구(NPC)를 탭하면 그 친구와의 DM 이 열린다.
// 그룹 채팅은 두지 않는다(오너 결정 보류). 사이드바·채널 목록 없이 ChatRoom 본문만 embedded 로 마운트.
import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ChatRoom } from "@/components/chat/ChatRoom";
import { AgentAvatar } from "@/components/common/AgentAvatar";
import { useChatStore } from "@/stores/chatStore";
import { AGENTS } from "@/types/agent";
import s from "@/components/tracker/Tracker.module.css";

export function ChatBuilding() {
  const navigate = useNavigate();
  const { roomId = "" } = useParams();
  const { rooms, activeRoomId, setActiveRoom } = useChatStore();
  const room = rooms.find((r) => r.id === roomId && r.type === "dm");

  useEffect(() => {
    if (room && activeRoomId !== room.id) setActiveRoom(room.id);
  }, [room, activeRoomId, setActiveRoom]);

  const agent = room?.agentId ? AGENTS[room.agentId] : null;

  if (!room || !agent) {
    return (
      <section className={s.building}>
        <header className={s.head}>
          <h2 className={s.title}>대화</h2>
          <button type="button" className={s.iconBtn} onClick={() => navigate("/village")} aria-label="방으로">✕</button>
        </header>
        <div className={s.body}><div className={s.empty}>방에서 친구를 눌러 대화를 시작하세요</div></div>
      </section>
    );
  }

  return (
    <section className={s.building} aria-label={`${agent.name}와 대화`}>
      <header className={s.head}>
        <AgentAvatar agentId={agent.id} size={26} />
        <h2 className={s.title} style={{ color: agent.color }}>
          {agent.name} <small style={{ color: "var(--text-muted)", fontWeight: 500, fontSize: 12 }}>{agent.role}</small>
        </h2>
        <button type="button" className={s.iconBtn} onClick={() => navigate("/village")} aria-label="방으로">✕</button>
      </header>
      {/* ChatRoom 은 flex:1 컬럼 — 패널 높이를 그대로 채운다 */}
      <ChatRoom embedded />
    </section>
  );
}
