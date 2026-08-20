import { useEffect, useState } from "react";
import { getAlertGroups, getCrossGraphInsight } from "../api";
import type { ApplyFixConservationCheck, ApplyFixResponse, CrossGraphInsightResponse } from "../types";
import ApplyFixModal from "./ApplyFixModal";
import { CrossGraphInsightCard } from "./CrossGraphInsightCard";

const DEFAULT_ALERT_ID = "ALERT-TIRE-001";
const PREVIEW: ApplyFixConservationCheck = {
  status: "GREEN",
  currentAutomation: 0.35,
  projectedAutomation: 0.38,
  thetaMin: 0.42,
  safe: true,
};

export default function FusionClimaxPanel() {
  const [alertId, setAlertId] = useState<string | null>(null);
  const [insight, setInsight] = useState<CrossGraphInsightResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const candidates = [DEFAULT_ALERT_ID];
      try {
        const groups = await getAlertGroups();
        const grouped = groups.groups?.flatMap((group) => group.alerts || []) || [];
        const ungrouped = groups.ungrouped || [];
        for (const alert of [...grouped, ...ungrouped]) {
          const id = alert.alertId || alert.alert_id;
          if (id && !candidates.includes(id)) candidates.push(id);
        }
      } catch {
        // The known demo alert remains the deterministic fallback.
      }
      for (const candidate of candidates) {
        const result = await getCrossGraphInsight(candidate);
        if (result) {
          if (!cancelled) {
            setAlertId(result.alertId || candidate);
            setInsight(result);
            setLoading(false);
          }
          return;
        }
      }
      if (!cancelled) setLoading(false);
    }
    void load();
    return () => { cancelled = true; };
  }, []);

  const monthlyCost = insight?.combinedImpact?.monthlyCost;
  const formatMoney = (value?: number) => typeof value === "number"
    ? new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value)
    : "pending";
  const applyAlertId = alertId || DEFAULT_ALERT_ID;
  const supplier = insight?.rootCause?.upstreamSupplier || "upstream supplier";

  return (
    <section className="copilot-card p-5" data-testid="fusion-climax-panel">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="dataops-kicker">E5 · Process-tech fusion climax</p>
          <h2 className="dataops-title">Celonis sees where. SAP sees what. The graph answers why.</h2>
          <p className="mt-1 text-sm dataops-muted">Cross-graph evidence resolves the operational cost before the fix is written back.</p>
        </div>
        <span className="rounded-full bg-purple-500/15 px-3 py-1 text-xs font-semibold text-purple-200">Celonis · SAP · Graph</span>
      </div>
      {loading ? <p className="mt-4 text-sm dataops-muted">Correlating process, ERP, and graph signals...</p> : null}
      {!loading && !insight ? <p className="mt-4 text-sm" style={{ color: "var(--copilot-danger)" }}>Cross-graph insight unavailable.</p> : null}
      {insight && alertId ? (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-3" data-testid="fusion-source-summary">
            <Metric label="Process signal" value={insight.processSignal?.activity || "Celonis bottleneck"} />
            <Metric label="ERP impact" value={`${insight.erpImpact?.affectedPos ?? 0} POs affected`} />
            <Metric label="Why-now" value={insight.rootCause?.field || "Graph-correlated cause"} />
          </div>
          <div className="mt-4 rounded-md border border-amber-300/30 bg-amber-500/10 p-4" data-testid="fusion-monthly-impact">
            <div className="text-xs font-semibold uppercase tracking-[0.16em] text-amber-200">$/month resolved</div>
            <div className="mt-1 text-3xl font-bold text-amber-100">{formatMoney(monthlyCost)}</div>
            <p className="mt-1 text-sm text-amber-100/75">{insight.sourcesUsed?.length || 0} independent sources agree · {Math.round((insight.combinedImpact?.confidence || 0) * 100)}% confidence</p>
          </div>
          <div className="mt-4" data-testid="fusion-cross-graph-result"><CrossGraphInsightCard alertId={alertId} /></div>
          <button type="button" className="copilot-button mt-4 px-3 py-2 text-sm" data-testid="fusion-apply-fix" onClick={() => setOpen(true)}>
            Apply governed fix to SAP
          </button>
          <ApplyFixModal
            open={open}
            alertId={applyAlertId}
            option="apply_pre_join_filter"
            optionLabel="Apply pre-join filter on MATKL_V2 range"
            entityId={String(insight.erpImpact?.affectedPos ? `PO-${insight.erpImpact.affectedPos}` : `PO-${applyAlertId}`)}
            supplier={supplier}
            matchingParameter={insight.rootCause?.field || "MATKL_V2"}
            conservationPreview={PREVIEW}
            onClose={() => setOpen(false)}
            onApplied={(_response: ApplyFixResponse) => undefined}
          />
        </>
      ) : null}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}><div className="text-xs uppercase dataops-muted">{label}</div><div className="mt-1 text-sm font-semibold">{value}</div></div>;
}
