import { useEffect, useState } from "react";
import { EvolutionPanel } from "../../../../../copilot_sdk/frontend";
import { getAeImpact, getEvolutionVariants, getPatternOrigin } from "../api";
import AEImpactPanel from "../components/AEImpactPanel";
import AuditTrailPanel from "../components/AuditTrailPanel";
import AuditTrailViewer from "../components/AuditTrailViewer";
import AccuracyAlertsPanel from "../components/AccuracyAlertsPanel";
import CohortStatusPanel from "../components/CohortStatusPanel";
import CrossSystemPanel from "../components/CrossSystemPanel";
import OperationalRulesPanel from "../components/OperationalRulesPanel";
import PatternOriginCard from "../components/PatternOriginCard";
import RuleGenealogyTree from "../components/RuleGenealogyTree";
import RuleGenealogyPanel from "../components/RuleGenealogyPanel";
import RuleLifecyclePanel from "../components/RuleLifecyclePanel";
import SchemaImpactPanel from "../components/SchemaImpactPanel";
import TransferStatusPanel from "../components/TransferStatusPanel";
import DataOpsGovernancePanel from "../components/DataOpsGovernancePanel";
import type { AEImpact, EvolutionVariant, PatternOrigin } from "../types";

export default function EvidenceScreen() {
  const [variants, setVariants] = useState<EvolutionVariant[]>([]);
  const [origin, setOrigin] = useState<PatternOrigin | null>(null);
  const [impact, setImpact] = useState<AEImpact | null>(null);
  const [loading, setLoading] = useState(true);
  const [criticalLoaded, setCriticalLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setCriticalLoaded(false);
    setError(null);
    Promise.all([getEvolutionVariants(), getPatternOrigin(), getAeImpact()])
      .then(([variantResult, originResult, impactResult]) => {
        if (!cancelled) {
          setVariants(variantResult);
          setOrigin(originResult);
          setImpact(impactResult);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Could not load evidence data.");
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

  if (loading) {
    return <Frame message="Loading evolution evidence..." />;
  }

  const dataReady = criticalLoaded && !loading;

  return (
    <div data-screen-ready={String(dataReady)} className="grid gap-4">
      {error ? <Frame message={error} tone="error" /> : null}
      <CohortStatusPanel />
      <DataOpsGovernancePanel />
      <CrossSystemPanel />
      <AEImpactPanel impact={impact} />
      <EvolutionPanel variants={variants} title="AgentEvolver Audit Trail" />
      <RuleGenealogyTree />
      <AuditTrailViewer />
      <SchemaImpactPanel />
      <OperationalRulesPanel />
      <AccuracyAlertsPanel />
      <RuleGenealogyPanel />
      <RuleLifecyclePanel />
      <PatternOriginCard origin={origin} />
      <TransferStatusPanel />
      <AuditTrailPanel />
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
