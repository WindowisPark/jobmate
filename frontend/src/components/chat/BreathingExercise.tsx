import { useEffect, useRef, useState } from "react";

interface BreathingStep {
  label: string;
  seconds: number;
}

interface BreathingExerciseProps {
  data: {
    name?: string;
    steps?: BreathingStep[];
    cycles?: number;
    total_minutes?: number;
  };
}

const DEFAULT_478_STEPS: BreathingStep[] = [
  { label: "숨 들이쉬기", seconds: 4 },
  { label: "숨 참기", seconds: 7 },
  { label: "숨 내쉬기", seconds: 8 },
];

export default function BreathingExercise({ data }: BreathingExerciseProps) {
  const steps = data.steps?.length ? data.steps : DEFAULT_478_STEPS;
  const cycles = data.cycles || 3;
  const name = data.name || "호흡 운동";

  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [currentCycle, setCurrentCycle] = useState(0);
  const [countdown, setCountdown] = useState(0);
  const [isFinished, setIsFinished] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const start = () => {
    setIsRunning(true);
    setIsFinished(false);
    setCurrentStep(0);
    setCurrentCycle(0);
    setCountdown(steps[0]!.seconds);
    runTimer(0, 0, steps[0]!.seconds);
  };

  const stop = () => {
    setIsRunning(false);
    if (timerRef.current) clearInterval(timerRef.current);
  };

  const runTimer = (step: number, cycle: number, seconds: number) => {
    if (timerRef.current) clearInterval(timerRef.current);
    let remaining = seconds;
    setCountdown(remaining);

    timerRef.current = setInterval(() => {
      remaining -= 1;
      if (remaining <= 0) {
        // 다음 스텝
        const nextStep = step + 1;
        if (nextStep < steps.length) {
          setCurrentStep(nextStep);
          setCountdown(steps[nextStep]!.seconds);
          runTimer(nextStep, cycle, steps[nextStep]!.seconds);
        } else {
          // 다음 사이클
          const nextCycle = cycle + 1;
          if (nextCycle < cycles) {
            setCurrentCycle(nextCycle);
            setCurrentStep(0);
            setCountdown(steps[0]!.seconds);
            runTimer(0, nextCycle, steps[0]!.seconds);
          } else {
            // 완료
            if (timerRef.current) clearInterval(timerRef.current);
            setIsRunning(false);
            setIsFinished(true);
          }
        }
      } else {
        setCountdown(remaining);
      }
    }, 1000);
  };

  // 원 크기 계산 (단계별)
  const getCircleScale = () => {
    if (!isRunning) return 1;
    const step = steps[currentStep];
    if (!step) return 1;
    const progress = 1 - countdown / step.seconds;
    if (step.label.includes("들이쉬")) return 0.6 + progress * 0.4;
    if (step.label.includes("내쉬")) return 1.0 - progress * 0.4;
    return 1.0; // 참기
  };

  const circleScale = getCircleScale();
  const stepLabel = steps[currentStep]?.label || "";

  return (
    <div
      style={{
        background: "var(--bg-tertiary)",
        borderRadius: "var(--radius-lg)",
        padding: "20px",
        margin: "8px 0",
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: "var(--font-sm)", color: "var(--text-secondary)", marginBottom: 8 }}>
        {name}
      </div>

      {/* 호흡 원 */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: 140,
        }}
      >
        <div
          style={{
            width: 120 * circleScale,
            height: 120 * circleScale,
            borderRadius: "50%",
            background: isRunning
              ? "radial-gradient(circle, rgba(152,195,121,0.3), rgba(152,195,121,0.1))"
              : "radial-gradient(circle, rgba(152,195,121,0.15), rgba(152,195,121,0.05))",
            border: `2px solid ${isRunning ? "#98c379" : "var(--border)"}`,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            transition: "width 1s ease, height 1s ease, background 0.5s ease",
          }}
        >
          {isRunning ? (
            <>
              <div style={{ fontSize: 24, fontWeight: 700, color: "#98c379" }}>
                {countdown}
              </div>
              <div style={{ fontSize: "var(--font-sm)", color: "var(--text-secondary)", marginTop: 4 }}>
                {stepLabel}
              </div>
            </>
          ) : isFinished ? (
            <div style={{ fontSize: "var(--font-sm)", color: "#98c379" }}>
              완료!
            </div>
          ) : (
            <div style={{ fontSize: "var(--font-sm)", color: "var(--text-secondary)" }}>
              시작하기
            </div>
          )}
        </div>
      </div>

      {/* 사이클 표시 */}
      {isRunning && (
        <div style={{ fontSize: "var(--font-sm)", color: "var(--text-secondary)", marginTop: 8 }}>
          {currentCycle + 1} / {cycles} 사이클
        </div>
      )}

      {/* 시작/중지 버튼 */}
      <button
        onClick={isRunning ? stop : start}
        style={{
          marginTop: 12,
          padding: "8px 24px",
          borderRadius: "var(--radius-md)",
          border: "none",
          background: isRunning ? "rgba(224,108,117,0.2)" : "rgba(152,195,121,0.2)",
          color: isRunning ? "#e06c75" : "#98c379",
          cursor: "pointer",
          fontSize: "var(--font-sm)",
          fontWeight: 600,
        }}
      >
        {isRunning ? "중지" : isFinished ? "다시 하기" : "시작"}
      </button>
    </div>
  );
}
