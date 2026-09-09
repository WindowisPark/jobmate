// 📝 지원 대시보드 건물 — 패널 셸. 라우트: /village/tracker[/new|/import|/:id]
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useApplicationStore, type TrackerView } from "@/stores/applicationStore";
import type { Application } from "@/types/application";
import { ApplicationDetailView } from "./ApplicationDetail";
import { ApplicationForm } from "./ApplicationForm";
import { ImportCsvDialog } from "./ImportCsvDialog";
import { StatusChangeSheet } from "./StatusChangeSheet";
import { BoardView, CalendarView, SeasonView, TableView, TrackView } from "./views";
import { Empty } from "./bits";
import s from "./Tracker.module.css";

const VIEWS: { key: TrackerView; label: string }[] = [
  { key: "board", label: "진행중" }, { key: "calendar", label: "캘린더" },
  { key: "season", label: "시즌별" }, { key: "track", label: "트랙별" }, { key: "table", label: "전체" },
];

export function TrackerBuilding({ mode }: { mode: "list" | "new" | "import" | "detail" }) {
  const navigate = useNavigate();
  const { id } = useParams();
  const { items, loading, loaded, error, view, setView, fetchAll, fetchRefs } = useApplicationStore();
  const [sheetApp, setSheetApp] = useState<Application | null>(null);

  useEffect(() => {
    if (!loaded) void fetchAll();
    void fetchRefs();
  }, [loaded, fetchAll, fetchRefs]);

  const close = () => navigate("/village");
  const back = () => navigate("/village/tracker");

  const title = mode === "new" ? "지원 추가" : mode === "import" ? "노션에서 가져오기" : mode === "detail" ? "지원 상세" : "지원 대시보드";

  return (
    <section className={s.building} aria-label="지원 대시보드">
      <header className={s.head}>
        {mode !== "list" && <button type="button" className={s.iconBtn} onClick={back} aria-label="목록으로">‹</button>}
        <h2 className={s.title}>{title}</h2>
        {mode === "list" && (
          <>
            <button type="button" className={s.iconBtn} onClick={() => navigate("/village/tracker/import")}>CSV</button>
            <button type="button" className={s.primaryBtn} onClick={() => navigate("/village/tracker/new")}>+ 지원 추가</button>
          </>
        )}
        <button type="button" className={s.iconBtn} onClick={close} aria-label="방으로">✕</button>
      </header>

      {mode === "list" && (
        <nav className={s.tabs} aria-label="보기">
          {VIEWS.map((v) => (
            <button key={v.key} type="button" className={`${s.tab} ${view === v.key ? s.tabActive : ""}`} onClick={() => setView(v.key)}>
              {v.label}
            </button>
          ))}
        </nav>
      )}

      <div className={s.body}>
        {mode === "new" && <ApplicationForm onSaved={(a) => navigate(`/village/tracker/${a.id}`)} onCancel={back} />}
        {mode === "import" && <ImportCsvDialog onDone={back} />}
        {mode === "detail" && id && <ApplicationDetailView id={id} />}
        {mode === "list" && (
          loading && !loaded ? <Empty>불러오는 중…</Empty>
          : error ? <Empty>{error}</Empty>
          : view === "board" ? <BoardView items={items} onChangeStatus={setSheetApp} />
          : view === "calendar" ? <CalendarView items={items} onChangeStatus={setSheetApp} />
          : view === "season" ? <SeasonView items={items} onChangeStatus={setSheetApp} />
          : view === "track" ? <TrackView items={items} onChangeStatus={setSheetApp} />
          : <TableView items={items} onChangeStatus={setSheetApp} />
        )}
      </div>

      {sheetApp && <StatusChangeSheet app={sheetApp} onClose={() => setSheetApp(null)} />}
    </section>
  );
}

/** documents / jobs 건물 — 아직 준비 중 */
export function ComingSoonBuilding({ label, note }: { label: string; note: string }) {
  const navigate = useNavigate();
  return (
    <section className={s.building}>
      <header className={s.head}>
        <h2 className={s.title}>{label}</h2>
        <button type="button" className={s.iconBtn} onClick={() => navigate("/village")} aria-label="방으로">✕</button>
      </header>
      <div className={s.body}><Empty>{note}</Empty></div>
    </section>
  );
}
