import { useEffect, useState } from "react";
import { EvolutionPanel } from "../../../../../copilot_sdk/frontend";
import { getAeImpact, getEvolutionVariants, getPatternOrigin } from "../api";
import AEImpactPanel from "../components/AEImpactPanel";
import AuditTrailViewer from "../components/AuditTrailViewer";
import OperationalRulesPanel from "../components/OperationalRulesPanel";
import PatternOriginCard from "../components/PatternOriginCard";
import RuleGenealogyTree from "../components/RuleGenealogyTree";
import RuleLifecyclePanel from "../components/RuleLifecyclePanel";
import SchemaImpactPanel from "../components/SchemaImpactPanel";
import type { AEImpact, EvolutionVariant, PatternOrigin } from "../types";

export default function EvidenceScreen() {
  const [variants, setVariants] = useState<EvolutionVariant[]>([]);
  const [origin, setOrigin] = useState<PatternOrigin | null>(null);
  const [impact, setImpact] = useState<AEImpact | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
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

  return (
    <div className="grid gap-4">
      {error ? <Frame message={error} tone="error" /> : null}
      <AEImpactPanel impact={impact} />
      <EvolutionPanel variants={variants} title="AgentEvolver Audit Trail" />
      <RuleGenealogyTree />
      <RuleLifecyclePanel />
      <AuditTrailViewer />
      <SchemaImpactPanel />
      <OperationalRulesPanel />
      <PatternOriginCard origin={origin} />
    </div>
  );
}

function Frame({ message, tone = "muted" }: { message: string; tone?: "muted" | "error" }) {
  return (
    <section className="copilot-card p-6 text-sm" style={{ color: tone === "error" ? "var(--copilot-danger)" : "var(--copilot-text-muted)" }}>
      {message}
    </section>
  );
}
