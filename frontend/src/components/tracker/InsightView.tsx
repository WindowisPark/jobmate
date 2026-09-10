// 📈 인사이트 — 지원 데이터를 읽어주는 화면.
// 계산은 전부 서버(/applications/stats)가 한다. 여기서는 읽고 보여주기만 한다.
import { useEffect } from "react";
import { useApplicationStore } from "@/stores/applicationStore";
import { Empty } from "./bits";
import s from "./Tracker.module.css";

/** 이 수보다 적은 표본에는 비율을 강조하지 않는다. 3건 중 1건을 33%라 부르면 거짓말에 가깝다. */
const MIN_SAMPLE = 5;

interface Row {
  key: string;
  label: string;
  sub?: string;
  total: number;
  applied: number;
  passed_docs: number;
  interview: number;
  offer: number;
}

export function InsightView() {
  const { stats, fetchStats } = useApplicationStore();

  // 상태를 바꾸고 돌아오면 숫자가 낡는다. 탭에 들어올 때마다 새로 받는다.
  useEffect(() => {
    void fetchStats();
  }, [fetchStats]);

  if (!stats) return <Empty>불러오는 중…</Empty>;
  if (stats.total === 0) return <Empty>아직 지원 내역이 없어요{"\n"}몇 건 쌓이면 여기서 흐름이 보여요</Empty>;

  const f = stats.funnel;

  return (
    <div className={s.insight}>
      <Funnel applied={f.applied} passed={f.passed_docs} interview={f.interview} offer={f.offer} />

      <StatTable
        title="채용방식별"
        note="자소서 없는 수시는 지원이 쉬워 통과율이 낮게 나옵니다. 뭉쳐 보면 거꾸로 읽혀요."
        rows={stats.by_hiring_type.map((h) => ({ key: h.hiring_label, label: h.hiring_label, ...h }))}
      />

      <StatTable
        title="제출물별"
        note="어떤 버전을 붙였을 때 서류가 붙었는지."
        rows={stats.by_document.map((d) => ({
          key: d.document_id,
          label: d.title,
          sub: d.doc_type_label,
          ...d,
        }))}
      />

      <StatTable
        title="트랙별"
        rows={stats.by_track.map((t) => ({ key: t.track_id ?? "none", label: t.track_name, ...t }))}
      />
    </div>
  );
}

function Funnel({ applied, passed, interview, offer }: { applied: number; passed: number; interview: number; offer: number }) {
  const steps = [
    { label: "지원", n: applied, color: "var(--accent-blue)" },
    { label: "서류통과", n: passed, color: "var(--accent-green)" },
    { label: "면접", n: interview, color: "var(--accent-warm)" },
    { label: "최종합격", n: offer, color: "var(--agent-seo-yeon)" },
  ];
  return (
    <section className={s.insightBlock}>
      <div className={s.insightTitle}>전체 흐름</div>
      <div className={s.funnelRows}>
        {steps.map((st, i) => {
          const width = applied > 0 ? Math.max(2, (st.n / applied) * 100) : 0;
          const rate = i === 0 || applied === 0 ? null : Math.round((st.n / applied) * 100);
          return (
            <div key={st.label} className={s.funnelRow}>
              <span className={s.funnelLabel}>{st.label}</span>
              <span className={s.funnelBarWrap}>
                <span className={s.funnelBar} style={{ width: `${width}%`, background: st.color }} />
              </span>
              <span className={s.funnelNum}>{st.n}</span>
              <span className={s.funnelRate}>{rate === null ? "" : `${rate}%`}</span>
            </div>
          );
        })}
      </div>
      {applied < MIN_SAMPLE && (
        <p className={s.insightNote}>지원 {applied}건이라 비율은 아직 참고만 하세요.</p>
      )}
    </section>
  );
}

function StatTable({ title, note, rows }: { title: string; note?: string; rows: Row[] }) {
  const shown = rows.filter((r) => r.total > 0);
  if (shown.length === 0) return null;
  return (
    <section className={s.insightBlock}>
      <div className={s.insightTitle}>{title}</div>
      {note && <p className={s.insightNote}>{note}</p>}
      <table className={s.insightTable}>
        <thead>
          <tr>
            <th>{title.replace("별", "")}</th>
            <th>지원</th>
            <th>서류</th>
            <th>면접</th>
            <th>합격</th>
            <th>서류통과율</th>
          </tr>
        </thead>
        <tbody>
          {shown.map((r) => {
            const small = r.applied < MIN_SAMPLE;
            const rate = r.applied > 0 ? Math.round((r.passed_docs / r.applied) * 100) : null;
            return (
              <tr key={r.key}>
                <td>
                  <span className={s.insightName}>{r.label}</span>
                  {r.sub && <span className={s.insightSub}>{r.sub}</span>}
                </td>
                <td>{r.applied}</td>
                <td>{r.passed_docs}</td>
                <td>{r.interview}</td>
                <td>{r.offer}</td>
                <td
                  className={small ? s.rateWeak : s.rate}
                  title={small ? `지원 ${r.applied}건이라 표본이 적어요` : undefined}
                >
                  {rate === null ? "—" : `${rate}%`}
                  {small && rate !== null && <span className={s.rateWeakMark}>?</span>}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
