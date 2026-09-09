// 에이전트 아바타 — 방의 픽셀 블롭 스프라이트(16px, CC0 팔레트)를 그대로 쓴다.
// 사람 얼굴 SVG 는 방 캐릭터(사람 아닌 픽셀 크리처)와 정체성이 어긋나 제거했다.
import { AGENTS } from "@/types/agent";
import type { AgentId } from "@/types/agent";

interface Props {
  agentId: AgentId;
  size?: number;
}

const SPRITES: Record<AgentId, string> = {
  seo_yeon: "/room/pixel/blob_seo_yeon.png",
  jun_ho: "/room/pixel/blob_jun_ho.png",
  ha_eun: "/room/pixel/blob_ha_eun.png",
  min_su: "/room/pixel/blob_min_su.png",
};

export function AgentAvatar({ agentId, size = 48 }: Props) {
  const color = AGENTS[agentId]?.color ?? "#999";
  // 스프라이트는 원 안에서 정수배로만 키운다 — 픽셀이 뭉개지지 않게
  const scale = Math.max(1, Math.floor((size * 0.7) / 16));
  const px = 16 * scale;
  return (
    <span
      role="img"
      aria-label={AGENTS[agentId]?.name}
      style={{
        width: size, height: size, borderRadius: "50%", flexShrink: 0,
        background: `${color}22`, border: `2px solid ${color}55`,
        display: "inline-flex", alignItems: "center", justifyContent: "center",
        boxSizing: "border-box",
      }}
    >
      <img
        src={SPRITES[agentId]}
        alt=""
        width={px}
        height={px}
        draggable={false}
        style={{ imageRendering: "pixelated", display: "block" }}
      />
    </span>
  );
}
