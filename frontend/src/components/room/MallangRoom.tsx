// 내 방 — DOM/CSS 렌더러 (테마: 픽셀 / 말랑이).
// 배경 이미지 1장(없으면 CSS 폴백) + 가구 핫스팟 + 캐릭터 PNG 스프라이트 + 말풍선.
// 이동: 가구/친구 탭(그 앞으로 hop) · 바닥 탭(거기로 hop) · 방향키/WASD(걷기, 가구에 막힘).
// 도착하면 바로 열지 않고 '확인' 간판이 뜬다 — 다시 탭하거나 Enter/Space 로 열기. 방을 떠나는 동작(채팅)이 특히 그렇다.
// 픽셀 테마는 방 폭을 원본(176px)의 정수배로 스냅하고 image-rendering: pixelated 로 그린다.

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import s from "./MallangRoom.module.css";
import {
  HOP_MS, PIXEL_THEME, WALK_SPEED_X,
  canStand, targetKey, targetLabel, targetNear,
  type Box, type Hotspot, type OpenTarget, type Pct,
  type RoomAgentId, type RoomBubble, type RoomNpc, type RoomTheme,
} from "./roomLayout";

export interface MallangRoomProps {
  theme?: RoomTheme;
  /** 지원 마감 임박(D-day≤3) 신호 → 책상 점등 */
  lit?: boolean;
  /** 점등 라벨에 붙일 짧은 배지 (예: 'D-2') */
  litLabel?: string;
  /** 미니미 그림·이름. 없으면 테마 기본 */
  me?: { src?: string; name?: string };
  /** 서버가 준 NPC 선제 대사. 주면 테마의 예시 문구 대신 이걸 띄운다 */
  bubbles?: readonly RoomBubble[];
  /** 말풍선을 눌렀을 때 — 그 친구와의 대화로 넘어간다 */
  onBubbleAccept?: (bubble: RoomBubble) => void;
  /** 말풍선을 닫았을 때 */
  onBubbleDismiss?: (bubble: RoomBubble) => void;
  /** 확인 단계를 거쳐 열기로 결정됐을 때 */
  onOpen: (target: OpenTarget) => void;
}

const boxStyle = (b: Box): React.CSSProperties => ({ left: `${b.x}%`, top: `${b.y}%`, width: `${b.w}%`, height: `${b.h}%` });

const KEY_DIR: Record<string, Pct> = {
  ArrowLeft: { x: -1, y: 0 }, a: { x: -1, y: 0 }, A: { x: -1, y: 0 },
  ArrowRight: { x: 1, y: 0 }, d: { x: 1, y: 0 }, D: { x: 1, y: 0 },
  ArrowUp: { x: 0, y: -1 }, w: { x: 0, y: -1 }, W: { x: 0, y: -1 },
  ArrowDown: { x: 0, y: 1 }, s: { x: 0, y: 1 }, S: { x: 0, y: 1 },
};
const CONFIRM_KEYS = new Set(["Enter", " "]);

function isTypingTarget(el: Element | null) {
  if (!el) return false;
  const tag = el.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || (el as HTMLElement).isContentEditable;
}

export function MallangRoom({
  theme = PIXEL_THEME, lit = false, litLabel, me, bubbles, onBubbleAccept, onBubbleDismiss, onOpen,
}: MallangRoomProps) {
  // 서버 말풍선을 에이전트별로 하나씩. 우선순위는 서버가 이미 정렬해 보낸다.
  const bubbleByAgent = useMemo(() => {
    const m = new Map<RoomAgentId, RoomBubble>();
    for (const b of bubbles ?? []) if (!m.has(b.agentId)) m.set(b.agentId, b);
    return m;
  }, [bubbles]);
  const topBubbleId = bubbles?.[0]?.id;

  const hostRef = useRef<HTMLDivElement>(null);
  const roomRef = useRef<HTMLDivElement>(null);
  const meRef = useRef<HTMLDivElement>(null);
  const posRef = useRef<Pct>(theme.meStart);
  const [mePos, setMePos] = useState<Pct>(theme.meStart);
  const [facingLeft, setFacingLeft] = useState(false);
  const [hopping, setHopping] = useState(false);
  const [walking, setWalking] = useState(false);
  const [pendingKey, setPendingKey] = useState<string | null>(null);   // 이동 중인 목표(라벨 강조)
  const [ready, setReady] = useState<OpenTarget | null>(null);         // 도착해서 확인 대기 중인 대상
  const [snapWidth, setSnapWidth] = useState<number | null>(null);
  const hopTimer = useRef<number | null>(null);
  const readyRef = useRef<OpenTarget | null>(null);
  const dismissedKey = useRef<string | null>(null);   // 열고 난 뒤, 그 자리를 떠나기 전까진 다시 묻지 않는다
  const onOpenRef = useRef(onOpen);
  onOpenRef.current = onOpen;
  const themeRef = useRef(theme);
  themeRef.current = theme;

  const setReadyBoth = (t: OpenTarget | null) => { readyRef.current = t; setReady(t); };

  useEffect(() => {
    posRef.current = theme.meStart;
    setMePos(theme.meStart);
    setReadyBoth(null);
    dismissedKey.current = null;
  }, [theme]);

  // 픽셀 테마: 방 폭을 원본의 정수배로 스냅
  useEffect(() => {
    const host = hostRef.current;
    if (!host || !theme.pixelArt || !theme.nativeWidth) { setSnapWidth(null); return; }
    const nat = theme.nativeWidth;
    const update = () => setSnapWidth(Math.max(2, Math.floor(Math.min(host.clientWidth, 960) / nat)) * nat);
    update();
    const ro = new ResizeObserver(update);
    ro.observe(host);
    return () => ro.disconnect();
  }, [theme]);

  const open = useCallback((t: OpenTarget) => {
    dismissedKey.current = targetKey(t);
    setReadyBoth(null);
    onOpenRef.current(t);
  }, []);

  /** 도착 처리 — 확인 대기로 전환(같은 자리에서 방금 열었다면 다시 묻지 않음) */
  const arrive = useCallback((p: Pct) => {
    const t = targetNear(themeRef.current, p);
    const key = targetKey(t);
    if (!t || key === dismissedKey.current) { setReadyBoth(null); return; }
    setReadyBoth(t);
  }, []);

  // ---- 탭 이동(hop)
  const hopTo = useCallback((target: Pct, intent: OpenTarget | null) => {
    if (hopTimer.current) window.clearTimeout(hopTimer.current);
    // 이미 그 대상 앞에서 확인 대기 중이면 두 번째 탭 = 열기
    if (intent && readyRef.current && targetKey(readyRef.current) === targetKey(intent)) { open(intent); return; }
    setReadyBoth(null);
    dismissedKey.current = null;
    setFacingLeft(target.x < posRef.current.x);
    posRef.current = target;
    setMePos(target);
    setPendingKey(targetKey(intent));
    setHopping(true);
    hopTimer.current = window.setTimeout(() => {
      setHopping(false);
      setPendingKey(null);
      if (intent) setReadyBoth(intent);
      else arrive(target);
    }, HOP_MS);
  }, [open, arrive]);

  useEffect(() => () => { if (hopTimer.current) window.clearTimeout(hopTimer.current); }, []);

  // ---- 바닥 탭
  const onRoomPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if ((e.target as HTMLElement).closest("button")) return;
    const rect = roomRef.current?.getBoundingClientRect();
    if (!rect) return;
    const p = { x: ((e.clientX - rect.left) / rect.width) * 100, y: ((e.clientY - rect.top) / rect.height) * 100 };
    if (!canStand(theme, p)) return;
    roomRef.current?.focus({ preventScroll: true });
    hopTo(p, null);
  };

  // ---- 키보드: 걷기 + Enter/Space 확인
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
        // 대상 앞을 떠나면 확인 간판을 내리고, 다시 물을 수 있게 한다
        const nearNow = targetKey(targetNear(t, next));
        if (readyRef.current && nearNow !== targetKey(readyRef.current)) setReadyBoth(null);
        if (dismissedKey.current && nearNow !== dismissedKey.current) dismissedKey.current = null;
      }
      raf = requestAnimationFrame(step);
    };

    const start = () => {
      if (raf) return;
      if (hopTimer.current) { window.clearTimeout(hopTimer.current); hopTimer.current = null; setHopping(false); setPendingKey(null); }
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
      arrive(posRef.current);
    };

    const onKeyDown = (e: KeyboardEvent) => {
      if (isTypingTarget(document.activeElement)) return;
      if (CONFIRM_KEYS.has(e.key)) {
        if (readyRef.current) { e.preventDefault(); open(readyRef.current); }
        return;
      }
      if (!KEY_DIR[e.key]) return;
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
  }, [open, arrive]);

  const meSrc = me?.src ?? theme.sprites.me;
  const meName = me?.name ?? "나";
  const moving = hopping || walking;
  const footStyle = (p: Pct): React.CSSProperties => ({
    left: `${p.x}%`, top: `${p.y}%`, width: `max(${theme.spriteWPct}%, ${theme.pixelArt ? 32 : 46}px)`, zIndex: Math.round(p.y * 10),
  });
  const hotspotIntent = (h: Hotspot): OpenTarget => ({ kind: "hotspot", hotspot: h });
  const npcIntent = (n: RoomNpc): OpenTarget => ({ kind: "npc", agentId: n.id, npc: n });

  // 확인 간판 위치: 대상 위쪽
  const readyAnchor: Pct | null = ready
    ? ready.kind === "hotspot"
      ? { x: ready.hotspot.box.x + ready.hotspot.box.w / 2, y: ready.hotspot.box.y }
      : { x: ready.npc.pos.x, y: ready.npc.pos.y - theme.spriteWPct * theme.aspect * 1.4 }
    : null;

  return (
    <div ref={hostRef} className={s.host}>
      <div
        ref={roomRef}
        className={`${s.room} ${theme.pixelArt ? s.pixel : ""}`}
        style={{ aspectRatio: `${theme.aspect}`, width: snapWidth ? `${snapWidth}px` : undefined }}
        tabIndex={0}
        role="application"
        aria-label="내 방. 방향키로 이동, 가구나 친구 앞에서 Enter 로 열기"
        onPointerDown={onRoomPointerDown}
      >
        {theme.bgSrc ? (
          <img className={s.bg} src={theme.bgSrc} alt="" draggable={false} />
        ) : (
          <div className={s.fallback} aria-hidden>
            <div className={s.wall} style={{ height: `${theme.wallPct}%` }} />
            <div className={s.baseboard} style={{ top: `${theme.wallPct}%` }} />
            <div className={s.floor} style={{ top: `${theme.wallPct}%` }} />
            {theme.decor.map((d, i) => <div key={i} className={`${s.decor} ${s[d.kind] ?? ""}`} style={boxStyle(d.box)} />)}
            {theme.hotspots.map((h) => <div key={h.id} className={`${s.decor} ${s[`f_${h.id}`] ?? ""}`} style={boxStyle(h.box)} />)}
          </div>
        )}

        {lit && <div className={s.glow} style={boxStyle(theme.glowBox)} />}

        {/* 가구 핫스팟(탭 영역) */}
        {theme.hotspots.map((h) => (
          <button key={h.id} type="button" className={s.hotspot} style={boxStyle(h.box)} aria-label={`${h.label} ${h.verb}`} onClick={() => hopTo(h.stand, hotspotIntent(h))} />
        ))}

        {/* 가구 간판 */}
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
          const key = `h:${h.id}`;
          return (
            <button
              key={`label-${h.id}`}
              type="button"
              className={[s.label, isLit ? s.labelLit : "", pendingKey === key ? s.labelActive : "", h.status === "soon" ? s.labelSoon : ""].join(" ")}
              style={style}
              onClick={() => hopTo(h.stand, hotspotIntent(h))}
            >
              {h.label}{isLit && litLabel ? ` · ${litLabel}` : ""}{h.status === "soon" ? " (준비 중)" : ""}
            </button>
          );
        })}

        {/* 친구(NPC) — 탭하면 곁으로 가서 대화 확인 */}
        {theme.npcs.map((n) => {
          const live = bubbleByAgent.get(n.id);
          const text = live?.text ?? (bubbles ? undefined : n.bubble);
          // 좁은 화면에서는 우선순위가 가장 높은 하나만 — 겹치면 방이 시끄럽다
          const secondary = live ? live.id !== topBubbleId : false;
          // 방 가장자리에 선 친구의 말풍선은 밖으로 새지 않게 붙여 세운다
          const edge = n.pos.x > 68 ? s.bubbleRight : n.pos.x < 32 ? s.bubbleLeft : "";
          return (
          <div key={n.id} className={`${s.sprite} ${s.npc}`} style={footStyle(n.pos)} title={`${n.name} · ${n.role}`}>
            {text && (
              <div className={`${s.bubble} ${live ? s.bubbleLive : ""} ${edge} ${secondary ? s.bubbleSecondary : ""}`}>
                {live ? (
                  <>
                    <button
                      type="button"
                      className={s.bubbleBody}
                      onClick={() => onBubbleAccept?.(live)}
                    >
                      <b>{n.name}</b> {text}
                    </button>
                    <button
                      type="button"
                      className={s.bubbleClose}
                      aria-label="말풍선 닫기"
                      onClick={() => onBubbleDismiss?.(live)}
                    >
                      ✕
                    </button>
                  </>
                ) : (
                  <><b>{n.name}</b> {text}</>
                )}
              </div>
            )}
            <button type="button" className={s.npcHit} aria-label={`${n.name}와 이야기하기`} onClick={() => hopTo(n.stand, npcIntent(n))}>
              <span className={s.flip} style={{ transform: n.flip ? "scaleX(-1)" : undefined }}>
                <img className={`${s.mallang} ${s.idle}`} src={theme.sprites[n.id]} alt="" draggable={false} style={{ animationDelay: `${(n.pos.x % 7) * 0.3}s` }} />
              </span>
            </button>
            <div className={s.shadow} />
            <span className={s.nameTag}>{n.name}<small className={s.role}>{n.role}</small></span>
          </div>
          );
        })}

        {/* 미니미 */}
        <div ref={meRef} className={`${s.sprite} ${s.me}`} style={{ ...footStyle(mePos), transitionDuration: walking ? "0ms" : `${HOP_MS}ms` }}>
          <span className={s.flip} style={{ transform: facingLeft ? "scaleX(-1)" : undefined }}>
            <img className={`${s.mallang} ${moving ? s.hop : s.idle}`} src={meSrc} alt={meName} draggable={false} style={{ animationDuration: moving ? `${HOP_MS / 2}ms` : undefined }} />
          </span>
          <div className={`${s.shadow} ${moving ? s.shadowHop : ""}`} style={{ animationDuration: moving ? `${HOP_MS / 2}ms` : undefined }} />
          <span className={`${s.nameTag} ${s.meTag}`}>{meName}</span>
        </div>

        {/* 확인 간판 — 도착 후 한 번 더 */}
        {ready && readyAnchor && (
          <div className={s.confirm} style={{ left: `${Math.max(12, Math.min(88, readyAnchor.x))}%`, top: `${readyAnchor.y}%` }} role="dialog" aria-live="polite">
            <button type="button" className={s.confirmBtn} onClick={() => open(ready)} autoFocus>
              {targetLabel(ready)} <span className={s.confirmKey}>Enter</span>
            </button>
            <button type="button" className={s.confirmCancel} onClick={() => { dismissedKey.current = targetKey(ready); setReadyBoth(null); }} aria-label="아니오">
              ✕
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
