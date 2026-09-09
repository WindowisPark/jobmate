// 내 방 — DOM/CSS 렌더러 (테마: 픽셀 / 말랑이).
// 배경 이미지 1장(없으면 CSS 폴백) + 가구 핫스팟 + 캐릭터 PNG 스프라이트 + 말풍선.
// 이동 세 가지: 가구 탭(그 앞으로 hop) · 바닥 탭(거기로 hop) · 방향키/WASD(걷기, 가구에 막힘). 가구 앞에 멈추면 열린다.
// 픽셀 테마는 방 폭을 원본(176px)의 정수배로 스냅하고 image-rendering: pixelated 로 그려 픽셀이 뭉개지지 않게 한다.

import { useCallback, useEffect, useRef, useState } from "react";
import s from "./MallangRoom.module.css";
import {
  HOP_MS, PIXEL_THEME, WALK_SPEED_X,
  canStand, hotspotNear,
  type Box, type Hotspot, type Pct, type RoomTheme,
} from "./roomLayout";

export interface MallangRoomProps {
  theme?: RoomTheme;
  /** 지원 마감 임박(D-day≤3) 신호 → 책상 점등 */
  lit?: boolean;
  /** 미니미 그림·이름. 없으면 테마 기본 */
  me?: { src?: string; name?: string };
  /** 가구 앞에 도착했을 때(탭 이동·걷기 모두) */
  onOpen: (h: Hotspot) => void;
}

const boxStyle = (b: Box): React.CSSProperties => ({ left: `${b.x}%`, top: `${b.y}%`, width: `${b.w}%`, height: `${b.h}%` });

const KEY_DIR: Record<string, Pct> = {
  ArrowLeft: { x: -1, y: 0 }, a: { x: -1, y: 0 }, A: { x: -1, y: 0 },
  ArrowRight: { x: 1, y: 0 }, d: { x: 1, y: 0 }, D: { x: 1, y: 0 },
  ArrowUp: { x: 0, y: -1 }, w: { x: 0, y: -1 }, W: { x: 0, y: -1 },
  ArrowDown: { x: 0, y: 1 }, s: { x: 0, y: 1 }, S: { x: 0, y: 1 },
};

function isTypingTarget(el: Element | null) {
  if (!el) return false;
  const tag = el.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || (el as HTMLElement).isContentEditable;
}

export function MallangRoom({ theme = PIXEL_THEME, lit = false, me, onOpen }: MallangRoomProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const roomRef = useRef<HTMLDivElement>(null);
  const meRef = useRef<HTMLDivElement>(null);
  const posRef = useRef<Pct>(theme.meStart);        // 진짜 위치(키보드 이동 중엔 DOM에 직접 쓴다)
  const [mePos, setMePos] = useState<Pct>(theme.meStart);
  const [facingLeft, setFacingLeft] = useState(false);
  const [hopping, setHopping] = useState(false);    // 탭 이동 중
  const [walking, setWalking] = useState(false);    // 키보드 이동 중
  const [pendingId, setPendingId] = useState<Hotspot["id"] | null>(null);
  const [snapWidth, setSnapWidth] = useState<number | null>(null);
  const hopTimer = useRef<number | null>(null);
  const lastOpened = useRef<Hotspot["id"] | null>(null);
  const onOpenRef = useRef(onOpen);
  onOpenRef.current = onOpen;
  const themeRef = useRef(theme);
  themeRef.current = theme;

  // 테마가 바뀌면 시작 위치로
  useEffect(() => {
    posRef.current = theme.meStart;
    setMePos(theme.meStart);
    lastOpened.current = null;
  }, [theme]);

  // 픽셀 테마: 방 폭을 원본의 정수배로 스냅
  useEffect(() => {
    const host = hostRef.current;
    if (!host || !theme.pixelArt || !theme.nativeWidth) { setSnapWidth(null); return; }
    const nat = theme.nativeWidth;
    const update = () => setSnapWidth(Math.max(2, Math.floor(Math.min(host.clientWidth, 960) / nat)) * nat);   // max-width(960)와 정합
    update();
    const ro = new ResizeObserver(update);
    ro.observe(host);
    return () => ro.disconnect();
  }, [theme]);

  const open = useCallback((h: Hotspot) => {
    lastOpened.current = h.id;
    onOpenRef.current(h);
  }, []);

  // ---- 탭 이동(hop): CSS transition 으로 left/top 을 옮기고, 끝나면 도착 처리
  const hopTo = useCallback((target: Pct, h: Hotspot | null) => {
    if (hopTimer.current) window.clearTimeout(hopTimer.current);
    setFacingLeft(target.x < posRef.current.x);
    posRef.current = target;
    setMePos(target);
    setPendingId(h?.id ?? null);
    setHopping(true);
    hopTimer.current = window.setTimeout(() => {
      setHopping(false);
      setPendingId(null);
      if (h) open(h);
      else lastOpened.current = null;
    }, HOP_MS);
  }, [open]);

  useEffect(() => () => { if (hopTimer.current) window.clearTimeout(hopTimer.current); }, []);

  // ---- 바닥 탭: 버튼(핫스팟·라벨) 위가 아니고 서 있을 수 있는 자리면 그곳으로
  const onRoomPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if ((e.target as HTMLElement).closest("button")) return;
    const rect = roomRef.current?.getBoundingClientRect();
    if (!rect) return;
    const p = { x: ((e.clientX - rect.left) / rect.width) * 100, y: ((e.clientY - rect.top) / rect.height) * 100 };
    if (!canStand(theme, p)) return;
    roomRef.current?.focus({ preventScroll: true });
    hopTo(p, null);
  };

  // ---- 키보드 걷기: rAF 루프가 posRef 와 DOM 을 직접 갱신하고, 멈출 때 state 로 동기화
  useEffect(() => {
    const keys = new Set<string>();
    let raf = 0;
    let last = 0;

    const step = (now: number) => {
      const t = themeRef.current;
      const dt = Math.min(0.05, (now - last) / 1000);
      last = now;
      let dx = 0;
      let dy = 0;
      for (const k of keys) {
        const d = KEY_DIR[k];
        if (d) { dx += d.x; dy += d.y; }
      }
      dx = Math.sign(dx);
      dy = Math.sign(dy);
      if (dx !== 0 || dy !== 0) {
        const p = posRef.current;
        // 축 분리 충돌 — 가구에 비스듬히 부딛혀도 미끄러진다
        const nx = { x: p.x + dx * WALK_SPEED_X * dt, y: p.y };
        const after1 = canStand(t, nx) ? nx : p;
        const ny = { x: after1.x, y: after1.y + dy * WALK_SPEED_X * t.aspect * dt };
        const next = canStand(t, ny) ? ny : after1;
        posRef.current = next;
        const el = meRef.current;
        if (el) {
          el.style.left = `${next.x}%`;
          el.style.top = `${next.y}%`;
          el.style.zIndex = String(Math.round(next.y * 10));
        }
        if (dx !== 0) setFacingLeft(dx < 0);
        if (lastOpened.current && !hotspotNear(t, next)) lastOpened.current = null;
      }
      raf = requestAnimationFrame(step);
    };

    const start = () => {
      if (raf) return;
      if (hopTimer.current) { window.clearTimeout(hopTimer.current); hopTimer.current = null; setHopping(false); setPendingId(null); }
      setWalking(true);
      last = performance.now();
      raf = requestAnimationFrame(step);
    };
    const stop = () => {
      if (!raf) return;
      cancelAnimationFrame(raf);
      raf = 0;
      setWalking(false);
      setMePos(posRef.current);
      const near = hotspotNear(themeRef.current, posRef.current);
      if (near && lastOpened.current !== near.id) open(near);
    };

    const onKeyDown = (e: KeyboardEvent) => {
      if (!KEY_DIR[e.key] || isTypingTarget(document.activeElement)) return;
      e.preventDefault();
      keys.add(e.key);
      start();
    };
    const onKeyUp = (e: KeyboardEvent) => {
      if (!keys.delete(e.key)) return;
      if (keys.size === 0) stop();
    };
    const onBlur = () => { keys.clear(); stop(); };

    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);
    window.addEventListener("blur", onBlur);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("keyup", onKeyUp);
      window.removeEventListener("blur", onBlur);
      if (raf) cancelAnimationFrame(raf);
    };
  }, [open]);

  const meSrc = me?.src ?? theme.sprites.me;
  const meName = me?.name ?? "나";
  const moving = hopping || walking;
  const footStyle = (p: Pct): React.CSSProperties => ({
    left: `${p.x}%`, top: `${p.y}%`, width: `max(${theme.spriteWPct}%, ${theme.pixelArt ? 32 : 46}px)`, zIndex: Math.round(p.y * 10),
  });

  return (
    <div ref={hostRef} className={s.host}>
      <div
        ref={roomRef}
        className={`${s.room} ${theme.pixelArt ? s.pixel : ""}`}
        style={{ aspectRatio: `${theme.aspect}`, width: snapWidth ? `${snapWidth}px` : undefined }}
        tabIndex={0}
        role="application"
        aria-label="내 방. 방향키로 이동, 가구를 눌러 열기"
        onPointerDown={onRoomPointerDown}
      >
        {/* 배경 */}
        {theme.bgSrc ? (
          <img className={s.bg} src={theme.bgSrc} alt="" draggable={false} />
        ) : (
          <div className={s.fallback} aria-hidden>
            <div className={s.wall} style={{ height: `${theme.wallPct}%` }} />
            <div className={s.baseboard} style={{ top: `${theme.wallPct}%` }} />
            <div className={s.floor} style={{ top: `${theme.wallPct}%` }} />
            {theme.decor.map((d, i) => <div key={i} className={`${s.decor} ${s[d.kind] ?? ""}`} style={boxStyle(d.box)} />)}
            {theme.hotspots.map((h) => <div key={h.id} className={`${s.decor} ${s[`f_${h.id}`] ?? ""}`} style={boxStyle(h.box)} />)}
            <span className={s.placeholderNote}>배경 그림 자리 · public/room/bg.jpg (docs/brand/room-art-prompt.md)</span>
          </div>
        )}

        {/* D-day 신호: 책상 점등 */}
        {lit && <div className={s.glow} style={boxStyle(theme.glowBox)} />}

        {/* 가구 핫스팟(탭 영역) */}
        {theme.hotspots.map((h) => (
          <button key={h.id} type="button" className={s.hotspot} style={boxStyle(h.box)} aria-label={`${h.label} 열기`} onClick={() => hopTo(h.stand, h)} />
        ))}

        {/* 가구 라벨 */}
        {theme.hotspots.map((h) => {
          const isLit = lit && h.id === "tracker";
          const cx = h.box.x + h.box.w / 2;
          const align = cx < 15 ? "left" : cx > 85 ? "right" : "center";
          const style: React.CSSProperties = {
            top: h.labelAt === "top" ? `${h.box.y}%` : `${h.box.y + h.box.h}%`,
            left: align === "left" ? `${h.box.x}%` : align === "right" ? undefined : `${cx}%`,
            right: align === "right" ? `${100 - (h.box.x + h.box.w)}%` : undefined,
            transform: `translate(${align === "center" ? "-50%" : "0"}, ${h.labelAt === "top" ? "-100%" : "0"})`,
          };
          return (
            <button
              key={`label-${h.id}`}
              type="button"
              className={[s.label, isLit ? s.labelLit : "", pendingId === h.id ? s.labelActive : "", h.status === "soon" ? s.labelSoon : ""].join(" ")}
              style={style}
              onClick={() => hopTo(h.stand, h)}
            >
              <span className={s.labelEmoji}>{h.emoji}</span>
              <span className={s.labelText}>{h.label}{isLit ? " · D-1" : ""}{h.status === "soon" ? " (준비 중)" : ""}</span>
            </button>
          );
        })}

        {/* NPC */}
        {theme.npcs.map((n) => (
          <div key={n.id} className={s.sprite} style={footStyle(n.pos)} title={`${n.name} · ${n.role}`}>
            {n.bubble && (
              <div className={s.bubble}>
                <b>{n.name}</b> {n.bubble}
              </div>
            )}
            <span className={s.flip} style={{ transform: n.flip ? "scaleX(-1)" : undefined }}>
              <img className={`${s.mallang} ${s.idle}`} src={theme.sprites[n.id]} alt={`${n.name} (${n.role})`} draggable={false} style={{ animationDelay: `${(n.pos.x % 7) * 0.3}s` }} />
            </span>
            <div className={s.shadow} />
            <span className={s.nameTag}>{n.name}<small className={s.role}>{n.role}</small></span>
          </div>
        ))}

        {/* 미니미 */}
        <div ref={meRef} className={`${s.sprite} ${s.me}`} style={{ ...footStyle(mePos), transitionDuration: walking ? "0ms" : `${HOP_MS}ms` }}>
          <span className={s.flip} style={{ transform: facingLeft ? "scaleX(-1)" : undefined }}>
            <img className={`${s.mallang} ${moving ? s.hop : s.idle}`} src={meSrc} alt={meName} draggable={false} style={{ animationDuration: moving ? `${HOP_MS / 2}ms` : undefined }} />
          </span>
          <div className={`${s.shadow} ${moving ? s.shadowHop : ""}`} style={{ animationDuration: moving ? `${HOP_MS / 2}ms` : undefined }} />
          <span className={`${s.nameTag} ${s.meTag}`}>{meName}</span>
        </div>
      </div>
    </div>
  );
}
