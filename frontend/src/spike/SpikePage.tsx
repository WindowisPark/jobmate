// 내 방 — 개발용 미리보기 페이지(/spike, DEV 전용). M2에서 /village 라우트로 승격되면 삭제.

import { useCallback, useState } from "react";
import { MallangRoom } from "@/components/room/MallangRoom";
import { MALLANG_THEME, PIXEL_THEME, PIXEL_THEME_KENNEY } from "@/components/room/roomLayout";
import type { OpenTarget, RoomTheme } from "@/components/room/roomLayout";

const THEMES: Array<{ key: string; label: string; theme: RoomTheme; note: string }> = [
  { key: "pixel", label: "픽셀 · 블롭", theme: PIXEL_THEME, note: "Kenney 16px 방 + 방 팔레트로 그린 슬라임" },
  { key: "pixel-kenney", label: "픽셀 · Kenney 슬라임", theme: PIXEL_THEME_KENNEY, note: "Tiny Dungeon 슬라임 색상 회전(비교용)" },
  { key: "mallang", label: "말랑이 일러스트", theme: MALLANG_THEME, note: "saju 말랑이 v2 + CSS 폴백 배경(보관)" },
];

export default function SpikePage() {
  const [lit, setLit] = useState(true);
  const [themeKey, setThemeKey] = useState("pixel");
  const [banner, setBanner] = useState<string | null>(null);

  const handleOpen = useCallback((t: OpenTarget) => {
    if (t.kind === "npc") setBanner(`${t.npc.name}와 대화 시작`);
    else setBanner(t.hotspot.status === "soon" ? `${t.hotspot.label} — 준비 중이에요` : `${t.hotspot.label} ${t.hotspot.verb}`);
    window.setTimeout(() => setBanner(null), 1800);
  }, []);

  const current = THEMES.find((t) => t.key === themeKey) ?? THEMES[0]!;

  return (
    <div style={{
      minHeight: "100vh", overflow: "auto", background: "var(--bg-primary)",
      color: "var(--text-primary)", padding: 12, display: "flex", flexDirection: "column", gap: 12,
    }}>
      <header>
        <h1 style={{ fontSize: 18, color: "var(--text-white)" }}>내 방 — 미리보기</h1>
        <p style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 4 }}>
          가구 탭 → 그 앞으로 hop · 바닥 탭 → 거기로 hop · <b>방향키/WASD</b>로 걷기(가구에 막히고, 가구 앞에 멈추면 열림).
        </p>
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 10, flexWrap: "wrap", fontSize: 12 }}>
          <div style={{ display: "flex", gap: 6 }}>
            {THEMES.map((t) => (
              <button
                key={t.key}
                onClick={() => setThemeKey(t.key)}
                title={t.note}
                style={{
                  fontSize: 12, padding: "5px 10px", borderRadius: 6, cursor: "pointer", border: "1px solid var(--border)",
                  background: themeKey === t.key ? "var(--bg-active)" : "var(--bg-tertiary)",
                  color: themeKey === t.key ? "#fff" : "var(--text-secondary)",
                }}
              >
                {t.label}
              </button>
            ))}
          </div>
          <label style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
            <input type="checkbox" checked={lit} onChange={(e) => setLit(e.target.checked)} />
            📝 지원 마감 임박 신호 (D-day ≤ 3)
          </label>
        </div>
      </header>

      <MallangRoom theme={current.theme} lit={lit} onOpen={handleOpen} />

      <p style={{ fontSize: 11, color: "var(--text-muted)", textAlign: "center" }}>{current.note} · 렌더러: DOM/CSS · 번들 증가 0</p>

      {banner && (
        <div style={{
          position: "fixed", left: "50%", bottom: 24, transform: "translateX(-50%)",
          background: "var(--accent-green)", color: "#10231a", fontWeight: 700, fontSize: 13,
          padding: "10px 18px", borderRadius: 999, boxShadow: "0 6px 20px rgba(0,0,0,0.4)", zIndex: 50,
        }}>
          {banner}
        </div>
      )}
    </div>
  );
}
