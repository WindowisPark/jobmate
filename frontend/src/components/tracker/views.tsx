// 📝 지원 대시보드의 5개 뷰 — 노션 '지원' DB 의 🔥진행중 · 📅캘린더 · 📊시즌별 · 🧭트랙별 · 📋전체
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  groupBySeason, groupByTrack, selectBoardColumns, selectCalendarEvents, type GroupStat,
} from "@/stores/applicationStore";
import { STATUS_LABELS, type Application } from "@/types/application";
import { DDayChip, Empty, StatusBadge, TrackChip, formatDate } from "./bits";
import s from "./Tracker.module.css";

interface ViewProps { items: Application[]; onChangeStatus: (app: Application) => void }

function Card({ app, onChangeStatus }: { app: Application; onChangeStatus: (a: Application) => void }) {
  const navigate = useNavigate();
  return (
    <div className={s.card} onClick={() => navigate(`/village/tracker/${app.id}`)} role="button" tabIndex={0}
      onKeyDown={(e) => { if (e.key === "Enter") navigate(`/village/tracker/${app.id}`); }}>
      <div className={s.cardTop}>
        <div>
          <div className={s.company}>{app.company.name}</div>
          <div className={s.position}>{app.position}</div>
        </div>
        <DDayChip deadline={app.deadline_at} active={app.is_active} />
      </div>
      {app.next_action && <div className={s.nextAction}>→ {app.next_action}</div>}
      <div className={s.cardFoot}>
        <TrackChip app={app} />
        {app.next_event_at && <span className={s.calEvent} style={{ fontSize: 11 }}>◆ {formatDate(app.next_event_at, true)}</span>}
        <button type="button" className={s.cardStatusBtn} onClick={(e) => { e.stopPropagation(); onChangeStatus(app); }}>
          상태 변경 ▾
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- 🔥 진행중
export function BoardView({ items, onChangeStatus }: ViewProps) {
  const columns = useMemo(() => selectBoardColumns(items), [items]);
  const [showEmpty, setShowEmpty] = useState(false);
  if (!items.some((a) => a.is_active)) return <Empty>진행 중인 지원이 없어요.<br />"+ 지원 추가"로 첫 공고를 올려보세요.</Empty>;
  const visible = showEmpty ? columns : columns.filter((c) => c.items.length > 0);
  const hidden = columns.length - visible.length;
  return (
    <div>
      {hidden > 0 && !showEmpty && (
        <button type="button" className={s.tab} style={{ marginBottom: 6 }} onClick={() => setShowEmpty(true)}>빈 단계 {hidden}개 보기 ▸</button>
      )}
      {showEmpty && <button type="button" className={s.tab} style={{ marginBottom: 6 }} onClick={() => setShowEmpty(false)}>빈 단계 숨기기 ▾</button>}
    <div className={s.board}>
      {visible.map((col) => (
        <div key={col.status} className={s.column}>
          <div className={s.columnHead}>
            <StatusBadge status={col.status} small />
            <span className={s.count}>{col.items.length}</span>
          </div>
          {col.items.map((a) => <Card key={a.id} app={a} onChangeStatus={onChangeStatus} />)}
        </div>
      ))}
    </div>
    </div>
  );
}

// ---------------------------------------------------------------- 📅 캘린더
const DOW = ["일", "월", "화", "수", "목", "금", "토"];
const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

export function CalendarView({ items, onChangeStatus }: ViewProps) {
  const today = new Date();
  const [cursor, setCursor] = useState(() => new Date(today.getFullYear(), today.getMonth(), 1));
  const [selected, setSelected] = useState<string | null>(iso(today));
  const events = useMemo(() => selectCalendarEvents(items), [items]);

  const first = new Date(cursor.getFullYear(), cursor.getMonth(), 1);
  const start = new Date(first);
  start.setDate(first.getDate() - first.getDay());
  const cells = Array.from({ length: 42 }, (_, i) => {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    return d;
  });
  const todayIso = iso(today);
  const selectedEvents = selected ? events[selected] ?? [] : [];

  return (
    <div>
      <div className={s.calHead}>
        <button type="button" className={s.iconBtn} onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth() - 1, 1))}>‹</button>
        <strong style={{ color: "var(--text-white)" }}>{cursor.getFullYear()}년 {cursor.getMonth() + 1}월</strong>
        <button type="button" className={s.iconBtn} onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1))}>›</button>
      </div>
      <div className={s.calGrid}>
        {DOW.map((d) => <div key={d} className={s.calDow}>{d}</div>)}
        {cells.map((d) => {
          const key = iso(d);
          const evs = events[key] ?? [];
          const out = d.getMonth() !== cursor.getMonth();
          return (
            <div key={key}
              className={`${s.calCell} ${out ? s.calCellOut : ""} ${key === todayIso ? s.calCellToday : ""} ${key === selected ? s.calCellSel : ""}`}
              onClick={() => setSelected(key)}>
              <span className={s.calDay}>{d.getDate()}</span>
              {evs.slice(0, 3).map((ev, i) => (
                <span key={i} className={`${s.calDot} ${ev.kind === "deadline" ? s.calDeadline : s.calEvent}`}>
                  {ev.kind === "deadline" ? "●" : "◆"} {ev.app.company.name}
                </span>
              ))}
              {evs.length > 3 && <span className={s.calDot}>+{evs.length - 3}</span>}
            </div>
          );
        })}
      </div>
      <div className={s.calList}>
        {selected && selectedEvents.length === 0 && <Empty>{formatDate(selected)} 에 일정이 없어요</Empty>}
        {selectedEvents.map((ev, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span className={ev.kind === "deadline" ? s.calDeadline : s.calEvent}>{ev.kind === "deadline" ? "● 마감" : "◆ 일정"}</span>
            <div style={{ flex: 1 }}><Card app={ev.app} onChangeStatus={onChangeStatus} /></div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- 📊 시즌별 · 🧭 트랙별 (접이식 그룹 + 표)
function Groups({ groups, onChangeStatus }: { groups: GroupStat[]; onChangeStatus: (a: Application) => void }) {
  const [open, setOpen] = useState<Record<string, boolean>>({});
  if (groups.length === 0) return <Empty>아직 지원 내역이 없어요</Empty>;
  return (
    <div>
      {groups.map((g, gi) => {
        const isOpen = open[g.key] ?? gi === 0;
        return (
          <div key={g.key} className={s.group}>
            <div className={s.groupHead} onClick={() => setOpen({ ...open, [g.key]: !isOpen })}>
              <span>{isOpen ? "▾" : "▸"} {g.label}</span>
              <span className={s.count}>{g.items.length}건</span>
              <span className={s.funnel}>
                <span>지원 <b>{g.applied}</b></span><span>서류 <b>{g.passed_docs}</b></span>
                <span>면접 <b>{g.interview}</b></span><span>합격 <b>{g.offer}</b></span>
              </span>
            </div>
            {isOpen && <Table items={g.items} onChangeStatus={onChangeStatus} compact />}
          </div>
        );
      })}
    </div>
  );
}
export function SeasonView({ items, onChangeStatus }: ViewProps) {
  return <Groups groups={useMemo(() => groupBySeason(items), [items])} onChangeStatus={onChangeStatus} />;
}
export function TrackView({ items, onChangeStatus }: ViewProps) {
  return <Groups groups={useMemo(() => groupByTrack(items), [items])} onChangeStatus={onChangeStatus} />;
}

// ---------------------------------------------------------------- 📋 전체
type SortKey = "title" | "status" | "deadline_at" | "applied_at" | "track";
function Table({ items, onChangeStatus, compact }: ViewProps & { compact?: boolean }) {
  const navigate = useNavigate();
  const [sort, setSort] = useState<{ key: SortKey; dir: 1 | -1 }>({ key: "deadline_at", dir: 1 });
  const sorted = useMemo(() => {
    const val = (a: Application): string => {
      switch (sort.key) {
        case "title": return a.title;
        case "status": return a.status_label;
        case "track": return a.track?.name ?? "";
        case "applied_at": return a.applied_at ?? "9999";
        default: return a.deadline_at ?? "9999";
      }
    };
    return [...items].sort((a, b) => val(a).localeCompare(val(b)) * sort.dir);
  }, [items, sort]);
  const th = (key: SortKey, label: string) => (
    <th onClick={() => setSort((p) => ({ key, dir: p.key === key ? (p.dir === 1 ? -1 : 1) : 1 }))}>
      {label}{sort.key === key ? (sort.dir === 1 ? " ↑" : " ↓") : ""}
    </th>
  );
  return (
    <div style={{ overflowX: "auto" }}>
      <table className={s.table}>
        <thead>
          <tr>
            {th("title", "제목")}{th("status", "상태")}{th("deadline_at", "마감")}
            {!compact && th("applied_at", "지원일")}{th("track", "트랙")}<th></th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((a) => (
            <tr key={a.id} onClick={() => navigate(`/village/tracker/${a.id}`)}>
              <td><div className={s.company} style={{ fontSize: 12 }}>{a.title}</div>
                {a.end_stage_label && <span className={s.subLabel}>{a.end_stage_label}에서 종료</span>}</td>
              <td><StatusBadge status={a.status} small /></td>
              <td><DDayChip deadline={a.deadline_at} active={a.is_active} /> <span className={s.subLabel}>{formatDate(a.deadline_at)}</span></td>
              {!compact && <td>{formatDate(a.applied_at)}</td>}
              <td><TrackChip app={a} /></td>
              <td><button type="button" className={s.cardStatusBtn} onClick={(e) => { e.stopPropagation(); onChangeStatus(a); }}>변경</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export function TableView({ items, onChangeStatus }: ViewProps) {
  const [q, setQ] = useState("");
  const filtered = useMemo(() => {
    const k = q.trim().toLowerCase();
    if (!k) return items;
    return items.filter((a) => [a.title, a.position, a.company.name, STATUS_LABELS[a.status], a.track?.name ?? ""].join(" ").toLowerCase().includes(k));
  }, [items, q]);
  return (
    <div>
      <input className={s.search} placeholder="회사·포지션·상태·트랙 검색" value={q} onChange={(e) => setQ(e.target.value)} />
      {filtered.length === 0 ? <Empty>검색 결과가 없어요</Empty> : <Table items={filtered} onChangeStatus={onChangeStatus} />}
    </div>
  );
}
