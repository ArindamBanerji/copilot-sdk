import { useEffect, useState } from "react";
import { fetchPromotionStatus, getNoveltyStatus } from "../api";
import type { ConfidenceBand, PromotionRecord } from "../types";
import ProvenanceBadge from "./ProvenanceBadge";

function bands(records: PromotionRecord[], novelty: unknown): ConfidenceBand[] {
  const noveltyRecord = novelty && typeof novelty === "object" ? novelty as Record<string, unknown> : {};
  const globalNovelty = typeof noveltyRecord.novelty_score === "number" ? noveltyRecord.novelty_score : 0;
  return records.map((record) => {
    const raw = record.confidence;
    const confidence = typeof raw === "number" ? raw : Math.max(0, Math.min(1, 1 - globalNovelty));
    const rising = globalNovelty > 0.5 || record.current_stage === "rolled_back";
    return { category: record.decision_class, confidence, novelty: globalNovelty, status: rising ? "novelty rising; review" : "within learned range", evidence_tier: record.evidence_tier };
  });
}

export function ConfidenceBandPanel() {
  const [items, setItems] = useState<ConfidenceBand[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchPromotionStatus(), getNoveltyStatus()]).then(([promotion, novelty]) => { if (!cancelled) setItems(bands(promotion?.categories ?? [], novelty)); }).finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);
  return <article data-testid="confidence-band-panel" className="copilot-card p-5">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-wide text-amber-700">S2P-CONFIDENCE</p><h2 className="mt-1 text-lg font-semibold text-slate-950">Confidence, always visible</h2><p className="mt-1 text-sm text-slate-600">Authority expands only while confidence and novelty remain legible.</p></div><ProvenanceBadge source="context" /></div>
    {loading ? <p className="mt-5 text-sm text-slate-500">Loading confidence bands...</p> : items.length === 0 ? <p className="mt-5 rounded-md bg-slate-50 p-4 text-sm text-slate-600">Confidence bands will appear after category records load.</p> : <div className="mt-5 space-y-3">{items.map((item) => <div key={item.category} className="rounded-lg border border-slate-200 p-3"><div className="flex justify-between text-sm"><span className="font-medium text-slate-900">{item.category}</span><span className="font-semibold text-slate-700">{Math.round(item.confidence * 100)}%</span></div><div className="mt-2 h-2 rounded-full bg-slate-100"><div className={`h-2 rounded-full ${item.confidence < 0.6 ? "bg-rose-500" : "bg-emerald-500"}`} style={{ width: `${Math.max(0, Math.min(100, item.confidence * 100))}%` }} /></div><p className="mt-2 text-xs text-slate-500">{item.status}{item.status.startsWith("novelty") ? "; auto-approve paused itself" : ""}</p></div>)}</div>}
  </article>;
}

export default ConfidenceBandPanel;
