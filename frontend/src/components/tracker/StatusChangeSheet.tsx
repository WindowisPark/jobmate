// 상태 변경 시트 — 모바일에서 칸반 DnD 대신 쓰는 방식. 탈락/포기는 종료단계를 반드시 고른다.
import { useState } from "react";
import { useApplicationStore } from "@/stores/applicationStore";
import { toast } from "@/stores/toastStore";
import {
  ACTIVE_STATUSES, CLOSED_STATUSES, CLOSED_WITH_STAGE, END_STAGE_LABELS, STATUS_LABELS,
  type Application, type ApplicationStatus, type EndStage,
} from "@/types/application";
import s from "./Tracker.module.css";

interface Props { app: Application; onClose: () => void; onChanged?: (app: Application) => void }

export function StatusChangeSheet({ app, onClose, onChanged }: Props) {
  const changeStatus = useApplicationStore((st) => st.changeStatus);
  const [status, setStatus] = useState<ApplicationStatus>(app.status);
  const [stage, setStage] = useState<EndStage | "">(app.end_stage ?? "");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const needsStage = CLOSED_WITH_STAGE.includes(status);

  const confirm = async () => {
    if (needsStage && !stage) return toast.warning("어느 단계에서 끝났는지 골라주세요");
    setBusy(true);
    try {
      const { celebration } = await changeStatus(app.id, status, needsStage ? (stage as EndStage) : null, note);
      toast.success(celebration ? `🎉 ${app.company.name} 최종합격! 축하해요` : `${STATUS_LABELS[status]}(으)로 바꿨어요`);
      const updated = useApplicationStore.getState().byId[app.id];
      if (updated) onChanged?.(updated);
      onClose();
    } catch {
      // api.ts 가 토스트를 띄운다
    } finally {
      setBusy(false);
    }
  };

  const opt = (k: ApplicationStatus) => (
    <button key={k} type="button" className={`${s.statusOpt} ${status === k ? s.statusOptSel : ""}`} onClick={() => setStatus(k)}>
      {STATUS_LABELS[k]}
    </button>
  );

  return (
    <div className={s.sheetBackdrop} onClick={onClose}>
      <div className={s.sheetBox} onClick={(e) => e.stopPropagation()} role="dialog" aria-label="상태 변경">
        <div className={s.sheetTitle}>
          <span>{app.company.name} · {app.position}</span>
          <button type="button" className={s.iconBtn} onClick={onClose}>닫기</button>
        </div>
        <div className={s.subLabel}>진행</div>
        <div className={s.statusGrid}>{ACTIVE_STATUSES.map(opt)}</div>
        <div className={s.subLabel}>결과</div>
        <div className={s.statusGrid}>{CLOSED_STATUSES.map(opt)}</div>
        {needsStage && (
          <>
            <div className={s.subLabel}>어느 단계에서 끝났나요? *</div>
            <div className={s.stageRow}>
              {(Object.keys(END_STAGE_LABELS) as EndStage[]).map((k) => (
                <button key={k} type="button" className={`${s.stageOpt} ${stage === k ? s.stageOptSel : ""}`} onClick={() => setStage(k)}>
                  {END_STAGE_LABELS[k]}
                </button>
              ))}
            </div>
          </>
        )}
        <div className={s.field}>
          <label>메모 (선택)</label>
          <input value={note} onChange={(e) => setNote(e.target.value)} maxLength={500} placeholder="면접관 3명, 시스템 설계 질문 많았음" />
        </div>
        <div className={s.formActions}>
          <button type="button" className={s.primaryBtn} onClick={confirm} disabled={busy || status === app.status && !note}>
            {busy ? "저장 중…" : "확인"}
          </button>
        </div>
      </div>
    </div>
  );
}
