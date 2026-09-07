import { useEffect, useState } from "react";
import { fetchFrozenTwinStatus, freezeFrozenTwin, getCohortStatus } from "../api";
import type { CohortStatusResponse, FrozenTwinStatus } from "../api";

export default function FrozenTwinControlPanel() {
  const [cohort, setCohort] = useState<CohortStatusResponse | null>(null);
  const [frozenTwin, setFrozenTwin] = useState<FrozenTwinStatus | null>(null);
  const [freezing, setFreezing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { let cancelled = false; Promise.all([getCohortStatus().catch(() => null), fetchFrozenTwinStatus()]).then(([cohortResponse, frozenResponse]) => { if (!cancelled) { setCohort(cohortResponse); setFrozenTwin(frozenResponse); } }); return () => { cancelled = true; }; }, []);
  const frozen = Boolean(frozenTwin?.frozen);
  const measured = cohort?.state === "MEASURED" && typeof cohort.real?.magnitude === "number";
  const baselineLabel = frozen ? "Baseline captured" : "No baseline captured";
  const oracleLabel = cohort?.instrument?.validated ? "Oracle experiment validated" : "Oracle experiment pending";
  const freeze = async () => {
    setFreezing(true);
    setError(null);
    try {
      setFrozenTwin(await freezeFrozenTwin());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Freeze failed");
    } finally {
      setFreezing(false);
    }
  };
  return <article data-testid="frozen-twin-control-panel" className="copilot-card p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-wide text-amber-700">DI-TWIN</p><h2 className="mt-1 text-lg font-semibold" style={{ color: "var(--copilot-text)" }}>Frozen Twin control</h2><p className="mt-1 text-sm dataops-muted">Frozen baseline versus live accumulation; cohort validation remains separate.</p></div><span data-testid="di-twin-modeled-label" className="rounded-full bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800">{measured ? "MEASURED" : "MODELED / PILOT-TARGET"}</span></div><div className="mt-4 grid gap-3 sm:grid-cols-3"><Metric label="Frozen baseline" value={baselineLabel} /><Metric label="Live cohort" value={cohort?.state ?? "Unavailable"} /><Metric label="Instrument check" value={oracleLabel} /></div><div className="mt-4 flex flex-wrap items-center gap-3"><button data-testid="freeze-twin-action" type="button" disabled={freezing || frozen} onClick={freeze} className="rounded-md px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50" style={{ background: "var(--copilot-accent)" }}>{freezing ? "Freezing..." : frozen ? "Baseline locked" : "Capture baseline"}</button>{error ? <span className="text-sm text-rose-300">{error}</span> : null}</div><p className="mt-4 text-sm dataops-muted">{measured ? `Measured divergence: ${cohort?.real?.magnitude}` : "No customer-measured divergence is asserted before the cohort reaches MEASURED."}</p></article>;
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-md bg-white/[0.04] p-3"><p className="text-xs uppercase tracking-wide dataops-muted">{label}</p><p className="mt-1 font-semibold" style={{ color: "var(--copilot-text)" }}>{value}</p></div>; }
