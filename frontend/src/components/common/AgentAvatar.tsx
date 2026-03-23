import type { AgentId } from "@/types/agent";

interface Props {
  agentId: AgentId;
  size?: number;
}

export function AgentAvatar({ agentId, size = 48 }: Props) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      {agentId === "seo_yeon" && <SeoYeonSVG />}
      {agentId === "jun_ho" && <JunHoSVG />}
      {agentId === "ha_eun" && <HaEunSVG />}
      {agentId === "min_su" && <MinSuSVG />}
    </svg>
  );
}

// 김서연 — 커리어 코치, 긴 머리, 귀걸이
function SeoYeonSVG() {
  return (
    <g>
      <circle cx="50" cy="50" r="48" fill="#e06c7522" stroke="#e06c7544" strokeWidth="2" />

      {/* Body */}
      <path d="M30 88 C30 70 38 64 50 64 C62 64 70 70 70 88" fill="#e06c75" />
      <path d="M42 66 L50 74 L58 66" fill="none" stroke="#c05560" strokeWidth="2" />

      {/* Neck */}
      <rect x="45" y="58" width="10" height="8" rx="3" fill="#f5d0a9" />

      {/* Hair back — behind face */}
      <ellipse cx="50" cy="38" rx="24" ry="12" fill="#2a1a1a" />
      {/* Side hair (long) behind face */}
      <rect x="26" y="36" width="6" height="28" rx="3" fill="#2a1a1a" />
      <rect x="68" y="36" width="6" height="28" rx="3" fill="#2a1a1a" />

      {/* Face */}
      <circle cx="50" cy="44" r="20" fill="#f5d0a9" />

      {/* Hair front — bangs only (above eyebrows) */}
      <path d="M30 38 C30 28 38 22 50 22 C62 22 70 28 70 38 L70 36 C70 36 65 32 50 32 C35 32 30 36 30 36 Z" fill="#2a1a1a" />
      {/* Fringe detail */}
      <path d="M34 36 Q42 30 50 32 Q58 30 66 36" fill="#2a1a1a" />

      {/* Eyes */}
      <ellipse cx="42" cy="44" rx="3" ry="3.5" fill="#2a2020" />
      <ellipse cx="58" cy="44" rx="3" ry="3.5" fill="#2a2020" />
      <circle cx="43.5" cy="43" r="1.2" fill="white" />
      <circle cx="59.5" cy="43" r="1.2" fill="white" />

      {/* Eyebrows */}
      <path d="M37 38 Q42 36 46 38" stroke="#2a1a1a" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      <path d="M54 38 Q58 36 63 38" stroke="#2a1a1a" strokeWidth="1.5" fill="none" strokeLinecap="round" />

      {/* Nose */}
      <path d="M49 48 Q50 50 51 48" stroke="#d4a070" strokeWidth="1" fill="none" />

      {/* Smile */}
      <path d="M44 53 Q50 57 56 53" stroke="#c06060" strokeWidth="1.5" fill="none" strokeLinecap="round" />

      {/* Blush */}
      <ellipse cx="38" cy="50" rx="4" ry="2.5" fill="#e06c7533" />
      <ellipse cx="62" cy="50" rx="4" ry="2.5" fill="#e06c7533" />

      {/* Earring */}
      <circle cx="27" cy="48" r="2.5" fill="#ffd700" />
      <circle cx="27" cy="52" r="1.5" fill="#ffed4a" />

      {/* Pen */}
      <line x1="68" y1="74" x2="74" y2="68" stroke="#fff" strokeWidth="2" strokeLinecap="round" />
    </g>
  );
}

// 박준호 — 취업 리서처, 짧은 머리, 안경
function JunHoSVG() {
  return (
    <g>
      <circle cx="50" cy="50" r="48" fill="#61afef22" stroke="#61afef44" strokeWidth="2" />

      {/* Body */}
      <path d="M30 88 C30 70 38 64 50 64 C62 64 70 70 70 88" fill="#61afef" />
      <rect x="44" y="64" width="12" height="6" rx="1" fill="#4a8abd" />
      <line x1="50" y1="64" x2="50" y2="70" stroke="#3a7aad" strokeWidth="1" />

      {/* Neck */}
      <rect x="45" y="58" width="10" height="8" rx="3" fill="#f0c8a0" />

      {/* Hair back */}
      <ellipse cx="50" cy="34" rx="22" ry="10" fill="#1a1a2a" />

      {/* Face */}
      <circle cx="50" cy="44" r="20" fill="#f0c8a0" />

      {/* Hair front — short neat top */}
      <path d="M30 36 C30 26 38 20 50 20 C62 20 70 26 70 36 L68 34 C66 28 58 24 50 24 C42 24 34 28 32 34 Z" fill="#1a1a2a" />

      {/* Glasses */}
      <circle cx="42" cy="44" r="7" fill="none" stroke="#666" strokeWidth="2" />
      <circle cx="58" cy="44" r="7" fill="none" stroke="#666" strokeWidth="2" />
      <line x1="49" y1="44" x2="51" y2="44" stroke="#666" strokeWidth="2" />
      <line x1="35" y1="42" x2="30" y2="40" stroke="#666" strokeWidth="1.5" />
      <line x1="65" y1="42" x2="70" y2="40" stroke="#666" strokeWidth="1.5" />

      {/* Eyes behind glasses */}
      <ellipse cx="42" cy="44" rx="2.5" ry="3" fill="#1a1a2a" />
      <ellipse cx="58" cy="44" rx="2.5" ry="3" fill="#1a1a2a" />
      <circle cx="43" cy="43" r="1" fill="white" />
      <circle cx="59" cy="43" r="1" fill="white" />

      {/* Eyebrows */}
      <line x1="37" y1="36" x2="46" y2="37" stroke="#1a1a2a" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="54" y1="37" x2="63" y2="36" stroke="#1a1a2a" strokeWidth="1.5" strokeLinecap="round" />

      {/* Nose */}
      <path d="M49 49 Q50 51 51 49" stroke="#c8a070" strokeWidth="1" fill="none" />

      {/* Mouth — focused */}
      <path d="M45 54 Q50 56 55 54" stroke="#a06060" strokeWidth="1.5" fill="none" strokeLinecap="round" />

      {/* Magnifying glass */}
      <circle cx="74" cy="72" r="5" fill="none" stroke="#61afef" strokeWidth="2" />
      <line x1="78" y1="76" x2="82" y2="80" stroke="#61afef" strokeWidth="2" strokeLinecap="round" />
    </g>
  );
}

// 이하은 — 멘탈 케어, 포니테일, 머리띠
function HaEunSVG() {
  return (
    <g>
      <circle cx="50" cy="50" r="48" fill="#98c37922" stroke="#98c37944" strokeWidth="2" />

      {/* Body */}
      <path d="M30 88 C30 70 38 64 50 64 C62 64 70 70 70 88" fill="#98c379" />
      <ellipse cx="50" cy="67" rx="10" ry="4" fill="#88b369" />

      {/* Neck */}
      <rect x="45" y="58" width="10" height="8" rx="3" fill="#f5d5b0" />

      {/* Hair back */}
      <ellipse cx="50" cy="36" rx="23" ry="12" fill="#3a2a1a" />
      {/* Ponytail */}
      <ellipse cx="72" cy="38" rx="8" ry="14" fill="#3a2a1a" />
      <circle cx="66" cy="32" r="3" fill="#98c379" />

      {/* Face */}
      <circle cx="50" cy="44" r="20" fill="#f5d5b0" />

      {/* Hair front — soft bangs */}
      <path d="M30 38 C30 28 40 22 50 22 C60 22 70 28 70 38 Q60 34 50 35 Q40 34 30 38 Z" fill="#3a2a1a" />

      {/* Headband */}
      <path d="M30 36 Q50 28 70 36" stroke="#98c379" strokeWidth="3" fill="none" strokeLinecap="round" />

      {/* Eyes — bigger, softer */}
      <ellipse cx="42" cy="45" rx="3.5" ry="4" fill="#2a2020" />
      <ellipse cx="58" cy="45" rx="3.5" ry="4" fill="#2a2020" />
      <circle cx="43.5" cy="44" r="1.5" fill="white" />
      <circle cx="59.5" cy="44" r="1.5" fill="white" />
      <circle cx="41" cy="46" r="0.7" fill="white" />
      <circle cx="57" cy="46" r="0.7" fill="white" />

      {/* Soft eyebrows */}
      <path d="M38 39 Q42 37 45 39" stroke="#3a2a1a" strokeWidth="1.2" fill="none" strokeLinecap="round" />
      <path d="M55 39 Q58 37 62 39" stroke="#3a2a1a" strokeWidth="1.2" fill="none" strokeLinecap="round" />

      {/* Nose */}
      <path d="M49 49 Q50 51 51 49" stroke="#d4a888" strokeWidth="1" fill="none" />

      {/* Warm smile */}
      <path d="M43 53 Q50 58 57 53" stroke="#c06060" strokeWidth="1.5" fill="none" strokeLinecap="round" />

      {/* Big blush */}
      <ellipse cx="37" cy="51" rx="5" ry="3" fill="#ff8a8a33" />
      <ellipse cx="63" cy="51" rx="5" ry="3" fill="#ff8a8a33" />

      {/* Leaf */}
      <path d="M24 74 Q20 66 26 62 Q30 68 24 74 Z" fill="#5a9a5a" />
    </g>
  );
}

// 정민수 — 현직자 멘토, 곱슬머리, 유머
function MinSuSVG() {
  return (
    <g>
      <circle cx="50" cy="50" r="48" fill="#e5c07b22" stroke="#e5c07b44" strokeWidth="2" />

      {/* Body */}
      <path d="M30 88 C30 70 38 64 50 64 C62 64 70 70 70 88" fill="#e5c07b" />
      <line x1="46" y1="66" x2="44" y2="74" stroke="#d5b06b" strokeWidth="1" />
      <line x1="54" y1="66" x2="56" y2="74" stroke="#d5b06b" strokeWidth="1" />

      {/* Neck */}
      <rect x="45" y="58" width="10" height="8" rx="3" fill="#e8c098" />

      {/* Hair back */}
      <ellipse cx="50" cy="34" rx="24" ry="12" fill="#1a1a1a" />

      {/* Face */}
      <circle cx="50" cy="44" r="20" fill="#e8c098" />

      {/* Hair front — curly */}
      <path d="M28 38 C28 26 38 18 50 18 C62 18 72 26 72 38 Q62 34 50 35 Q38 34 28 38 Z" fill="#1a1a1a" />
      {/* Curly bumps */}
      {[[34, 22], [42, 18], [50, 16], [58, 18], [66, 22]].map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={5} fill="#1a1a1a" />
      ))}
      {[[30, 28], [38, 20], [50, 17], [62, 20], [70, 28]].map(([x, y], i) => (
        <circle key={`b${i}`} cx={x} cy={y} r={4} fill="#1a1a1a" />
      ))}

      {/* Eyes — playful */}
      <ellipse cx="42" cy="44" rx="3" ry="3.5" fill="#1a1a1a" />
      <ellipse cx="58" cy="44" rx="3" ry="3.5" fill="#1a1a1a" />
      <circle cx="43.5" cy="43" r="1.2" fill="white" />
      <circle cx="59.5" cy="43" r="1.2" fill="white" />

      {/* One raised eyebrow */}
      <path d="M37 37 Q42 34 46 37" stroke="#1a1a1a" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      <path d="M54 36 Q58 33 63 37" stroke="#1a1a1a" strokeWidth="1.5" fill="none" strokeLinecap="round" />

      {/* Nose */}
      <path d="M48 48 Q50 51 52 48" stroke="#c8a060" strokeWidth="1" fill="none" />

      {/* Big grin */}
      <path d="M42 52 Q50 60 58 52" stroke="#a05050" strokeWidth="2" fill="none" strokeLinecap="round" />
      <path d="M45 54 L55 54" stroke="white" strokeWidth="1.5" />

      {/* Blush */}
      <ellipse cx="37" cy="50" rx="4" ry="2.5" fill="#e5c07b33" />
      <ellipse cx="63" cy="50" rx="4" ry="2.5" fill="#e5c07b33" />

      {/* Phone */}
      <rect x="72" y="70" width="8" height="12" rx="2" fill="#333" />
      <rect x="73" y="71" width="6" height="9" rx="1" fill="#4a8abd" />
    </g>
  );
}
