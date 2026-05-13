import { useEffect, useMemo, useState } from "react";
import { FingerprintPanel, type FactorItem } from "../../../../../copilot_sdk/frontend";
import { getAnalytics, getFingerprint } from "../api";
import AuditTrailViewer from "../components/AuditTrailViewer";
import ContrastCard from "../components/ContrastCard";
import CounterfactualCard from "../components/CounterfactualCard";
import DayOfWeekChart from "../components/DayOfWeekChart";
import DecisionExplorerPanel from "../components/DecisionExplorerPanel";
import ProfileArchetype from "../components/ProfileArchetype";
import RegimeChart from "../components/RegimeChart";
import ResearchImpactChart from "../components/ResearchImpactChart";
import RiskManagementCard from "../components/RiskManagementCard";
import RuleGenealogyTree from "../components/RuleGenealogyTree";
import RuleLifecyclePanel from "../components/RuleLifecyclePanel";
import type { Analytics, FingerprintResponse } from "../types";

const displayNames: Record<string, string> = {
  conviction: "Conviction",
  research_depth: "Research Depth",
  technical_signal: "Technical Signal",
  position_size: "Position Size",
  time_horizon: "Time Horizon",
  market_regime: "Market Regime",
};

function interpretation(name: string, weight: number): string {
  if (name === "conviction" && weight < 0.35) {
    return "Conviction needs confirmation from evidence.";
  }
  if (name === "research_depth") {
    return "Checklist depth is a repeatable edge.";
  }
  if (name === "market_regime") {
    return "Market context changes setup quality.";
  }
  return weight >= 0.6 ? "High-signal factor." : weight >= 0.3 ? "Useful with confirmation." : "Noisy on its own.";
}

function factorItems(fingerprint?: FingerprintResponse): FactorItem[] {
  return (fingerprint?.factors || []).map((factor) => {
    const weight = typeof factor.weight === "number" ? factor.weight : 0;
    return {
      name: factor.name,
      displayName: factor.displayName || displayNames[factor.name] || factor.name.replace(/_/g, " "),
      weight,
      sigma: typeof factor.sigma === "number" ? factor.sigma : 0,
      interpretation: factor.interpretation || interpretation(factor.name, weight),
      category: factor.category,
    };
  });
}

export default function AnalysisScreen() {
  const [analytics, setAnalytics] = useState<Analytics | undefined>();
  const [fingerprint, setFingerprint] = useState<FingerprintResponse | undefined>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [analyticsPayload, fingerprintPayload] = await Promise.all([getAnalytics(), getFingerprint()]);
        if (!cancelled) {
          setAnalytics(analyticsPayload);
          setFingerprint(fingerprintPayload);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Analysis load failed");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const factors = useMemo(() => factorItems(fingerprint), [fingerprint]);

  if (loading) {
    return <div className="copilot-card p-8 text-sm trading-muted">Loading analysis...</div>;
  }

  if (error) {
    return (
      <section className="copilot-card p-6">
        <h2 className="text-xl font-semibold">Analysis unavailable</h2>
        <p className="mt-2 text-sm trading-muted">{error}</p>
      </section>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <ContrastCard analytics={analytics} />
      <ProfileArchetype fingerprint={fingerprint} />
      <FingerprintPanel
        factors={factors}
        signalLabel="YOUR EDGE"
        noiseLabel="YOUR NOISE"
        perCategoryPrecision={fingerprint?.perCategoryPrecision}
        decisionsAnalyzed={fingerprint?.decisionsAnalyzed}
      />
      <DecisionExplorerPanel />
      <CounterfactualCard analytics={analytics} />
      <DayOfWeekChart analytics={analytics} />
      <ResearchImpactChart analytics={analytics} />
      <RegimeChart analytics={analytics} />
      <RiskManagementCard analytics={analytics} />
      <RuleGenealogyTree />
      <RuleLifecyclePanel />
      <AuditTrailViewer />
    </div>
  );
}
