import { useEffect, useMemo, useState } from "react";
import { FingerprintPanel } from "../../../../../copilot_sdk/frontend";
import { getFingerprint, getIncident } from "../api";
import AcquisitionPanel from "../components/AcquisitionPanel";
import AcquisitionAdvisorPanel from "../components/AcquisitionAdvisorPanel";
import BottleneckPanel from "../components/BottleneckPanel";
import { CrossGraphInsightCard } from "../components/CrossGraphInsightCard";
import CompoundingCurveOverlay from "../components/CompoundingCurveOverlay";
import CentroidTimelinePanel from "../components/CentroidTimelinePanel";
import DecisionExplorerPanel from "../components/DecisionExplorerPanel";
import FusionClimaxPanel from "../components/FusionClimaxPanel";
import IncidentReplayCard from "../components/IncidentReplayCard";
import EarnedProofPanel from "../components/EarnedProofPanel";
import { IntelligenceMapPanel } from "../components/IntelligenceMapPanel";
import { ProcessTimelinePanel } from "../components/ProcessTimelinePanel";
import ProfileArchetype from "../components/ProfileArchetype";
import SourceProfilePanel from "../components/SourceProfilePanel";
import SourceCompoundingPanel from "../components/SourceCompoundingPanel";
import SearchPanel from "../components/SearchPanel";
import WhatIfReordering from "../components/WhatIfReordering";
import type { FingerprintResponse, Incident } from "../types";

const factorDisplay: Record<string, { displayName: string; interpretation: string }> = {
  recurrence_frequency: {
    displayName: "Recurrence frequency",
    interpretation: "Recurring alerts are the system's strongest pattern signal.",
  },
  business_criticality: {
    displayName: "Business criticality",
    interpretation: "High-value systems require stricter decisions and fewer shortcuts.",
  },
  impact_scope: {
    displayName: "Impact scope",
    interpretation: "Downstream blast radius determines escalation pressure.",
  },
  downstream_urgency: {
    displayName: "Downstream urgency",
    interpretation: "Tight SLAs turn data quality issues into operational incidents.",
  },
  source_reliability: {
    displayName: "Source reliability",
    interpretation: "Unreliable sources are a blind spot when they appear narrow.",
  },
  data_freshness: {
    displayName: "Data freshness",
    interpretation: "Freshness is noisy alone, but important when paired with urgency.",
  },
};

export default function InsightScreen() {
  const [fingerprint, setFingerprint] = useState<FingerprintResponse | null>(null);
  const [incident, setIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);
  const [criticalLoaded, setCriticalLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setCriticalLoaded(false);
    setError(null);
    Promise.all([getFingerprint(), getIncident()])
      .then(([fingerprintResult, incidentResult]) => {
        if (!cancelled) {
          setFingerprint(fingerprintResult);
          setIncident(incidentResult);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Could not load insight data.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setCriticalLoaded(true);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const factors = useMemo(
    () =>
      (fingerprint?.factors || []).map((factor) => ({
        ...factor,
        displayName: factorDisplay[factor.name]?.displayName || factor.displayName || factor.name,
        interpretation: factorDisplay[factor.name]?.interpretation || factor.interpretation,
      })),
    [fingerprint],
  );

  if (loading) {
    return <Frame message="Loading DataOps insight..." />;
  }

  const dataReady = criticalLoaded && !loading;

  return (
    <div data-screen-ready={String(dataReady)} className="grid gap-4">
      {error ? <Frame message={error} tone="error" /> : null}
      <ProfileArchetype factors={factors} />
      <FingerprintPanel
        factors={factors}
        signalLabel="YOUR GRAPH SIGNAL"
        noiseLabel="YOUR BLIND SPOTS"
        perCategoryPrecision={fingerprint?.perCategoryPrecision}
        decisionsAnalyzed={fingerprint?.decisionsAnalyzed}
      />
      <IncidentReplayCard incident={incident} />
      <BottleneckPanel />
      <ProcessTimelinePanel />
      <AcquisitionPanel />
      <EarnedProofPanel />
      <AcquisitionAdvisorPanel />
      <SourceCompoundingPanel />
      <IntelligenceMapPanel />
      <CrossGraphInsightCard />
      <FusionClimaxPanel />
      <CompoundingCurveOverlay />
      <WhatIfReordering />
      <CentroidTimelinePanel />
      <SourceProfilePanel />
      <SearchPanel />
      <DecisionExplorerPanel />
    </div>
  );
}

function Frame({ message, tone = "muted" }: { message: string; tone?: "muted" | "error" }) {
  return (
    <section data-screen-ready="false" className="copilot-card p-6 text-sm" style={{ color: tone === "error" ? "var(--copilot-danger)" : "var(--copilot-text-muted)" }}>
      {message}
    </section>
  );
}
