// 마을 홈 — 방(MallangRoom) + 가구 패널(Outlet). 데스크톱은 우측 패널, 모바일은 전체 화면 시트.
import { useEffect } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { MallangRoom } from "@/components/room/MallangRoom";
import type { HotspotId, OpenTarget } from "@/components/room/roomLayout";
import { useIsMobile } from "@/hooks/useIsMobile";
import { useApplicationStore, selectUrgent } from "@/stores/applicationStore";
import { dDay, ddayLabel } from "@/types/application";
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
  const { activeHotspot, enter, exit } = useWorldStore();
  const items = useApplicationStore((st) => st.items);
  const loaded = useApplicationStore((st) => st.loaded);
  const fetchAll = useApplicationStore((st) => st.fetchAll);

  // 방 신호는 실제 데이터에서 — 마감 3일 이내 진행 건이 있으면 책상 점등
  useEffect(() => { if (!loaded) void fetchAll(); }, [loaded, fetchAll]);
  const urgent = selectUrgent(items);
  const lit = urgent.length > 0;
  const minD = urgent.reduce<number | null>((m, a) => { const d = dDay(a.deadline_at); return d === null ? m : m === null ? d : Math.min(m, d); }, null);
  const litLabel = lit ? ddayLabel(minD) : undefined;

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

  const panelOpen = activeHotspot !== null && location.pathname !== "/village";

  return (
    <div className={`${s.layout} ${isMobile ? s.mobile : ""}`}>
      <div className={`${s.roomArea} ${panelOpen && isMobile ? s.roomHidden : ""}`} aria-hidden={panelOpen && isMobile}>
        <header className={s.topbar}>
          <span className={s.brand}>JobMate <small>내 방</small></span>
          <nav className={s.nav} />
        </header>
        <MallangRoom lit={lit} litLabel={litLabel} onOpen={onOpen} />
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
