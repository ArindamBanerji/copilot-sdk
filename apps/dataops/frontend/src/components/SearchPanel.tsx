import { useEffect, useState } from "react";
import { searchDIAssets } from "../api";
import type { DISearchResponse } from "../types";

const statusTone: Record<string, string> = {
  healthy: "bg-emerald-400/20 text-emerald-200",
  degraded: "bg-amber-400/20 text-amber-200",
  stale: "bg-red-400/20 text-red-200",
};

export default function SearchPanel() {
  const [query, setQuery] = useState("");
  const [tier, setTier] = useState("");
  const [result, setResult] = useState<DISearchResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    const timer = window.setTimeout(() => {
      void searchDIAssets(query, tier ? { trust_tier: tier } : {}).then((payload) => {
        if (!cancelled) setResult(payload);
      }).catch(() => {
        if (!cancelled) setResult(null);
      });
    }, 150);
    return () => { cancelled = true; window.clearTimeout(timer); };
  }, [query, tier]);

  const assets = result?.results || [];
  return (
    <section data-testid="search-panel" className="copilot-card p-5">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-purple-200/75">Quality-aware search</p>
      <h2 className="mt-1 text-xl font-semibold text-white">Find trusted data assets</h2>
      <div className="mt-4 flex flex-wrap gap-2">
        <input data-testid="search-input" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search tables, models, or DAGs" className="min-w-[240px] flex-1 rounded-md border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white" />
        <select data-testid="search-trust-filter" value={tier} onChange={(event) => setTier(event.target.value)} className="rounded-md border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white">
          <option value="">All trust tiers</option><option value="1">Trust tier 1</option><option value="2">Trust tier 2</option><option value="3">Trust tier 3</option>
        </select>
      </div>
      <p data-testid="search-summary" className="mt-3 text-sm dataops-muted">{result?.qualitySummary || "Searching assets..."}</p>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-sm"><thead className="text-xs uppercase dataops-muted"><tr><th className="pb-2">Asset</th><th className="pb-2">Trust</th><th className="pb-2">Freshness</th><th className="pb-2">Quality</th></tr></thead>
          <tbody>{assets.map((asset) => <tr data-testid="search-result" key={asset.assetId} className="border-t border-white/5"><td className="py-2"><span className="font-semibold text-white">{asset.assetName}</span><span className="ml-2 text-xs dataops-muted">{asset.assetType} · {asset.sourceConnector}</span></td><td className="py-2">Tier {asset.trustTier} ({Math.round(asset.trustScore * 100)}%)</td><td className="py-2">{asset.freshnessHours == null ? "—" : `${asset.freshnessHours.toFixed(1)}h`}</td><td className="py-2"><span data-testid="quality-badge" className={`rounded-full px-2 py-1 text-xs ${statusTone[asset.qualityStatus] || statusTone.degraded}`}>{asset.qualityStatus}</span></td></tr>)}</tbody>
        </table>
      </div>
    </section>
  );
}
