import { useEffect, useState } from "react";

export interface DecisionExplorerPanelProps { baseUrl?: string; category?: string; outcome?: string; }

export default function DecisionExplorerPanel({ baseUrl = "/api/self", category, outcome }: DecisionExplorerPanelProps) {
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  useEffect(() => { const params = new URLSearchParams(); if (category) params.set("category", category); if (outcome) params.set("outcome", outcome); setLoading(true); setError(false); fetch(`${baseUrl}/decisions?${params.toString()}`, { signal: AbortSignal.timeout(10_000) }).then((response) => { if (!response.ok) throw new Error("Decision explorer unavailable"); return response.json(); }).then((value: { total?: unknown }) => setTotal(typeof value.total === "number" ? value.total : 0)).catch(() => setError(true)).finally(() => setLoading(false)); }, [baseUrl, category, outcome]);
  return <section data-testid="decision-explorer-panel" data-panel-ready={String(!loading)} className="copilot-card p-4"><h2 className="text-base font-semibold">Decision Explorer</h2><p>Browse domain-scoped decisions with filters.</p><div>{error ? "Decision explorer unavailable" : `${total} matching decisions`}</div></section>;
}
