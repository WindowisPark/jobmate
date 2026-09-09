// 방 레이아웃 — 테마 데이터.
// 모든 좌표는 방 컨테이너 기준 퍼센트(0~100). 배경 이미지와 핫스팟이 같은 좌표계를 공유한다.
//
// 두 테마:
//   PIXEL_THEME   — Kenney 16px 타일로 미리 렌더한 방(public/room/pixel/bg.png, 11×8 타일) + 픽셀 슬라임. 정수 배율로 표시.
//   MALLANG_THEME — saju 말랑이 일러스트 방(배경 그림 드롭인, 없으면 CSS 폴백). 보관용.

export type HotspotId = "tracker" | "documents" | "jobs" | "mental" | "rest";
export type RoomAgentId = "seo_yeon" | "jun_ho" | "ha_eun" | "min_su";

export interface Pct { x: number; y: number }
export interface Box { x: number; y: number; w: number; h: number }

export interface Hotspot {
  id: HotspotId;
  emoji: string;
  label: string;
  box: Box;                 // 탭 영역(+ 말랑이 테마의 폴백 가구 실루엣)
  stand: Pct;               // 미니미가 도착해 서는 곳(발 위치)
  status: "ready" | "soon";
  labelAt: "top" | "bottom";
  solid?: Box;              // 걸어서 지나갈 수 없는 영역. 없으면 통과 가능(벽걸이 등)
}

// 방 안 표기명은 전문성이 이름에 보이게: 첨삭이(seo_yeon 커리어 코치) · 탐색이(jun_ho 리서처) · 토닥이(ha_eun 멘탈) · 꿀팁이(min_su 멘토)
export interface RoomNpc {
  id: RoomAgentId;
  name: string;             // 방 안 표기명
  role: string;
  pos: Pct;                 // 발 위치
  bubble?: string;
  flip?: boolean;
}

export type DecorKind = "window" | "plant" | "rug" | "chair" | "picture";
export interface Decor { kind: DecorKind; box: Box }

export interface RoomTheme {
  id: "pixel" | "mallang";
  aspect: number;                       // 가로/세로
  wallPct: number;                      // 뒷벽 높이(%)
  spriteWPct: number;                   // 스프라이트 폭(방 폭 %)
  /** 픽셀아트: image-rendering: pixelated + 방 폭을 nativeWidth 의 정수배로 스냅 */
  pixelArt: boolean;
  nativeWidth?: number;
  bgSrc?: string;                       // 없으면 CSS 폴백(말랑이 테마)
  hotspots: readonly Hotspot[];
  solids: readonly Box[];               // 핫스팟 외 장애물(티테이블·식물 등)
  npcs: readonly RoomNpc[];
  meStart: Pct;
  floorBounds: { minX: number; maxX: number; minY: number; maxY: number };
  arriveRadius: { x: number; y: number };
  sprites: Record<RoomAgentId | "me", string>;
  glowBox: Box;                         // D-day 신호 글로우(책상)
  decor: readonly Decor[];              // CSS 폴백 장식(말랑이 테마)
}

/** 탭 → 도착까지 이동 시간(ms). CSS transition 과 hop 애니메이션 길이가 이 값을 따른다. */
export const HOP_MS = 720;
/** 키보드 이동 속도(%/s, 가로). 세로는 aspect 배로 맞춰 화면상 같은 속도. */
export const WALK_SPEED_X = 26;

// =====================================================================================
// PIXEL — 11×8 타일 = 176×128px. 타일 (c,r) → x% = c/11·100, y% = r/8·100
// =====================================================================================
const TX = (c: number) => (c / 11) * 100;
const TY = (r: number) => (r / 8) * 100;
const tbox = (c: number, r: number, w: number, h: number): Box => ({ x: TX(c), y: TY(r), w: TX(w), h: TY(h) });
const tpt = (c: number, r: number): Pct => ({ x: TX(c), y: TY(r) });

const PIXEL_HOTSPOTS: readonly Hotspot[] = [
  { id: "documents", emoji: "📚", label: "이력서·자소서", box: tbox(0, 2, 2, 1), stand: tpt(0.5, 3.6), status: "ready", labelAt: "bottom", solid: tbox(0, 2, 2, 1) },
  { id: "tracker", emoji: "📝", label: "지원 대시보드", box: tbox(2, 2, 2, 3), stand: tpt(2.5, 4.6), status: "ready", labelAt: "top", solid: tbox(2, 2, 2, 2) },
  { id: "jobs", emoji: "📮", label: "공고 게시판", box: tbox(7, 0, 2, 2), stand: tpt(7.5, 2.6), status: "ready", labelAt: "bottom" },
  { id: "rest", emoji: "💤", label: "루틴·휴식", box: tbox(10, 2, 1, 2), stand: tpt(9.5, 3.6), status: "soon", labelAt: "top", solid: tbox(10, 2, 1, 2) },
  { id: "mental", emoji: "🌿", label: "토닥이와 쉬기", box: tbox(8, 5, 2, 2), stand: tpt(7.5, 6.6), status: "ready", labelAt: "bottom", solid: tbox(8, 5, 2, 2) },   // 소파 왼쪽 — 걸어와 부딛히는 자리
];

export const PIXEL_THEME: RoomTheme = {
  id: "pixel",
  aspect: 11 / 8,
  wallPct: TY(2),
  spriteWPct: TX(1),
  pixelArt: true,
  nativeWidth: 176,
  bgSrc: "/room/pixel/bg.png",
  hotspots: PIXEL_HOTSPOTS,
  solids: [tbox(6, 2, 1, 2), tbox(0, 7, 1, 1), tbox(10, 7, 1, 1)],   // 티테이블, 식물 2
  npcs: [
    { id: "jun_ho", name: "탐색이", role: "취업 리서처", pos: tpt(5.5, 3.5), bubble: "카카오 서류 마감 내일이야!" },
    { id: "ha_eun", name: "토닥이", role: "멘탈 케어", pos: tpt(8.5, 5.4), bubble: "잠깐 숨 고르고 가자 🌿" },
    { id: "min_su", name: "꿀팁이", role: "현직자 멘토", pos: tpt(6.5, 7.5), flip: true },
  ],
  meStart: tpt(5.5, 5.6),
  floorBounds: { minX: 3, maxX: 97, minY: TY(2) + 3, maxY: 98 },
  arriveRadius: { x: 7, y: 9 },
  sprites: {
    me: "/room/pixel/blob_me.png",
    seo_yeon: "/room/pixel/blob_seo_yeon.png",
    jun_ho: "/room/pixel/blob_jun_ho.png",
    ha_eun: "/room/pixel/blob_ha_eun.png",
    min_su: "/room/pixel/blob_min_su.png",
  },
  glowBox: tbox(1.4, 2.4, 3.2, 2.6),
  decor: [],
};

/** Kenney Tiny Dungeon 슬라임(색상 회전) 버전 — 비교용 */
export const PIXEL_THEME_KENNEY: RoomTheme = {
  ...PIXEL_THEME,
  sprites: {
    me: "/room/pixel/slime_me.png",
    seo_yeon: "/room/pixel/slime_seo_yeon.png",
    jun_ho: "/room/pixel/slime_jun_ho.png",
    ha_eun: "/room/pixel/slime_ha_eun.png",
    min_su: "/room/pixel/slime_min_su.png",
  },
};

// =====================================================================================
// MALLANG — saju 말랑이 일러스트 방 (보관)
// =====================================================================================
export const MALLANG_SRC: Record<RoomAgentId | "egg", string> = {
  seo_yeon: "/room/mallang/seo_yeon.png",
  jun_ho: "/room/mallang/jun_ho.png",
  ha_eun: "/room/mallang/ha_eun.png",
  min_su: "/room/mallang/min_su.png",
  egg: "/room/mallang/egg.png",
};

export const MALLANG_THEME: RoomTheme = {
  id: "mallang",
  aspect: 3 / 2,
  wallPct: 34,
  spriteWPct: 11,
  pixelArt: false,
  hotspots: [
    { id: "documents", emoji: "📚", label: "이력서·자소서", box: { x: 4, y: 8, w: 12, h: 44 }, stand: { x: 10, y: 60 }, status: "ready", labelAt: "bottom", solid: { x: 4, y: 8, w: 12, h: 44 } },
    { id: "tracker", emoji: "📝", label: "지원 대시보드", box: { x: 20, y: 38, w: 18, h: 22 }, stand: { x: 29, y: 66 }, status: "ready", labelAt: "top", solid: { x: 20, y: 38, w: 18, h: 22 } },
    { id: "jobs", emoji: "📮", label: "공고 게시판", box: { x: 60, y: 8, w: 20, h: 22 }, stand: { x: 70, y: 46 }, status: "ready", labelAt: "bottom" },
    { id: "rest", emoji: "💤", label: "루틴·휴식", box: { x: 80, y: 38, w: 18, h: 26 }, stand: { x: 74, y: 62 }, status: "soon", labelAt: "top", solid: { x: 80, y: 38, w: 18, h: 26 } },
    { id: "mental", emoji: "🌿", label: "토닥이와 쉬기", box: { x: 58, y: 66, w: 22, h: 20 }, stand: { x: 52, y: 84 }, status: "ready", labelAt: "bottom", solid: { x: 58, y: 66, w: 22, h: 20 } },
  ],
  solids: [],
  npcs: [
    { id: "jun_ho", name: "탐색이", role: "취업 리서처", pos: { x: 48, y: 58 }, bubble: "카카오 서류 마감 내일이야!" },
    { id: "ha_eun", name: "토닥이", role: "멘탈 케어", pos: { x: 69, y: 76 }, bubble: "잠깐 숨 고르고 가자 🌿" },
    { id: "min_su", name: "꿀팁이", role: "현직자 멘토", pos: { x: 88, y: 89 }, flip: true },
  ],
  meStart: { x: 40, y: 88 },
  floorBounds: { minX: 5, maxX: 95, minY: 44, maxY: 97 },
  arriveRadius: { x: 7, y: 9 },
  sprites: { me: MALLANG_SRC.egg, seo_yeon: MALLANG_SRC.seo_yeon, jun_ho: MALLANG_SRC.jun_ho, ha_eun: MALLANG_SRC.ha_eun, min_su: MALLANG_SRC.min_su },
  glowBox: { x: 16, y: 44, w: 26, h: 30 },
  decor: [
    { kind: "window", box: { x: 40, y: 6, w: 16, h: 24 } },
    { kind: "picture", box: { x: 22, y: 12, w: 8, h: 10 } },
    { kind: "rug", box: { x: 28, y: 70, w: 30, h: 24 } },
    { kind: "chair", box: { x: 25, y: 60, w: 8, h: 8 } },
    { kind: "plant", box: { x: 88, y: 16, w: 8, h: 20 } },
    { kind: "plant", box: { x: 2, y: 78, w: 8, h: 18 } },
  ],
};

// =====================================================================================
const inBox = (p: Pct, b: Box) => p.x >= b.x && p.x <= b.x + b.w && p.y >= b.y && p.y <= b.y + b.h;

/** 미니미 발이 놓일 수 있는 자리인지 */
export function canStand(theme: RoomTheme, p: Pct): boolean {
  const f = theme.floorBounds;
  if (p.x < f.minX || p.x > f.maxX || p.y < f.minY || p.y > f.maxY) return false;
  if (theme.solids.some((b) => inBox(p, b))) return false;
  return !theme.hotspots.some((h) => h.solid && inBox(p, h.solid));
}

/** 발 위치가 어느 가구 앞(stand)인지 */
export function hotspotNear(theme: RoomTheme, p: Pct): Hotspot | null {
  const r = theme.arriveRadius;
  return theme.hotspots.find((h) => Math.abs(p.x - h.stand.x) <= r.x && Math.abs(p.y - h.stand.y) <= r.y) ?? null;
}
