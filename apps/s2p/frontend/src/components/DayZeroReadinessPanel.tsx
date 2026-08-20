import { useEffect, useState } from "react";
import { getPreviewConservation, getPreviewQueue } from "../api";
import type { ConservationStatus, PreviewQueueResponse } from "../types";
import ProvenanceBadge from "./ProvenanceBadge";

export function DayZeroReadinessPanel() {
  const [queue, setQueue] = useState<PreviewQueueResponse | null>(null);
  const [conservation, setConservation] = useState<ConservationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => { let cancelled = false; Promise.all([getPreviewQueue(), getPreviewConservation()]).then(([q, c]) => { if (!cancelled) { setQueue(q); setConservation(c); } }).finally(() => { if (!cancelled) setLoading(false); }); return () => { cancelled = true; }; }, []);
  const total = queue?.total ?? queue?.exceptions?.length ?? 0;
  const verified = conservation?.verified_decisions ?? conservation?.verifiedDecisions ?? 0;
  const coverage = total > 0 ? "Preview queue present" : "No preview queue loaded";
  return <article data-testid="day-zero-readiness-panel" className="copilot-card border-amber-200 bg-amber-50/40 p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-wide text-amber-700">S2P-DAY0</p><h2 className="mt-1 text-lg font-semibold text-slate-950">Day-zero data readiness</h2><p className="mt-2 max-w-2xl text-sm font-medium text-slate-800">Day one we don’t hand you a number. We hand you the truth about your data.</p></div><ProvenanceBadge source="context" /></div>{loading ? <p className="mt-5 text-sm text-slate-500">Checking source coverage...</p> : <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><Readiness label="Source coverage" value={coverage} /><Readiness label="Completeness" value={total > 0 ? `${total} exceptions available` : "Unknown"} /><Readiness label="Provenance" value="Context only" /><Readiness label="Trust tier" value={verified > 0 ? `${verified} verified decisions` : "Needs enrichment"} /></div>}</article>;
}

function Readiness({ label, value }: { label: string; value: string }) { return <div className="rounded-md border border-amber-200 bg-white/80 p-3"><p className="text-xs uppercase tracking-wide text-slate-500">{label}</p><p className="mt-1 text-sm font-semibold text-slate-900">{value}</p></div>; }
export default DayZeroReadinessPanel;
