// 노션 "📝 지원" CSV 임포트 — dry-run 리포트를 먼저 보여주고 확정한다.
import { useRef, useState } from "react";
import { useApplicationStore } from "@/stores/applicationStore";
import { toast } from "@/stores/toastStore";
import type { ImportReport } from "@/types/application";
import s from "./Tracker.module.css";

export function ImportCsvDialog({ onDone }: { onDone: () => void }) {
  const importCsv = useApplicationStore((st) => st.importCsv);
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [onDuplicate, setOnDuplicate] = useState<"skip" | "update">("skip");
  const [report, setReport] = useState<ImportReport | null>(null);
  const [busy, setBusy] = useState(false);

  const run = async (dryRun: boolean) => {
    if (!file) return;
    setBusy(true);
    try {
      const rep = await importCsv(file, { dryRun, onDuplicate });
      setReport(rep);
      if (!dryRun) {
        toast.success(`${rep.created}건 추가 · ${rep.updated}건 갱신 · ${rep.skipped}건 건너뜀`);
        onDone();
      }
    } catch {
      // api.ts 가 토스트
    } finally {
      setBusy(false);
    }
  };

  const pick = (f: File | undefined) => {
    if (!f) return;
    setFile(f);
    setReport(null);
  };

  return (
    <div>
      <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: 10 }}>
        노션의 <b>📝 지원</b> 데이터베이스에서 <code>··· → 내보내기 → CSV</code> 로 받은 파일을 올리면
        상태·종료단계·트랙·이력서 버전이 그대로 들어옵니다. D-day·시즌 같은 수식 열은 무시해요.
      </p>
      <label className={s.dropzone}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); pick(e.dataTransfer.files[0]); }}>
        <input ref={fileRef} type="file" accept=".csv,text/csv" onChange={(e) => pick(e.target.files?.[0])} />
        {file ? <b style={{ color: "var(--text-white)" }}>{file.name}</b> : "CSV 파일을 끌어다 놓거나 클릭해서 선택"}
        <div className={s.subLabel}>2MB · 2,000행까지</div>
      </label>

      <div className={s.radioRow}>
        <label><input type="radio" checked={onDuplicate === "skip"} onChange={() => setOnDuplicate("skip")} /> 이미 있는 건 건너뛰기</label>
        <label><input type="radio" checked={onDuplicate === "update"} onChange={() => setOnDuplicate("update")} /> 이미 있는 건 덮어쓰기</label>
      </div>

      <div className={s.formActions} style={{ justifyContent: "flex-start" }}>
        <button type="button" className={s.iconBtn} disabled={!file || busy} onClick={() => run(true)}>미리 검사</button>
        <button type="button" className={s.primaryBtn} disabled={!file || busy || !report} onClick={() => run(false)}>
          {busy ? "처리 중…" : "가져오기"}
        </button>
      </div>

      {report && (
        <div className={s.section}>
          <div className={s.report}>
            <div className={s.stat}><b>{report.total_rows}</b><span>행</span></div>
            <div className={s.stat}><b>{report.created}</b><span>추가</span></div>
            <div className={s.stat}><b>{report.updated}</b><span>갱신</span></div>
            <div className={s.stat}><b>{report.errors.length}</b><span>오류</span></div>
          </div>
          {report.errors.length > 0 && (
            <>
              <div className={s.sectionTitle}>오류 행 (건너뜁니다)</div>
              <table className={s.table}>
                <tbody>
                  {report.errors.slice(0, 20).map((e, i) => (
                    <tr key={i}><td>{e.row}행</td><td>{e.field ?? ""}</td><td style={{ color: "#ff9a9a" }}>{e.reason}</td></tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
          {report.preview.length > 0 && (
            <>
              <div className={s.sectionTitle}>미리보기 (앞 {report.preview.length}건)</div>
              <table className={s.table}>
                <thead><tr><th>회사</th><th>포지션</th><th>상태</th><th>마감</th><th>이력서</th></tr></thead>
                <tbody>
                  {report.preview.map((p, i) => (
                    <tr key={i}>
                      <td>{String(p.company ?? "")}</td><td>{String(p.position ?? "")}</td>
                      <td>{String(p.status ?? "")}{p.end_stage ? ` (${String(p.end_stage)})` : ""}</td>
                      <td>{String(p.deadline_at ?? "")}</td><td>{String(p.resume ?? "")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
          {report.dry_run && <p className={s.subLabel} style={{ marginTop: 8 }}>검사만 했어요 — 아직 저장되지 않았습니다. 위 "가져오기"로 확정하세요.</p>}
        </div>
      )}
    </div>
  );
}
