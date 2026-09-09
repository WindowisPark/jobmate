// 트래커 공용 조각 — 상태 배지, D-day 칩, 트랙 칩, 빈 상태
import { STATUS_COLORS, STATUS_LABELS, ddayLabel, dDay, type Application, type ApplicationStatus } from "@/types/application";
import s from "./Tracker.module.css";

export function StatusBadge({ status, small }: { status: ApplicationStatus; small?: boolean }) {
  return (
    <span className={`${s.badge} ${small ? s.badgeSmall : ""}`} style={{ background: `${STATUS_COLORS[status]}26`, color: STATUS_COLORS[status], borderColor: `${STATUS_COLORS[status]}55` }}>
      {STATUS_LABELS[status]}
    </span>
  );
}

export function DDayChip({ deadline, active = true }: { deadline: string | null; active?: boolean }) {
  const n = dDay(deadline);
  if (n === null) return null;
  const tone = !active ? s.ddayMuted : n < 0 ? s.ddayOver : n <= 3 ? s.ddayUrgent : n <= 7 ? s.ddaySoon : "";
  return <span className={`${s.dday} ${tone}`} title={`마감 ${deadline}`}>{ddayLabel(n)}</span>;
}

export function TrackChip({ app }: { app: Application }) {
  if (!app.track) return null;
  return (
    <span className={s.trackChip} style={{ borderColor: app.track.color ?? undefined, color: app.track.color ?? undefined }}>
      {app.track.name}
    </span>
  );
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <div className={s.empty}>{children}</div>;
}

export function formatDate(iso: string | null, withTime = false): string {
  if (!iso) return "—";
  const d = new Date(iso.length === 10 ? `${iso}T00:00:00` : iso);
  const date = `${d.getMonth() + 1}/${d.getDate()}`;
  if (!withTime) return date;
  return `${date} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}
