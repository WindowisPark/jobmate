import { useOfficeStore } from "@/stores/officeStore";
import { AGENTS } from "@/types/agent";
import type { AgentId } from "@/types/agent";

const TILE_SIZE = 48;
const OFFICE_COLS = 12;
const OFFICE_ROWS = 8;

export function OfficeView() {
  const { agents } = useOfficeStore();

  return (
    <div
      style={{
        height: OFFICE_ROWS * TILE_SIZE,
        background: "#2b2d31",
        borderBottom: "1px solid #383a3f",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Grid background */}
      <div
        style={{
          width: OFFICE_COLS * TILE_SIZE,
          height: OFFICE_ROWS * TILE_SIZE,
          margin: "0 auto",
          position: "relative",
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)",
          backgroundSize: `${TILE_SIZE}px ${TILE_SIZE}px`,
        }}
      >
        {/* Agent sprites (placeholder) */}
        {(Object.keys(agents) as AgentId[]).map((agentId) => {
          const state = agents[agentId]!;
          const profile = AGENTS[agentId];
          return (
            <div
              key={agentId}
              style={{
                position: "absolute",
                left: state.position.x * TILE_SIZE,
                top: state.position.y * TILE_SIZE,
                width: TILE_SIZE,
                height: TILE_SIZE,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                transition: "left 0.5s, top 0.5s",
              }}
            >
              {/* Status bubble */}
              <div
                style={{
                  fontSize: 10,
                  color: "#9a9b9d",
                  background: "#383a3f",
                  borderRadius: 4,
                  padding: "1px 4px",
                  marginBottom: 2,
                  whiteSpace: "nowrap",
                }}
              >
                {state.action === "idle" ? profile.name : `${profile.name} - ${state.action}`}
              </div>
              {/* Placeholder sprite */}
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: "50%",
                  background: "#007a5a",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 14,
                  color: "white",
                }}
              >
                {profile.name[0]}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
