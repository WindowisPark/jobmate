// 마을 홈 — 방(MallangRoom) + 가구 패널(Outlet). 데스크톱은 우측 패널, 모바일은 전체 화면 시트.
// 방의 신호(책상 점등·말풍선)는 전부 서버(GET /api/world/state)에서 온다.
import { useCallback, useEffect, useMemo } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { MallangRoom } from "@/components/room/MallangRoom";
import type { HotspotId, OpenTarget, RoomBubble } from "@/components/room/roomLayout";
import { useIsMobile } from "@/hooks/useIsMobile";
import { useChatStore } from "@/stores/chatStore";
import { HOTSPOT_ROUTES, npcChatRoute, useWorldStore } from "@/stores/worldStore";
import { toast } from "@/stores/toastStore";
import s from "./Village.module.css";

const PANEL_BY_PATH: Array<[prefix: string, id: HotspotId]> = [
  ["/village/tracker", "tracker"],
  ["/village/documents", "documents"],
  ["/village/jobs", "jobs"],
  ["/village/chat", "mental"],
];

export function VillageLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const isMobile = useIsMobile();
  const { activeHotspot, enter, exit, buildings, prompts, refresh, accept, dismiss } =
    useWorldStore();
  const setPendingReply = useChatStore((st) => st.setPendingReply);
  const addMessage = useChatStore((st) => st.addMessage);

  // 방에 들어올 때, 그리고 탭으로 돌아올 때 신호를 다시 받는다
  useEffect(() => {
    void refresh();
    const onVisible = () => { if (document.visibilityState === "visible") void refresh(); };
    document.addEventListener("visibilitychange", onVisible);
    return () => document.removeEventListener("visibilitychange", onVisible);
  }, [refresh]);

  // 패널에서 무언가 바꾸고 방으로 돌아오면 신호가 낡는다
  useEffect(() => {
    if (location.pathname === "/village") void refresh();
  }, [location.pathname, refresh]);

  const tracker = buildings.find((b) => b.id === "tracker");
  const lit = tracker?.lit ?? false;
  const litLabel = tracker?.label ?? undefined;

  const bubbles: RoomBubble[] = useMemo(
    () => prompts.map((p) => ({ id: p.id, agentId: p.agent_id, text: p.text })),
    [prompts],
  );

  // URL ↔ 열린 가구 동기화 (뒤로가기로 패널이 닫힌다)
  useEffect(() => {
    const hit = PANEL_BY_PATH.find(([p]) => location.pathname.startsWith(p));
    if (hit) enter(hit[1]);
    else exit();
  }, [location.pathname, enter, exit]);

  const onOpen = (t: OpenTarget) => {
    if (t.kind === "npc") {
      navigate(npcChatRoute(t.agentId));
      return;
    }
    const route = HOTSPOT_ROUTES[t.hotspot.id];
    if (!route) {
      toast.info(`${t.hotspot.label}는 준비 중이에요`);
      return;
    }
    navigate(route);
  };

  // 말풍선을 누르면 그 대사가 DM 에 남고, 답장 초안이 채워진 채 대화가 열린다
  const onBubbleAccept = useCallback(
    async (b: RoomBubble) => {
      const result = await accept(b.id);
      if (!result) return;
      // 서버는 이 대사를 DM 에 이미 저장했다. 화면에도 같은 줄을 올려 대화가 이어지게 한다.
      // (DM 은 아직 지난 대화를 불러오지 않는다 — 그래서 여기서 직접 넣는다)
      addMessage(result.room_id, {
        id: crypto.randomUUID(),
        conversationId: result.room_id,
        senderType: "agent",
        agentId: result.agent_id,
        content: result.text,
        createdAt: new Date().toISOString(),
      });
      if (result.suggested_reply) setPendingReply(result.room_id, result.suggested_reply);
      navigate(`/village/chat/${result.room_id}`);
    },
    [accept, addMessage, navigate, setPendingReply],
  );

  const panelOpen = activeHotspot !== null && location.pathname !== "/village";

  return (
    <div className={`${s.layout} ${isMobile ? s.mobile : ""}`}>
      <div className={`${s.roomArea} ${panelOpen && isMobile ? s.roomHidden : ""}`} aria-hidden={panelOpen && isMobile}>
        <header className={s.topbar}>
          <span className={s.brand}>JobMate <small>내 방</small></span>
          <nav className={s.nav} />
        </header>
        <MallangRoom
          lit={lit}
          litLabel={litLabel}
          bubbles={bubbles}
          onBubbleAccept={onBubbleAccept}
          onBubbleDismiss={(b) => void dismiss(b.id)}
          onOpen={onOpen}
        />
        {!panelOpen && (
          <p className={s.hint}>가구나 친구를 누르거나 방향키로 걸어가세요 · 도착하면 한 번 더 눌러 열어요 · 책상이 빛나면 마감 3일 안</p>
        )}
      </div>

      {panelOpen && (
        <aside className={`${s.panel} ${isMobile ? s.sheet : ""}`} role="dialog" aria-modal={isMobile}>
          <Outlet />
        </aside>
      )}
    </div>
  );
}
