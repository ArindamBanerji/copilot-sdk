import { useEffect, useMemo, useState } from "react";
import FingerprintPanel, { type FactorItem, type FingerprintCategory } from "../../../../../copilot_sdk/frontend/FingerprintPanel";
import { getAnalytics, getFingerprint } from "../api";
import CategoryAccuracyChart from "../components/CategoryAccuracyChart";
import ContrastCard from "../components/ContrastCard";
import CounterfactualCard from "../components/CounterfactualCard";
import DayOfWeekChart from "../components/DayOfWeekChart";
import { DecisionExplorerPanel } from "../components/DecisionExplorerPanel";
import DiscoveryDigestCard from "../components/DiscoveryDigestCard";
import EventImpactCard from "../components/EventImpactCard";
import MenuMatrixCard from "../components/MenuMatrixCard";
import ProfileArchetype from "../components/ProfileArchetype";
import ProvenanceBadge from "../components/ProvenanceBadge";
import TrustRadarPanel from "../components/TrustRadarPanel";
import WasteCostCard from "../components/WasteCostCard";
import { factorDisplayName } from "../factorDisplay";
import type { Analytics, FingerprintFactor, FingerprintResponse } from "../types";
import { GatedSignalReliabilityPanel, MirrorOpenPanel } from "../components/PurchasingBeatPanels";

const interpretations: Record<string, string> = {
  historical_waste: "Items with low waste are your edge; high-waste items need guardrails.",
  day_of_week: "Friday is your blind spot.",
  weather_forecast: "Weather is noisy for your ordering decisions.",
  event_flag: "Events create under-ordering risk.",
  expected_demand: "Your demand estimate is reasonably calibrated.",
  supplier_lead_time: "Lead time matters mostly when stockouts are expensive.",
};

function toFactorItems(fingerprint?: FingerprintResponse): FactorItem[] {
  const factors = fingerprint?.factors;
  if (!factors) {
    return [];
  }
  if (Array.isArray(factors)) {
    return factors.map((factor: FingerprintFactor) => ({
      name: factor.name,
      displayName: factorDisplayName(factor.name),
      weight: Number(factor.weight ?? 0),
      sigma: Number(factor.sigma ?? 0),
      interpretation: interpretations[factor.name] ?? factor.interpretation ?? "Factor precision is still forming.",
      category: factor.category as FingerprintCategory | undefined,
    }));
  }
  return Object.entries(factors).map(([name, weight]) => ({
    name,
    displayName: factorDisplayName(name),
    weight: Number(weight ?? 0),
    sigma: 0,
    interpretation: interpretations[name] ?? "Factor precision is still forming.",
  }));
}

export default function AnalysisScreen() {
  const [analytics, setAnalytics] = useState<Analytics | undefined>();
  const [fingerprint, setFingerprint] = useState<FingerprintResponse | undefined>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | undefined>();

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(undefined);
      try {
        const [nextAnalytics, nextFingerprint] = await Promise.all([getAnalytics(), getFingerprint()]);
        if (mounted) {
          setAnalytics(nextAnalytics);
          setFingerprint(nextFingerprint);
        }
      } catch (caught) {
        if (mounted) {
          setError(caught instanceof Error ? caught.message : "Unable to load analysis");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, []);

  const factors = useMemo(() => toFactorItems(fingerprint), [fingerprint]);

  if (loading) {
    return (
      <div data-screen-ready="false" className="purchase-stack analysis-screen">
        <section className="purchase-card">Loading analysis...</section>
        <MenuMatrixCard />
      </div>
    );
  }

  if (error) {
    return (
      <div data-screen-ready="true" className="purchase-stack analysis-screen">
        <section className="purchase-card error-card">
          <p className="purchase-kicker">Analysis unavailable</p>
          <p>{error}</p>
        </section>
        <MenuMatrixCard />
      </div>
    );
  }

  return (
    <div data-screen-ready="true" className="purchase-stack analysis-screen">
      <div className="flex flex-wrap items-center justify-end gap-2">
        <ProvenanceBadge
          source={String(
            (fingerprint as { source?: string; provenance?: string } | undefined)?.provenance ??
              (fingerprint as { source?: string; provenance?: string } | undefined)?.source ??
              "real_measured",
          )}
        />
      </div>
      <TrustRadarPanel />
      <MirrorOpenPanel />
      <GatedSignalReliabilityPanel />
      <ContrastCard analytics={analytics} />
      <ProfileArchetype fingerprint={fingerprint} />
      <FingerprintPanel
        factors={factors}
        signalLabel="YOUR SIGNAL"
        noiseLabel="YOUR BLIND SPOTS"
        decisionsAnalyzed={fingerprint?.decisionsAnalyzed}
      />
      <DecisionExplorerPanel />
      <CounterfactualCard analytics={analytics} />
      <CategoryAccuracyChart analytics={analytics} />
      <DayOfWeekChart analytics={analytics} />
      <EventImpactCard analytics={analytics} />
      <DiscoveryDigestCard />
      <WasteCostCard analytics={analytics} />
      <MenuMatrixCard />
    </div>
  );
}
