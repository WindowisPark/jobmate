import { useEffect, useRef } from "react";
import { useOfficeStore } from "@/stores/officeStore";
import { AGENTS } from "@/types/agent";
import type { AgentId } from "@/types/agent";
import {
  TILE_SIZE,
  OFFICE_COLS,
  OFFICE_ROWS,
  OFFICE_MAP,
  TILE_COLORS,
} from "@/types/office";

const WIDTH = OFFICE_COLS * TILE_SIZE;
const HEIGHT = OFFICE_ROWS * TILE_SIZE;

const AGENT_COLORS: Record<string, string> = {
  seo_yeon: "#e06c75",
  jun_ho: "#61afef",
  ha_eun: "#98c379",
  min_su: "#e5c07b",
};

function drawRoundRect(
  ctx: CanvasRenderingContext2D,
  x: number, y: number, w: number, h: number, r: number,
) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
  ctx.fill();
}

export function OfficeView() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameRef = useRef(0);
  const tick = useOfficeStore((s) => s.tick);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;

    const render = () => {
      // 상태 업데이트
      tick();
      frameRef.current++;
      const frame = frameRef.current;
      const agents = useOfficeStore.getState().agents;

      ctx.clearRect(0, 0, WIDTH, HEIGHT);

      // === 타일맵 ===
      for (let row = 0; row < OFFICE_ROWS; row++) {
        for (let col = 0; col < OFFICE_COLS; col++) {
          const tile = OFFICE_MAP[row]![col]!;
          const x = col * TILE_SIZE;
          const y = row * TILE_SIZE;

          ctx.fillStyle = TILE_COLORS[tile] ?? "#4a4a5a";
          ctx.fillRect(x, y, TILE_SIZE, TILE_SIZE);

          ctx.strokeStyle = "rgba(255,255,255,0.03)";
          ctx.strokeRect(x, y, TILE_SIZE, TILE_SIZE);

          if (tile === "W") {
            ctx.fillStyle = "rgba(0,0,0,0.2)";
            ctx.fillRect(x, y, TILE_SIZE, TILE_SIZE);
          }

          if (tile === "N") {
            ctx.fillStyle = "rgba(100,180,255,0.15)";
            ctx.fillRect(x, y, TILE_SIZE, TILE_SIZE);
          }

          if (tile === "R") {
            ctx.fillStyle = "rgba(180,100,80,0.1)";
            ctx.fillRect(x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4);
          }

          // 책상
          if (["1", "2", "3", "4"].includes(tile)) {
            ctx.fillStyle = "#7a6a5a";
            ctx.fillRect(x + 4, y + 4, TILE_SIZE - 8, TILE_SIZE - 8);
            ctx.fillStyle = "#2a3a4a";
            ctx.fillRect(x + 10, y + 8, TILE_SIZE - 20, TILE_SIZE - 20);
            ctx.fillStyle = "#4a8abd";
            ctx.fillRect(x + 12, y + 10, TILE_SIZE - 24, TILE_SIZE - 24);
          }

          // 의자
          if (["5", "6", "7", "8"].includes(tile)) {
            ctx.fillStyle = "#5a5a6a";
            ctx.fillRect(x + 10, y + 10, TILE_SIZE - 20, TILE_SIZE - 20);
          }

          // 소파
          if (tile === "S") {
            ctx.fillStyle = "#8a6a5a";
            ctx.fillRect(x + 4, y + 8, TILE_SIZE - 8, TILE_SIZE - 16);
            ctx.fillStyle = "#9a7a6a";
            ctx.fillRect(x + 6, y + 10, TILE_SIZE - 12, TILE_SIZE - 22);
          }

          // 식물
          if (tile === "P") {
            ctx.fillStyle = "#5a3a2a";
            ctx.fillRect(x + 14, y + 22, 12, 14);
            ctx.fillStyle = "#4a8a4a";
            ctx.beginPath();
            ctx.arc(x + 20, y + 18, 12, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = "#3a7a3a";
            ctx.beginPath();
            ctx.arc(x + 16, y + 14, 8, 0, Math.PI * 2);
            ctx.fill();
          }

          // 화이트보드
          if (tile === "B") {
            ctx.fillStyle = "#ddd";
            ctx.fillRect(x + 4, y + 4, TILE_SIZE - 8, TILE_SIZE - 10);
            ctx.fillStyle = "#aaa";
            ctx.fillRect(x + 6, y + 6, TILE_SIZE - 12, 2);
            ctx.fillRect(x + 6, y + 12, TILE_SIZE - 16, 2);
            ctx.fillRect(x + 6, y + 18, TILE_SIZE - 14, 2);
          }

          // 커피머신
          if (tile === "C") {
            ctx.fillStyle = "#4a3a3a";
            ctx.fillRect(x + 10, y + 8, TILE_SIZE - 20, TILE_SIZE - 14);
            ctx.fillStyle = "#e06c75";
            ctx.beginPath();
            ctx.arc(x + 20, y + 20, 4, 0, Math.PI * 2);
            ctx.fill();
          }

          // 문
          if (tile === "D") {
            ctx.fillStyle = "#6a5a4a";
            ctx.fillRect(x + 8, y, TILE_SIZE - 16, TILE_SIZE);
          }
        }
      }

      // === 에이전트 (y순 정렬) ===
      const agentList = (Object.keys(agents) as AgentId[])
        .map((id) => ({ ...agents[id]!, agentId: id }))
        .sort((a, b) => a.y - b.y);

      for (const agent of agentList) {
        const color = AGENT_COLORS[agent.agentId] ?? "#aaa";
        const profile = AGENTS[agent.agentId];
        const isTyping = agent.behavior === "typing";
        const isWalking =
          agent.behavior === "wandering" || agent.behavior === "walking_to_desk";

        const cx = agent.x + TILE_SIZE / 2;
        const cy = agent.y + TILE_SIZE / 2;

        // 그림자
        ctx.fillStyle = "rgba(0,0,0,0.2)";
        ctx.beginPath();
        ctx.ellipse(cx, cy + 14, 10, 4, 0, 0, Math.PI * 2);
        ctx.fill();

        // 바운스
        const bounce = isWalking ? Math.sin(frame * 0.3) * 2 : 0;
        const bodyY = cy - 4 + bounce;

        // 몸
        ctx.fillStyle = color;
        drawRoundRect(ctx, cx - 8, bodyY - 2, 16, 18, 4);

        // 머리
        ctx.fillStyle = "#f0d0a0";
        ctx.beginPath();
        ctx.arc(cx, bodyY - 10, 9, 0, Math.PI * 2);
        ctx.fill();

        // 머리카락
        ctx.fillStyle = agent.agentId === "ha_eun" ? "#4a3020" : "#2a2020";
        ctx.beginPath();
        ctx.arc(cx, bodyY - 13, 9, Math.PI, Math.PI * 2);
        ctx.fill();

        // 타이핑 — 팔
        if (isTyping) {
          const armOff = Math.sin(frame * 0.4) * 3;
          ctx.fillStyle = color;
          ctx.fillRect(cx - 12, bodyY + 2, 5, 8 + armOff);
          ctx.fillRect(cx + 7, bodyY + 2, 5, 8 - armOff);
          if (frame % 8 < 4) {
            ctx.fillStyle = "#fff";
            ctx.fillRect(cx - 14 + (frame % 3) * 4, bodyY + 12, 2, 2);
          }
        }

        // 다리
        ctx.fillStyle = "#3a3a4a";
        if (isWalking) {
          const legOff = Math.sin(frame * 0.3) * 4;
          ctx.fillRect(cx - 5, bodyY + 14, 4, 6 + legOff);
          ctx.fillRect(cx + 1, bodyY + 14, 4, 6 - legOff);
        } else {
          ctx.fillRect(cx - 5, bodyY + 14, 4, 6);
          ctx.fillRect(cx + 1, bodyY + 14, 4, 6);
        }

        // 이름
        ctx.font = "bold 9px sans-serif";
        ctx.textAlign = "center";
        ctx.fillStyle = "rgba(0,0,0,0.6)";
        ctx.fillText(profile.name, cx + 1, bodyY - 22 + 1);
        ctx.fillStyle = "#fff";
        ctx.fillText(profile.name, cx, bodyY - 22);

        // 타이핑 말풍선
        if (isTyping) {
          const by = bodyY - 36;
          ctx.fillStyle = "rgba(0,0,0,0.7)";
          drawRoundRect(ctx, cx - 22, by - 4, 44, 14, 6);
          ctx.font = "8px sans-serif";
          ctx.fillStyle = color;
          const dots = ".".repeat((Math.floor(frame / 10) % 3) + 1);
          ctx.textAlign = "center";
          ctx.fillText(`타이핑${dots}`, cx, by + 6);
        }
      }

      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(animId);
  }, [tick]);

  return (
    <div
      style={{
        background: "#232428",
        borderBottom: "1px solid #383a3f",
        display: "flex",
        justifyContent: "center",
        padding: "8px 0",
        minHeight: HEIGHT + 16,
      }}
    >
      <canvas
        ref={canvasRef}
        width={WIDTH}
        height={HEIGHT}
        style={{
          borderRadius: 8,
        }}
      />
    </div>
  );
}
