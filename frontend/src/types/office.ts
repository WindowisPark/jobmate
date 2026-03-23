import type { AgentId } from "./agent";

// 타일 타입
export type TileType =
  | "floor"
  | "wall"
  | "door"
  | "window"
  | "desk_seo_yeon"
  | "desk_jun_ho"
  | "desk_ha_eun"
  | "desk_min_su"
  | "chair_seo_yeon"
  | "chair_jun_ho"
  | "chair_ha_eun"
  | "chair_min_su"
  | "sofa"
  | "plant"
  | "whiteboard"
  | "bookshelf"
  | "coffee_machine"
  | "rug";

// 에이전트 행동 상태
export type AgentBehavior =
  | "wandering"     // 랜덤 돌아다님
  | "walking_to_desk" // 책상으로 이동 중
  | "sitting_down"  // 앉는 중
  | "typing"        // 타이핑 중 (응답 생성)
  | "standing_up"   // 일어나는 중
  | "idle_at_spot"  // 한 곳에서 잠시 멈춤
  | "drinking"      // 커피머신 근처
  | "chatting";     // 소파 근처에서 잡담

export interface AgentOfficeFull {
  id: AgentId;
  x: number;          // 픽셀 좌표
  y: number;
  targetX: number;    // 이동 목표
  targetY: number;
  behavior: AgentBehavior;
  direction: "left" | "right" | "up" | "down";
  frameIndex: number; // 애니메이션 프레임
  deskTile: { col: number; row: number };  // 본인 책상 위치
  chairTile: { col: number; row: number }; // 본인 의자 위치
}

// 12x8 오피스 타일맵
export const TILE_SIZE = 40;
export const OFFICE_COLS = 14;
export const OFFICE_ROWS = 9;

// W=wall, F=floor, D=door, N=window, R=rug
// 1~4=desk, 5~8=chair (seo_yeon, jun_ho, ha_eun, min_su)
// S=sofa, P=plant, B=whiteboard, K=bookshelf, C=coffee_machine
export const OFFICE_MAP: string[][] = [
  ["W","W","W","W","N","W","W","W","N","W","W","W","W","W"],
  ["W","F","F","1","5","F","F","F","F","2","6","F","F","W"],
  ["W","F","F","F","F","F","F","F","F","F","F","F","F","W"],
  ["W","F","F","F","F","F","B","B","F","F","F","F","F","W"],
  ["W","F","F","F","F","S","R","R","S","F","F","F","F","W"],
  ["W","F","F","F","F","F","R","R","F","F","F","F","F","W"],
  ["W","F","F","3","7","F","F","F","F","4","8","F","F","W"],
  ["W","F","F","F","F","F","P","C","F","F","F","F","F","W"],
  ["W","W","W","W","W","D","F","F","D","W","W","W","W","W"],
];

// 걸을 수 있는 타일인지
export function isWalkable(col: number, row: number): boolean {
  if (row < 0 || row >= OFFICE_ROWS || col < 0 || col >= OFFICE_COLS) return false;
  const tile = OFFICE_MAP[row]![col]!;
  return ["F", "R", "D"].includes(tile);
}

// 타일 색상
export const TILE_COLORS: Record<string, string> = {
  W: "#3a3a4a",   // 벽
  F: "#4a4a5a",   // 바닥
  D: "#5a6a5a",   // 문
  N: "#4a5a6a",   // 창문
  R: "#5a4a4a",   // 러그
  S: "#6a5a4a",   // 소파
  P: "#3a5a3a",   // 식물
  B: "#5a5a6a",   // 화이트보드
  K: "#5a4a3a",   // 책장
  C: "#4a3a3a",   // 커피머신
  "1": "#5a4a5a", "2": "#4a5a5a", "3": "#5a5a4a", "4": "#5a4a4a", // 책상
  "5": "#4a4a5a", "6": "#4a4a5a", "7": "#4a4a5a", "8": "#4a4a5a", // 의자
};

// 에이전트별 책상/의자 위치
export const AGENT_DESK_POSITIONS: Record<AgentId, { desk: { col: number; row: number }; chair: { col: number; row: number } }> = {
  seo_yeon: { desk: { col: 3, row: 1 }, chair: { col: 4, row: 1 } },
  jun_ho:   { desk: { col: 9, row: 1 }, chair: { col: 10, row: 1 } },
  ha_eun:   { desk: { col: 3, row: 6 }, chair: { col: 4, row: 6 } },
  min_su:   { desk: { col: 9, row: 6 }, chair: { col: 10, row: 6 } },
};
