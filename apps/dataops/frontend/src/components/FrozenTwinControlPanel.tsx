import { useEffect, useState } from "react";
import { getCohortStatus } from "../api";
import type { CohortStatusResponse } from "../api";

export default function FrozenTwinControlPanel() {
  const [cohort, setCohort] = useState<CohortStatusResponse | null>(null);
  useEffect(() => { let cancelled = false; getCohortStatus().then((response) => { if (!cancelled) setCohort(response); }).catch(() => { if (!cancelled) setCohort(null); }); return () => { cancelled = true; }; }, []);
  const frozen = Boolean(cohort?.instrument?.validated);
  const measured = cohort?.state === "MEASURED" && typeof cohort.real?.magnitude === "number";
  return <article data-testid="frozen-twin-control-panel" className="copilot-card p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-wide text-amber-700">DI-TWIN</p><h2 className="mt-1 text-lg font-semibold" style={{ color: "var(--copilot-text)" }}>Frozen Twin control</h2><p className="mt-1 text-sm dataops-muted">Frozen checkpoint versus live accumulation; the gap is the value of compounding.</p></div><span data-testid="di-twin-modeled-label" className="rounded-full bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800">{measured ? "MEASURED" : "MODELED / PILOT-TARGET"}</span></div><div className="mt-4 grid gap-3 sm:grid-cols-2"><Metric label="Frozen checkpoint" value={frozen ? "Pinned" : "Pending"} /><Metric label="Live arm" value={cohort?.state ?? "Unavailable"} /></div><p className="mt-4 text-sm dataops-muted">{measured ? `Measured divergence: ${cohort?.real?.magnitude}` : "No customer-measured divergence is asserted before the cohort reaches MEASURED."}</p></article>;
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-md bg-white/[0.04] p-3"><p className="text-xs uppercase tracking-wide dataops-muted">{label}</p><p className="mt-1 font-semibold" style={{ color: "var(--copilot-text)" }}>{value}</p></div>; }
