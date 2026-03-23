import { useEffect, useRef } from "react";
import { useOfficeStore } from "@/stores/officeStore";
import { AGENTS } from "@/types/agent";
import type { AgentId } from "@/types/agent";
import { TILE_SIZE, OFFICE_COLS, OFFICE_ROWS, OFFICE_MAP, TILE_COLORS } from "@/types/office";

const WIDTH = OFFICE_COLS * TILE_SIZE;
const HEIGHT = OFFICE_ROWS * TILE_SIZE;

// 캐릭터별 스타일
const CHAR_STYLE: Record<AgentId, {
  bodyColor: string;
  hairColor: string;
  hairStyle: "short" | "long" | "ponytail" | "curly";
  skinTone: string;
  accessory?: "glasses" | "earring" | "headband";
}> = {
  seo_yeon: { bodyColor: "#e06c75", hairColor: "#2a1a1a", hairStyle: "long", skinTone: "#f5d0a9", accessory: "earring" },
  jun_ho:   { bodyColor: "#61afef", hairColor: "#1a1a2a", hairStyle: "short", skinTone: "#f0c8a0", accessory: "glasses" },
  ha_eun:   { bodyColor: "#98c379", hairColor: "#3a2a1a", hairStyle: "ponytail", skinTone: "#f5d5b0", accessory: "headband" },
  min_su:   { bodyColor: "#e5c07b", hairColor: "#1a1a1a", hairStyle: "curly", skinTone: "#e8c098" },
};

function drawRoundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
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

function drawCharacter(
  ctx: CanvasRenderingContext2D,
  agentId: AgentId,
  cx: number, cy: number,
  isTyping: boolean, isWalking: boolean,
  frame: number,
) {
  const style = CHAR_STYLE[agentId];
  const profile = AGENTS[agentId];
  const bounce = isWalking ? Math.sin(frame * 0.25) * 2.5 : 0;
  const bodyY = cy - 4 + bounce;

  // 그림자
  ctx.fillStyle = "rgba(0,0,0,0.15)";
  ctx.beginPath();
  ctx.ellipse(cx, cy + 15, 11, 4, 0, 0, Math.PI * 2);
  ctx.fill();

  // 다리
  ctx.fillStyle = "#3a3a4a";
  if (isWalking) {
    const legOff = Math.sin(frame * 0.25) * 5;
    ctx.fillRect(cx - 5, bodyY + 15, 4, 7 + legOff);
    ctx.fillRect(cx + 1, bodyY + 15, 4, 7 - legOff);
  } else {
    ctx.fillRect(cx - 5, bodyY + 15, 4, 7);
    ctx.fillRect(cx + 1, bodyY + 15, 4, 7);
  }

  // 신발
  ctx.fillStyle = "#2a2a3a";
  ctx.fillRect(cx - 6, bodyY + 21, 6, 2);
  ctx.fillRect(cx, bodyY + 21, 6, 2);

  // 몸
  ctx.fillStyle = style.bodyColor;
  drawRoundRect(ctx, cx - 9, bodyY - 1, 18, 18, 4);

  // 팔
  if (isTyping) {
    const armOff = Math.sin(frame * 0.35) * 3;
    ctx.fillStyle = style.bodyColor;
    ctx.fillRect(cx - 13, bodyY + 3, 5, 9 + armOff);
    ctx.fillRect(cx + 8, bodyY + 3, 5, 9 - armOff);
    // 손
    ctx.fillStyle = style.skinTone;
    ctx.beginPath();
    ctx.arc(cx - 10, bodyY + 13 + armOff, 3, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(cx + 10, bodyY + 13 - armOff, 3, 0, Math.PI * 2);
    ctx.fill();
  } else {
    ctx.fillStyle = style.bodyColor;
    ctx.fillRect(cx - 13, bodyY + 3, 5, 10);
    ctx.fillRect(cx + 8, bodyY + 3, 5, 10);
  }

  // 머리
  ctx.fillStyle = style.skinTone;
  ctx.beginPath();
  ctx.arc(cx, bodyY - 10, 10, 0, Math.PI * 2);
  ctx.fill();

  // 머리카락 (스타일별)
  ctx.fillStyle = style.hairColor;
  if (style.hairStyle === "short") {
    ctx.beginPath();
    ctx.arc(cx, bodyY - 13, 10, Math.PI, Math.PI * 2);
    ctx.fill();
    ctx.fillRect(cx - 10, bodyY - 14, 20, 5);
  } else if (style.hairStyle === "long") {
    ctx.beginPath();
    ctx.arc(cx, bodyY - 13, 10, Math.PI * 0.85, Math.PI * 2.15);
    ctx.fill();
    // 긴 머리 양옆
    ctx.fillRect(cx - 11, bodyY - 12, 4, 16);
    ctx.fillRect(cx + 7, bodyY - 12, 4, 16);
  } else if (style.hairStyle === "ponytail") {
    ctx.beginPath();
    ctx.arc(cx, bodyY - 13, 10, Math.PI, Math.PI * 2);
    ctx.fill();
    // 포니테일
    ctx.fillRect(cx + 6, bodyY - 16, 4, 3);
    ctx.beginPath();
    ctx.arc(cx + 10, bodyY - 10, 5, 0, Math.PI * 2);
    ctx.fill();
  } else if (style.hairStyle === "curly") {
    ctx.beginPath();
    ctx.arc(cx, bodyY - 13, 11, Math.PI * 0.8, Math.PI * 2.2);
    ctx.fill();
    // 곱슬 텍스처
    for (let i = 0; i < 4; i++) {
      ctx.beginPath();
      ctx.arc(cx - 8 + i * 5, bodyY - 18, 3, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // 액세서리
  if (style.accessory === "glasses") {
    ctx.strokeStyle = "#666";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(cx - 4, bodyY - 10, 4, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(cx + 4, bodyY - 10, 4, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(cx, bodyY - 10);
    ctx.lineTo(cx, bodyY - 10);
    ctx.stroke();
  } else if (style.accessory === "earring") {
    ctx.fillStyle = "#ffd700";
    ctx.beginPath();
    ctx.arc(cx - 10, bodyY - 6, 2, 0, Math.PI * 2);
    ctx.fill();
  } else if (style.accessory === "headband") {
    ctx.strokeStyle = style.bodyColor;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(cx, bodyY - 14, 10, Math.PI * 1.1, Math.PI * 1.9);
    ctx.stroke();
  }

  // 눈
  ctx.fillStyle = "#2a2a2a";
  ctx.beginPath();
  ctx.arc(cx - 4, bodyY - 10, 1.5, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.arc(cx + 4, bodyY - 10, 1.5, 0, Math.PI * 2);
  ctx.fill();

  // 입 (타이핑중이면 말하는 모양)
  if (isTyping && frame % 20 < 10) {
    ctx.fillStyle = "#c06060";
    ctx.beginPath();
    ctx.arc(cx, bodyY - 6, 2, 0, Math.PI);
    ctx.fill();
  } else {
    ctx.strokeStyle = "#c08080";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(cx, bodyY - 6, 2, 0.1, Math.PI - 0.1);
    ctx.stroke();
  }

  // 이름
  ctx.font = "bold 9px sans-serif";
  ctx.textAlign = "center";
  ctx.fillStyle = "rgba(0,0,0,0.5)";
  ctx.fillText(profile.name, cx + 1, bodyY - 25 + 1);
  ctx.fillStyle = "#fff";
  ctx.fillText(profile.name, cx, bodyY - 25);

  // 타이핑 말풍선
  if (isTyping) {
    const by = bodyY - 38;
    ctx.fillStyle = "rgba(0,0,0,0.75)";
    drawRoundRect(ctx, cx - 24, by - 5, 48, 16, 6);
    // 꼬리
    ctx.beginPath();
    ctx.moveTo(cx - 3, by + 11);
    ctx.lineTo(cx + 3, by + 11);
    ctx.lineTo(cx, by + 15);
    ctx.closePath();
    ctx.fill();

    ctx.font = "9px sans-serif";
    ctx.fillStyle = style.bodyColor;
    ctx.textAlign = "center";
    const dots = "●".repeat((Math.floor(frame / 8) % 3) + 1).padEnd(3, "○");
    ctx.fillText(`타이핑 ${dots}`, cx, by + 7);
  }
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

          // 바닥
          ctx.fillStyle = TILE_COLORS[tile] ?? "#4a4a5a";
          ctx.fillRect(x, y, TILE_SIZE, TILE_SIZE);

          // 바닥 패턴 (체크무늬)
          if (["F", "R", "D"].includes(tile)) {
            if ((row + col) % 2 === 0) {
              ctx.fillStyle = "rgba(255,255,255,0.015)";
              ctx.fillRect(x, y, TILE_SIZE, TILE_SIZE);
            }
          }

          if (tile === "W") {
            ctx.fillStyle = "rgba(0,0,0,0.15)";
            ctx.fillRect(x, y, TILE_SIZE, TILE_SIZE);
            // 벽 텍스처
            ctx.fillStyle = "rgba(255,255,255,0.02)";
            ctx.fillRect(x, y + TILE_SIZE - 3, TILE_SIZE, 3);
          }

          if (tile === "N") {
            // 창문 — 반짝이는 효과
            const glow = Math.sin(frame * 0.02 + col) * 0.05 + 0.15;
            ctx.fillStyle = `rgba(100,180,255,${glow})`;
            ctx.fillRect(x, y, TILE_SIZE, TILE_SIZE);
            ctx.fillStyle = "rgba(200,230,255,0.08)";
            ctx.fillRect(x + 4, y + 4, TILE_SIZE - 8, TILE_SIZE - 8);
          }

          if (tile === "R") {
            ctx.fillStyle = "rgba(180,100,80,0.08)";
            ctx.fillRect(x + 1, y + 1, TILE_SIZE - 2, TILE_SIZE - 2);
            // 러그 보더
            ctx.strokeStyle = "rgba(180,100,80,0.12)";
            ctx.lineWidth = 1;
            ctx.strokeRect(x + 3, y + 3, TILE_SIZE - 6, TILE_SIZE - 6);
          }

          // 책상
          if (["1", "2", "3", "4"].includes(tile)) {
            // 책상 본체
            ctx.fillStyle = "#7a6a55";
            drawRoundRect(ctx, x + 3, y + 3, TILE_SIZE - 6, TILE_SIZE - 6, 3);
            // 모니터
            ctx.fillStyle = "#1a2a3a";
            ctx.fillRect(x + 8, y + 6, TILE_SIZE - 16, TILE_SIZE - 18);
            // 화면 (살짝 빛남)
            const screenGlow = Math.sin(frame * 0.03) * 0.1 + 0.5;
            ctx.fillStyle = `rgba(74,138,189,${screenGlow})`;
            ctx.fillRect(x + 10, y + 8, TILE_SIZE - 20, TILE_SIZE - 22);
            // 모니터 받침
            ctx.fillStyle = "#555";
            ctx.fillRect(x + TILE_SIZE / 2 - 3, y + TILE_SIZE - 10, 6, 4);
          }

          // 의자
          if (["5", "6", "7", "8"].includes(tile)) {
            const chairIdx = parseInt(tile) - 5;
            const chairColors = ["#8a5050", "#506080", "#508050", "#806050"];
            ctx.fillStyle = chairColors[chairIdx] ?? "#5a5a6a";
            drawRoundRect(ctx, x + 8, y + 8, TILE_SIZE - 16, TILE_SIZE - 16, 4);
            // 의자 등받이
            ctx.fillStyle = chairColors[chairIdx] ?? "#5a5a6a";
            ctx.fillRect(x + 10, y + 4, TILE_SIZE - 20, 6);
          }

          // 소파
          if (tile === "S") {
            ctx.fillStyle = "#8a6a55";
            drawRoundRect(ctx, x + 3, y + 6, TILE_SIZE - 6, TILE_SIZE - 10, 5);
            ctx.fillStyle = "#9a7a65";
            drawRoundRect(ctx, x + 5, y + 8, TILE_SIZE - 10, TILE_SIZE - 16, 4);
            // 쿠션
            ctx.fillStyle = "#a08a70";
            ctx.beginPath();
            ctx.arc(x + TILE_SIZE / 2, y + TILE_SIZE / 2, 6, 0, Math.PI * 2);
            ctx.fill();
          }

          // 식물
          if (tile === "P") {
            // 화분
            ctx.fillStyle = "#8a5a3a";
            drawRoundRect(ctx, x + 12, y + 20, 16, 16, 3);
            ctx.fillStyle = "#6a4a2a";
            ctx.fillRect(x + 10, y + 20, 20, 4);
            // 잎
            ctx.fillStyle = "#4a8a4a";
            ctx.beginPath(); ctx.arc(x + 20, y + 16, 10, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = "#3a7a3a";
            ctx.beginPath(); ctx.arc(x + 15, y + 12, 7, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = "#5a9a5a";
            ctx.beginPath(); ctx.arc(x + 25, y + 14, 6, 0, Math.PI * 2); ctx.fill();
          }

          // 화이트보드
          if (tile === "B") {
            ctx.fillStyle = "#bbb";
            ctx.fillRect(x + 3, y + 2, TILE_SIZE - 6, TILE_SIZE - 6);
            ctx.fillStyle = "#eee";
            ctx.fillRect(x + 5, y + 4, TILE_SIZE - 10, TILE_SIZE - 10);
            // 낙서
            ctx.strokeStyle = "#e06c7588";
            ctx.lineWidth = 1;
            ctx.beginPath(); ctx.moveTo(x + 8, y + 10); ctx.lineTo(x + 20, y + 14); ctx.stroke();
            ctx.strokeStyle = "#61afef88";
            ctx.beginPath(); ctx.moveTo(x + 10, y + 18); ctx.lineTo(x + 28, y + 20); ctx.stroke();
            ctx.strokeStyle = "#98c37988";
            ctx.beginPath(); ctx.moveTo(x + 8, y + 26); ctx.lineTo(x + 24, y + 24); ctx.stroke();
          }

          // 커피머신
          if (tile === "C") {
            ctx.fillStyle = "#4a3a3a";
            drawRoundRect(ctx, x + 8, y + 6, TILE_SIZE - 16, TILE_SIZE - 10, 4);
            // 빨간불
            ctx.fillStyle = "#e06c75";
            ctx.beginPath(); ctx.arc(x + 20, y + 22, 3, 0, Math.PI * 2); ctx.fill();
            // 스팀
            if (frame % 30 < 15) {
              ctx.fillStyle = "rgba(255,255,255,0.1)";
              ctx.beginPath(); ctx.arc(x + 20, y + 2, 4, 0, Math.PI * 2); ctx.fill();
            }
          }

          // 문
          if (tile === "D") {
            ctx.fillStyle = "#6a5a4a";
            drawRoundRect(ctx, x + 6, y, TILE_SIZE - 12, TILE_SIZE, 2);
            // 손잡이
            ctx.fillStyle = "#ffd700";
            ctx.beginPath(); ctx.arc(x + TILE_SIZE - 12, y + TILE_SIZE / 2, 2, 0, Math.PI * 2); ctx.fill();
          }
        }
      }

      // === 에이전트 (y순) ===
      const agentList = (Object.keys(agents) as AgentId[])
        .map((id) => ({ ...agents[id]!, agentId: id }))
        .sort((a, b) => a.y - b.y);

      for (const agent of agentList) {
        const cx = agent.x + TILE_SIZE / 2;
        const cy = agent.y + TILE_SIZE / 2;
        const isTyping = agent.behavior === "typing";
        const isWalking = agent.behavior === "wandering" || agent.behavior === "walking_to_desk";

        drawCharacter(ctx, agent.agentId, cx, cy, isTyping, isWalking, frame);
      }

      // 오피스 테두리 비네팅 효과
      const grad = ctx.createRadialGradient(WIDTH / 2, HEIGHT / 2, HEIGHT * 0.4, WIDTH / 2, HEIGHT / 2, HEIGHT * 0.8);
      grad.addColorStop(0, "rgba(0,0,0,0)");
      grad.addColorStop(1, "rgba(0,0,0,0.15)");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, WIDTH, HEIGHT);

      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(animId);
  }, [tick]);

  return (
    <div
      style={{
        background: "#1e2024",
        borderBottom: "1px solid var(--border)",
        display: "flex",
        justifyContent: "center",
        padding: "10px 0",
        minHeight: HEIGHT + 20,
      }}
    >
      <canvas
        ref={canvasRef}
        width={WIDTH}
        height={HEIGHT}
        style={{ borderRadius: "var(--radius-lg)", border: "1px solid rgba(255,255,255,0.05)" }}
      />
    </div>
  );
}
