import { useEffect, useMemo, useState } from "react";
import { FingerprintPanel, GovernedVsUngovernedPanel, type FactorItem, type ScoreResult } from "../../../../../copilot_sdk/frontend";
import { fetchPromotion, getAnalytics, getConservationStatus, getFingerprint, prescoreTrade } from "../api";
import ContrastCard from "../components/ContrastCard";
import CorrelationPanel from "../components/CorrelationPanel";
import CounterfactualCard from "../components/CounterfactualPanel";
import DayOfWeekChart from "../components/DayOfWeekChart";
import DecisionExplorer from "../components/DecisionExplorer";
import DispersionFollowCard from "../components/DispersionFollowCard";
import PatternDetectionPanel from "../components/PatternDetectionPanel";
import ProfileArchetype from "../components/ProfileArchetype";
import RegimeChart from "../components/RegimeChart";
import RegimePanel from "../components/RegimePanel";
import RegimeVRPCard from "../components/RegimeVRPCard";
import ResearchImpactChart from "../components/ResearchImpactChart";
import RiskManagementCard from "../components/RiskManagementCard";
import RuleGenealogyTree from "../components/RuleGenealogyTree";
import RuleLifecyclePanel from "../components/RuleLifecyclePanel";
import TailBetsCard from "../components/TailBetsCard";
import TrustRadarPanel from "../components/TrustRadarPanel";
import VolSharpeCard from "../components/VolSharpeCard";
import VolatilityPanel from "../components/VolatilityPanel";
import VRPAttributionCard from "../components/VRPAttributionCard";
import { ClaimGateBadge, RegimeMirrorPanel } from "../components/DemoBeatPanels";
import type { Analytics, FingerprintResponse } from "../types";

const displayNames: Record<string, string> = {
  signal_alignment: "Conviction",
  market_regime: "Research Depth",
  position_sizing: "Technical Signal",
  timing_quality: "Position Size",
  risk_reward_actual: "Time Horizon",
  emotional_indicator: "Market Regime",
};

function interpretation(name: string, weight: number): string {
  if (name === "signal_alignment" && weight < 0.35) {
    return "Conviction needs confirmation from evidence.";
  }
  if (name === "market_regime") {
    return "Checklist depth is a repeatable edge.";
  }
  if (name === "emotional_indicator") {
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
  const [comparison, setComparison] = useState<{
    score: ScoreResult | null;
    conservationStatus?: string;
    evidenceTier?: string;
    promotionState?: string;
  }>({ score: null });
  const factors = useMemo(() => factorItems(fingerprint), [fingerprint]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([
      getAnalytics().catch(() => undefined),
      getFingerprint().catch(() => undefined),
    ])
      .then(([nextAnalytics, nextFingerprint]) => {
        if (cancelled) return;
        setAnalytics(nextAnalytics);
        setFingerprint(nextFingerprint);
        setError(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    Promise.all([getConservationStatus(), fetchPromotion()])
      .then(([conservation, promotion]) => {
        const strategy = promotion?.strategies?.[0];
        setComparison((current) => ({
          ...current,
          conservationStatus: conservation.status,
          promotionState: strategy?.tier || "SHADOW",
        }));
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!fingerprint) return;
    const factors = Object.fromEntries(
      (fingerprint.factors || []).map((factor) => [factor.name, typeof factor.weight === "number" ? factor.weight : 0.5]),
    );
    prescoreTrade({
      category: "trend_following",
      ticker: "SPY",
      direction: "long",
      strategyTag: "trend_following",
      sizePct: 0.1,
    }).then((prescore) => {
      if (!prescore) return;
      const action = prescore.action || prescore.recommendation || "observe";
      setComparison((current) => ({
        ...current,
        evidenceTier: "T_S",
        score: {
          decisionId: "analysis-prescore",
          action,
          actionIndex: 0,
          confidence: typeof prescore.confidence === "number" ? prescore.confidence : 0,
          probabilities: [typeof prescore.confidence === "number" ? prescore.confidence : 0],
          category: prescore.category || "trend_following",
          factors,
          actionNames: [action],
        },
      }));
    }).catch(() => undefined);
  }, [fingerprint]);

  if (loading) {
    return <div data-screen-ready="false" className="copilot-card p-8 text-sm trading-muted">Loading analysis...</div>;
  }

  if (error) {
    return (
      <section data-screen-ready="true" className="copilot-card p-6">
        <h2 className="text-xl font-semibold">Analysis unavailable</h2>
        <p className="mt-2 text-sm trading-muted">{error}</p>
      </section>
    );
  }

  return (
    <div data-screen-ready="true" className="flex flex-col gap-4">
      <TrustRadarPanel />
      <RegimeMirrorPanel />
      <ClaimGateBadge />
      <GovernedVsUngovernedPanel
        scoreResponse={comparison.score}
        copilot="Trading"
        conservationStatus={comparison.conservationStatus}
        evidenceTier={comparison.evidenceTier}
        promotionState={comparison.promotionState}
      />
      <RegimePanel />
      <VolatilityPanel />
      <PatternDetectionPanel />
      <ContrastCard analytics={analytics} />
      <ProfileArchetype fingerprint={fingerprint} />
      <FingerprintPanel
        factors={factors}
        signalLabel="YOUR EDGE"
        noiseLabel="YOUR NOISE"
        perCategoryPrecision={fingerprint?.perCategoryPrecision}
        decisionsAnalyzed={fingerprint?.decisionsAnalyzed}
      />
      <DecisionExplorer />
      <div className="grid gap-4 xl:grid-cols-2" data-testid="vol-analytics-grid">
        <VolSharpeCard />
        <VRPAttributionCard />
        <RegimeVRPCard />
        <DispersionFollowCard />
        <TailBetsCard />
      </div>
      <CorrelationPanel />
      <CounterfactualCard analytics={analytics} />
      <DayOfWeekChart analytics={analytics} />
      <ResearchImpactChart analytics={analytics} />
      <RegimeChart analytics={analytics} />
      <RiskManagementCard analytics={analytics} />
      <RuleGenealogyTree />
      <RuleLifecyclePanel />
    </div>
  );
}
