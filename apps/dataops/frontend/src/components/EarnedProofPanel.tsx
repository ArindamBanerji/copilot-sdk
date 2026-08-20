import { useEffect, useState } from "react";
import { fetchDataOpsTrust, fetchDIProducts } from "../api";
import type { DIProduct, TrustResponse } from "../types";

export default function EarnedProofPanel() {
  const [trust, setTrust] = useState<TrustResponse | null>(null);
  const [products, setProducts] = useState<DIProduct[]>([]);
  const [removed, setRemoved] = useState(false);
  useEffect(() => { let cancelled = false; Promise.all([fetchDataOpsTrust(), fetchDIProducts()]).then(([nextTrust, nextProducts]) => { if (!cancelled) { setTrust(nextTrust); setProducts(nextProducts?.products ?? []); } }); return () => { cancelled = true; }; }, []);
  const current = trust?.overallTrust ?? null;
  const sourceCount = products[0]?.sources?.length ?? 0;
  const delta = removed && current !== null && sourceCount > 0 ? Math.min(0.12, current / sourceCount) : 0;
  const whatIf = current === null ? null : Math.max(0, current - delta);
  return <article data-testid="earned-proof-panel" className="copilot-card p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-wide text-amber-700">DI-PROOF</p><h2 className="mt-1 text-lg font-semibold" style={{ color: "var(--copilot-text)" }}>Earned, not asserted</h2><p className="mt-1 text-sm dataops-muted">Withdraw one source and inspect the trust delta behind the claim.</p></div><span className="rounded-full bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800">MODELLED WHAT-IF</span></div><button type="button" data-testid="earned-proof-toggle" className="copilot-button-secondary mt-4 px-3 py-2 text-sm" onClick={() => setRemoved((value) => !value)}>{removed ? "Restore source" : "Remove source #3"}</button><div className="mt-4 grid gap-3 sm:grid-cols-2"><Metric label="Current trust" value={current === null ? "Unavailable" : current.toFixed(2)} /><Metric label="What-if trust" value={whatIf === null ? "Unavailable" : whatIf.toFixed(2)} /></div>{removed ? <p data-testid="earned-proof-delta" className="mt-3 text-sm dataops-muted">Removing the source changes the computed proxy by {delta.toFixed(2)}. This is a modelled sensitivity, not a measured customer outcome.</p> : null}</article>;
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-md bg-white/[0.04] p-3"><p className="text-xs uppercase tracking-wide dataops-muted">{label}</p><p className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>{value}</p></div>; }
