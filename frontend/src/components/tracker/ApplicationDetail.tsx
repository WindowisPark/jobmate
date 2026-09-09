// 지원 상세 — 상태·이력 타임라인 + 수정 폼
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApplicationStore } from "@/stores/applicationStore";
import { STATUS_LABELS, type Application, type ApplicationDetail as Detail, type HistoryEntry } from "@/types/application";
import { ApplicationForm } from "./ApplicationForm";
import { StatusChangeSheet } from "./StatusChangeSheet";
import { DDayChip, StatusBadge, TrackChip, formatDate } from "./bits";
import s from "./Tracker.module.css";

const SOURCE_LABEL: Record<HistoryEntry["source"], string> = { user: "", agent: "· 에이전트", import: "· 노션 임포트" };

export function ApplicationDetailView({ id }: { id: string }) {
  const navigate = useNavigate();
  const { byId, fetchDetail, remove } = useApplicationStore();
  const [detail, setDetail] = useState<Detail | null>(null);
  const [editing, setEditing] = useState(false);
  const [sheet, setSheet] = useState(false);
  const app: Application | undefined = byId[id];

  useEffect(() => {
    let alive = true;
    fetchDetail(id).then((d) => { if (alive) setDetail(d); }).catch(() => navigate("/village/tracker"));
    return () => { alive = false; };
  }, [id, fetchDetail, navigate, app?.status, app?.updated_at]);

  const cur = app ?? detail;
  if (!cur) return <p className={s.subLabel}>불러오는 중…</p>;

  const onDelete = async () => {
    if (!window.confirm(`"${cur.title}" 지원 내역을 지울까요? 이력도 함께 사라져요.`)) return;
    await remove(id);
    navigate("/village/tracker");
  };

  return (
    <div>
      <div className={s.detailHead}>
        <div className={s.detailTitle}>{cur.company.name} <span style={{ color: "var(--text-secondary)", fontWeight: 500 }}>{cur.position}</span></div>
        <StatusBadge status={cur.status} />
        <DDayChip deadline={cur.deadline_at} active={cur.is_active} />
        <TrackChip app={cur} />
      </div>
      <div className={s.formActions} style={{ justifyContent: "flex-start", marginBottom: 12 }}>
        <button type="button" className={s.primaryBtn} onClick={() => setSheet(true)}>상태 변경</button>
        <button type="button" className={s.iconBtn} onClick={() => setEditing((v) => !v)}>{editing ? "수정 닫기" : "수정"}</button>
        {cur.posting_url && <a className={s.iconBtn} href={cur.posting_url} target="_blank" rel="noreferrer">공고 열기 ↗</a>}
        <span style={{ flex: 1 }} />
        <button type="button" className={s.dangerBtn} onClick={onDelete}>삭제</button>
      </div>

      {editing ? (
        <ApplicationForm initial={cur} onSaved={() => setEditing(false)} onCancel={() => setEditing(false)} />
      ) : (
        <dl style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "4px 12px", fontSize: 13, margin: 0 }}>
          {cur.end_stage_label && <><dt className={s.subLabel}>종료단계</dt><dd>{cur.end_stage_label}</dd></>}
          {cur.next_action && <><dt className={s.subLabel}>다음 액션</dt><dd style={{ color: "var(--accent-warm)" }}>{cur.next_action}</dd></>}
          {cur.next_event_at && <><dt className={s.subLabel}>다음 일정</dt><dd>{formatDate(cur.next_event_at, true)}</dd></>}
          <dt className={s.subLabel}>마감</dt><dd>{cur.deadline_at ?? "—"}</dd>
          <dt className={s.subLabel}>지원일</dt><dd>{cur.applied_at ?? "—"}</dd>
          <dt className={s.subLabel}>발견일</dt><dd>{cur.discovered_at ?? "—"}</dd>
          {(cur.employment_label || cur.hiring_label) && <><dt className={s.subLabel}>형태</dt><dd>{[cur.employment_label, cur.hiring_label].filter(Boolean).join(" · ")}</dd></>}
          {cur.resume_document && <><dt className={s.subLabel}>이력서</dt><dd>{cur.resume_document.title}</dd></>}
          {cur.season && <><dt className={s.subLabel}>시즌</dt><dd>{cur.season}</dd></>}
          {cur.retrospective && <><dt className={s.subLabel}>회고</dt><dd style={{ whiteSpace: "pre-wrap" }}>{cur.retrospective}</dd></>}
        </dl>
      )}

      <div className={s.section}>
        <div className={s.sectionTitle}>이력</div>
        <ul className={s.timeline}>
          {(detail?.history ?? []).slice().reverse().map((h) => (
            <li key={h.id}>
              <time>{formatDate(h.changed_at, true)}</time>
              <span>
                {h.from_status ? `${STATUS_LABELS[h.from_status]} → ` : ""}<b style={{ color: "var(--text-white)" }}>{STATUS_LABELS[h.to_status]}</b>
                {h.note ? ` — ${h.note}` : ""} <span className={s.subLabel}>{SOURCE_LABEL[h.source]}</span>
              </span>
            </li>
          ))}
        </ul>
      </div>

      {sheet && <StatusChangeSheet app={cur} onClose={() => setSheet(false)} />}
    </div>
  );
}
