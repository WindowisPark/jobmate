// 공고 게시판 — 검색 엔진을 품지 않는다.
// 공고 탐색은 사람인·원티드가 훨씬 잘하고, 그 결과는 내 데이터가 아니라 방이 반응할 신호를 만들지 않는다.
// 이 건물이 하는 일은 하나다: 밖에서 본 공고를 트래커로 넘겨주는 다리.
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApplicationStore } from "@/stores/applicationStore";
import { toast } from "@/stores/toastStore";
import s from "./Tracker.module.css";

const SITES = [
  { name: "사람인", url: "https://www.saramin.co.kr/zf_user/search?searchword=" },
  { name: "원티드", url: "https://www.wanted.co.kr/search?query=" },
  { name: "잡코리아", url: "https://www.jobkorea.co.kr/Search/?stext=" },
];

export function JobBoardBuilding() {
  const navigate = useNavigate();
  const create = useApplicationStore((st) => st.create);
  const [q, setQ] = useState("");
  const [f, setF] = useState({ company: "", position: "", url: "", deadline: "" });
  const [saving, setSaving] = useState(false);

  const add = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!f.company.trim() || !f.position.trim()) {
      toast.info("회사와 포지션은 채워주세요");
      return;
    }
    setSaving(true);
    try {
      const app = await create({
        company_name: f.company.trim(),
        position: f.position.trim(),
        posting_url: f.url.trim() || null,
        deadline_at: f.deadline || null,
        status: "discovered",
      });
      toast.success("발견한 공고로 담았어요");
      navigate(`/village/tracker/${app.id}`);
    } catch {
      // api.ts 가 토스트
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className={s.building} aria-label="공고 게시판">
      <header className={s.head}>
        <h2 className={s.title}>공고 게시판</h2>
        <button type="button" className={s.iconBtn} onClick={() => navigate("/village")} aria-label="방으로">✕</button>
      </header>

      <div className={s.body}>
        <div className={s.insightBlock}>
          <div className={s.insightTitle}>공고 찾으러 가기</div>
          <p className={s.insightNote}>
            검색은 채용 사이트가 더 잘합니다. 여기서는 찾은 공고를 담는 일만 해요.
          </p>
          <div className={s.field}>
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="백엔드 개발자"
              aria-label="검색어"
            />
          </div>
          <div className={s.siteLinks}>
            {SITES.map((site) => (
              <a
                key={site.name}
                className={s.iconBtn}
                href={site.url + encodeURIComponent(q.trim() || "신입")}
                target="_blank"
                rel="noreferrer"
              >
                {site.name} ↗
              </a>
            ))}
          </div>
        </div>

        <form className={s.insightBlock} onSubmit={add}>
          <div className={s.insightTitle}>발견한 공고 담기</div>
          <p className={s.insightNote}>담아두면 마감이 가까워질 때 방 책상에 불이 켜집니다.</p>
          <div className={s.row}>
            <div className={s.field}>
              <label>회사 *</label>
              <input value={f.company} onChange={(e) => setF({ ...f, company: e.target.value })} placeholder="카카오" />
            </div>
            <div className={s.field}>
              <label>포지션 *</label>
              <input value={f.position} onChange={(e) => setF({ ...f, position: e.target.value })} placeholder="백엔드 개발자" />
            </div>
          </div>
          <div className={s.row}>
            <div className={s.field}>
              <label>공고 URL</label>
              <input type="url" value={f.url} onChange={(e) => setF({ ...f, url: e.target.value })} placeholder="https://" />
            </div>
            <div className={s.field}>
              <label>마감일</label>
              <input type="date" value={f.deadline} onChange={(e) => setF({ ...f, deadline: e.target.value })} />
            </div>
          </div>
          <div className={s.formActions}>
            <button type="submit" className={s.primaryBtn} disabled={saving}>
              {saving ? "담는 중…" : "발견함으로 담기"}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}
