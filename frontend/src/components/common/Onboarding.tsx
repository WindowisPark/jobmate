import { useState } from "react";
import { AGENTS, AGENT_IDS } from "@/types/agent";

interface Props {
  onComplete: () => void;
}

export function Onboarding({ onComplete }: Props) {
  const [step, setStep] = useState(0);

  const steps = [
    // Step 0: Welcome
    <div key="welcome" style={{ textAlign: "center" }}>
      <div style={{ fontSize: 56, marginBottom: 16 }}>💼</div>
      <h1 style={{ fontSize: 28, fontWeight: 800, color: "var(--text-white)", marginBottom: 8 }}>
        JobMate에 오신 걸 환영해요!
      </h1>
      <p style={{ color: "var(--text-secondary)", fontSize: 16, lineHeight: 1.7, maxWidth: 400, margin: "0 auto" }}>
        취업 준비가 막막하고 힘들 때,<br />
        4명의 전문가 팀이 함께합니다.
      </p>
    </div>,

    // Step 1: Team intro
    <div key="team">
      <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text-white)", textAlign: "center", marginBottom: 24 }}>
        팀을 소개합니다
      </h2>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        {AGENT_IDS.map((id) => {
          const agent = AGENTS[id];
          return (
            <div
              key={id}
              style={{
                background: `${agent.color}11`,
                border: `1px solid ${agent.color}22`,
                borderRadius: 12,
                padding: 16,
                transition: "transform var(--transition-fast)",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.transform = "scale(1.02)")}
              onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1)")}
            >
              <div style={{ fontSize: 28, marginBottom: 8 }}>{agent.emoji}</div>
              <div style={{ color: agent.color, fontWeight: 700, fontSize: 16, marginBottom: 2 }}>
                {agent.name}
              </div>
              <div style={{ color: "var(--text-secondary)", fontSize: 12, marginBottom: 8 }}>
                {agent.role} · {agent.personality}
              </div>
              <div style={{ color: "var(--text-muted)", fontSize: 12, fontStyle: "italic" }}>
                "{agent.greeting}"
              </div>
            </div>
          );
        })}
      </div>
    </div>,

    // Step 2: How to use
    <div key="howto" style={{ textAlign: "center" }}>
      <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text-white)", marginBottom: 24 }}>
        이렇게 사용하세요
      </h2>
      <div style={{ display: "flex", flexDirection: "column", gap: 16, maxWidth: 400, margin: "0 auto" }}>
        {[
          { icon: "💬", title: "# general에서 팀 채팅", desc: "메시지를 보내면 팀원들이 함께 응답해요" },
          { icon: "@", title: "@멘션으로 지목", desc: "@김서연 처럼 특정 멤버를 호출할 수 있어요" },
          { icon: "🔒", title: "1:1 DM", desc: "사이드바에서 이름을 클릭하면 개인 대화가 시작돼요" },
          { icon: "🏢", title: "오피스 뷰", desc: "채팅 위에서 팀원들이 사무실에서 일하는 모습을 볼 수 있어요" },
        ].map((item) => (
          <div
            key={item.title}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 14,
              textAlign: "left",
              padding: "12px 16px",
              background: "var(--bg-tertiary)",
              borderRadius: "var(--radius-lg)",
            }}
          >
            <div style={{ fontSize: 24, width: 40, textAlign: "center", flexShrink: 0 }}>{item.icon}</div>
            <div>
              <div style={{ color: "var(--text-primary)", fontWeight: 600, fontSize: 14 }}>{item.title}</div>
              <div style={{ color: "var(--text-secondary)", fontSize: 13 }}>{item.desc}</div>
            </div>
          </div>
        ))}
      </div>
    </div>,
  ];

  const isLast = step === steps.length - 1;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "var(--bg-primary)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 2000,
      }}
    >
      {/* Content */}
      <div
        style={{
          maxWidth: 560,
          width: "100%",
          padding: "0 24px",
          animation: "fadeIn 0.4s ease",
        }}
        key={step}
      >
        {steps[step]}
      </div>

      {/* Navigation */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          marginTop: 40,
        }}
      >
        {/* Dots */}
        <div style={{ display: "flex", gap: 8 }}>
          {steps.map((_, i) => (
            <div
              key={i}
              style={{
                width: i === step ? 24 : 8,
                height: 8,
                borderRadius: 4,
                background: i === step ? "var(--accent-green)" : "var(--border)",
                transition: "all var(--transition-normal)",
              }}
            />
          ))}
        </div>

        {/* Button */}
        <button
          onClick={() => (isLast ? onComplete() : setStep(step + 1))}
          style={{
            padding: "12px 32px",
            borderRadius: "var(--radius-lg)",
            background: isLast ? "var(--accent-green)" : "var(--bg-tertiary)",
            color: isLast ? "#fff" : "var(--text-primary)",
            border: isLast ? "none" : "1px solid var(--border)",
            fontWeight: 700,
            fontSize: 15,
            cursor: "pointer",
            transition: "all var(--transition-fast)",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.85")}
          onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
        >
          {isLast ? "시작하기 →" : "다음"}
        </button>
      </div>

      {/* Skip */}
      {!isLast && (
        <button
          onClick={onComplete}
          style={{
            marginTop: 16,
            background: "none",
            border: "none",
            color: "var(--text-muted)",
            fontSize: 13,
            cursor: "pointer",
          }}
        >
          건너뛰기
        </button>
      )}
    </div>
  );
}
