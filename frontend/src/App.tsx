import { useState } from "react";
import { Layout } from "@/components/common/Layout";
import { Onboarding } from "@/components/common/Onboarding";

export default function App() {
  const [showOnboarding, setShowOnboarding] = useState(() => {
    return !localStorage.getItem("jobmate_onboarded");
  });

  const handleOnboardingComplete = () => {
    localStorage.setItem("jobmate_onboarded", "true");
    setShowOnboarding(false);
  };

  if (showOnboarding) {
    return <Onboarding onComplete={handleOnboardingComplete} />;
  }

  return <Layout />;
}
