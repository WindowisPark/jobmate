// 지원 생성/수정 폼. 상태는 생성 시에만 고르고, 수정은 StatusChangeSheet 로만(서버 규칙과 동일).
import { useState } from "react";
import { useApplicationStore } from "@/stores/applicationStore";
import {
  CLOSED_WITH_STAGE, EMPLOYMENT_LABELS, END_STAGE_LABELS, HIRING_LABELS, STATUS_LABELS,
  type Application, type ApplicationInput, type ApplicationStatus, type EmploymentType, type EndStage, type HiringType,
} from "@/types/application";
import s from "./Tracker.module.css";

interface Props {
  initial?: Application;             // 있으면 수정 모드
  onSaved: (app: Application) => void;
  onCancel: () => void;
}

const toLocalInput = (iso: string | null) => (iso ? iso.slice(0, 16) : "");

export function ApplicationForm({ initial, onSaved, onCancel }: Props) {
  const { companies, tracks, documents, create, update } = useApplicationStore();
  const [f, setF] = useState({
    company_name: initial?.company.name ?? "",
    position: initial?.position ?? "",
    title: initial?.title ?? "",
    track_name: initial?.track?.name ?? "",
    resume_document_title: initial?.resume_document?.title ?? "",
    posting_url: initial?.posting_url ?? "",
    status: (initial?.status ?? "discovered") as ApplicationStatus,
    end_stage: (initial?.end_stage ?? "") as EndStage | "",
    employment_type: (initial?.employment_type ?? "") as EmploymentType | "",
    hiring_type: (initial?.hiring_type ?? "") as HiringType | "",
    discovered_at: initial?.discovered_at ?? "",
    applied_at: initial?.applied_at ?? "",
    deadline_at: initial?.deadline_at ?? "",
    next_event_at: toLocalInput(initial?.next_event_at ?? null),
    next_action: initial?.next_action ?? "",
    retrospective: initial?.retrospective ?? "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setF((p) => ({ ...p, [k]: e.target.value }));
  const needsStage = !initial && CLOSED_WITH_STAGE.includes(f.status);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!f.company_name.trim()) return setError("회사명을 입력해주세요");
    if (!f.position.trim()) return setError("포지션을 입력해주세요");
    if (needsStage && !f.end_stage) return setError("탈락·포기는 종료단계를 골라주세요");
    setSaving(true);
    try {
      const nul = (v: string) => (v.trim() ? v.trim() : null);
      const base: ApplicationInput = {
        company_name: f.company_name.trim(),
        position: f.position.trim(),
        title: f.title.trim() || undefined,
        posting_url: nul(f.posting_url),
        employment_type: (f.employment_type || null) as EmploymentType | null,
        hiring_type: (f.hiring_type || null) as HiringType | null,
        discovered_at: nul(f.discovered_at),
        applied_at: nul(f.applied_at),
        deadline_at: nul(f.deadline_at),
        next_event_at: f.next_event_at ? new Date(f.next_event_at).toISOString() : null,
        next_action: nul(f.next_action),
        retrospective: nul(f.retrospective),
      };
      if (f.track_name.trim()) base.track_name = f.track_name.trim();
      else if (initial?.track) base.clear_track = true;
      if (f.resume_document_title.trim()) base.resume_document_title = f.resume_document_title.trim();
      else if (initial?.resume_document) base.clear_resume_document = true;

      const saved = initial
        ? await update(initial.id, base)
        : await create({ ...base, status: f.status, end_stage: needsStage ? (f.end_stage as EndStage) : null });
      onSaved(saved);
    } catch (err: any) {
      setError(err.message ?? "저장에 실패했어요");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form className={s.form} onSubmit={submit}>
      <div className={s.row}>
        <div className={s.field}>
          <label>회사 *</label>
          <input list="tracker-companies" value={f.company_name} onChange={set("company_name")} placeholder="카카오" required />
          <datalist id="tracker-companies">{companies.map((c) => <option key={c.id} value={c.name} />)}</datalist>
        </div>
        <div className={s.field}>
          <label>포지션 * <span className={s.subLabel}>(공고 직무명 그대로)</span></label>
          <input value={f.position} onChange={set("position")} placeholder="백엔드 개발자" required />
        </div>
      </div>
      <div className={s.field}>
        <label>제목 <span className={s.subLabel}>(비우면 "회사 - 포지션")</span></label>
        <input value={f.title} onChange={set("title")} placeholder={f.company_name && f.position ? `${f.company_name} - ${f.position}` : ""} />
      </div>
      <div className={s.row}>
        <div className={s.field}>
          <label>트랙</label>
          <input list="tracker-tracks" value={f.track_name} onChange={set("track_name")} placeholder="백엔드" />
          <datalist id="tracker-tracks">{tracks.map((t) => <option key={t.id} value={t.name} />)}</datalist>
        </div>
        <div className={s.field}>
          <label>이력서 버전</label>
          <input list="tracker-docs" value={f.resume_document_title} onChange={set("resume_document_title")} placeholder="이력서 v3" />
          <datalist id="tracker-docs">{documents.map((d) => <option key={d.id} value={d.title} />)}</datalist>
        </div>
      </div>
      <div className={s.field}>
        <label>공고 URL</label>
        <input type="url" value={f.posting_url} onChange={set("posting_url")} placeholder="https://" />
      </div>

      {!initial && (
        <div className={s.row}>
          <div className={s.field}>
            <label>상태</label>
            <select value={f.status} onChange={set("status")}>
              {(Object.keys(STATUS_LABELS) as ApplicationStatus[]).map((k) => <option key={k} value={k}>{STATUS_LABELS[k]}</option>)}
            </select>
          </div>
          {needsStage && (
            <div className={s.field}>
              <label>종료단계 * <span className={s.subLabel}>(어디서 끝났나)</span></label>
              <select value={f.end_stage} onChange={set("end_stage")} required>
                <option value="">선택</option>
                {(Object.keys(END_STAGE_LABELS) as EndStage[]).map((k) => <option key={k} value={k}>{END_STAGE_LABELS[k]}</option>)}
              </select>
            </div>
          )}
        </div>
      )}

      <div className={s.row}>
        <div className={s.field}>
          <label>고용형태</label>
          <select value={f.employment_type} onChange={set("employment_type")}>
            <option value="">—</option>
            {(Object.keys(EMPLOYMENT_LABELS) as EmploymentType[]).map((k) => <option key={k} value={k}>{EMPLOYMENT_LABELS[k]}</option>)}
          </select>
        </div>
        <div className={s.field}>
          <label>채용방식</label>
          <select value={f.hiring_type} onChange={set("hiring_type")}>
            <option value="">—</option>
            {(Object.keys(HIRING_LABELS) as HiringType[]).map((k) => <option key={k} value={k}>{HIRING_LABELS[k]}</option>)}
          </select>
        </div>
      </div>
      <div className={s.row}>
        <div className={s.field}><label>발견일</label><input type="date" value={f.discovered_at} onChange={set("discovered_at")} /></div>
        <div className={s.field}><label>지원일</label><input type="date" value={f.applied_at} onChange={set("applied_at")} /></div>
      </div>
      <div className={s.row}>
        <div className={s.field}><label>마감일</label><input type="date" value={f.deadline_at} onChange={set("deadline_at")} /></div>
        <div className={s.field}><label>다음 일정 <span className={s.subLabel}>(코테·면접·발표)</span></label><input type="datetime-local" value={f.next_event_at} onChange={set("next_event_at")} /></div>
      </div>
      <div className={s.field}>
        <label>다음 액션 <span className={s.subLabel}>(내가 해야 할 일 한 줄)</span></label>
        <input value={f.next_action} onChange={set("next_action")} maxLength={500} placeholder="자소서 3번 문항 다듬기" />
      </div>
      <div className={s.field}>
        <label>한 줄 회고 <span className={s.subLabel}>(결과 났을 때 — 왜 됐는지/안 됐는지, 다음에 바꿀 것)</span></label>
        <textarea value={f.retrospective} onChange={set("retrospective")} />
      </div>
      {error && <p className={s.error}>{error}</p>}
      <div className={s.formActions}>
        <button type="button" className={s.iconBtn} onClick={onCancel}>취소</button>
        <button type="submit" className={s.primaryBtn} disabled={saving}>{saving ? "저장 중…" : initial ? "저장" : "추가"}</button>
      </div>
    </form>
  );
}
