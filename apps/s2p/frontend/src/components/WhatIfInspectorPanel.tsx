import { useState } from "react";
import { apiPost } from "../api";
import ProvenanceBadge from "./ProvenanceBadge";

type Probe = { factor: string; current: number; perturbed: number };
type Result = Probe & { delta: number | null; action?: string };
const PROBES: Probe[] = [
  { factor: "amount_variance_ratio", current: 0.052, perturbed: 0.048 },
  { factor: "supplier_exception_history", current: 0.5, perturbed: 0.8 },
  { factor: "commodity_index_correlation", current: 0.4, perturbed: 0.1 },
];

export function WhatIfInspectorPanel() {
  const [results, setResults] = useState<Result[]>([]);
  const [loading, setLoading] = useState(false);
  async function inspect() {
    setLoading(true);
    const response = await apiPost<Record<string, unknown>>("/api/s2p/score/counterfactual", { factors: PROBES.map((probe) => probe.current), perturbations: PROBES.map((probe) => ({ factor: probe.factor, value: probe.perturbed })) }).catch(() => null);
    const raw = Array.isArray(response?.results) ? response.results : [];
    setResults(PROBES.map((probe, index) => { const item = raw[index] as Record<string, unknown> | undefined; const delta = typeof item?.delta === "number" ? item.delta : null; return { ...probe, delta, action: typeof item?.action === "string" ? item.action : undefined }; }));
    setLoading(false);
  }
  return <article data-testid="what-if-inspector-panel" className="copilot-card p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-wide text-amber-700">S2P-WHATIF</p><h2 className="mt-1 text-lg font-semibold text-slate-950">What would change this decision?</h2><p className="mt-1 text-sm text-slate-600">Probe one factor at a time and inspect the boundary rather than guessing.</p></div><ProvenanceBadge source="context" /></div><button type="button" onClick={inspect} disabled={loading} className="mt-4 rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white disabled:opacity-50">{loading ? "Inspecting..." : "Inspect factor boundaries"}</button>{results.length === 0 ? <p className="mt-4 text-sm text-slate-500">Run the inspector to calculate flip conditions from the scoring endpoint.</p> : <div className="mt-4 space-y-3">{results.map((result) => <div key={result.factor} className="rounded-lg border border-slate-200 p-3"><p className="text-sm font-medium text-slate-900">If {result.factor} moves from {result.current.toFixed(3)} to {result.perturbed.toFixed(3)}</p><p className="mt-1 text-xs text-slate-600">{result.delta === null ? "No boundary delta returned." : `Computed score change: ${result.delta >= 0 ? "+" : ""}${result.delta.toFixed(3)}${result.action ? ` · action: ${result.action}` : ""}`}</p></div>)}</div>}</article>;
}

export default WhatIfInspectorPanel;
