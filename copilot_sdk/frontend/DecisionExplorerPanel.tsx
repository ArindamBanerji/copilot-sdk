import { useEffect, useState } from "react";

export interface DecisionExplorerPanelProps { baseUrl?: string; category?: string; outcome?: string; }

export default function DecisionExplorerPanel({ baseUrl = "/api/self", category, outcome }: DecisionExplorerPanelProps) {
  const [total, setTotal] = useState(0);
  useEffect(() => { const params = new URLSearchParams(); if (category) params.set("category", category); if (outcome) params.set("outcome", outcome); fetch(`${baseUrl}/decisions?${params.toString()}`).then((response) => response.json()).then((value: { total?: unknown }) => setTotal(typeof value.total === "number" ? value.total : 0)); }, [baseUrl, category, outcome]);
  return <section data-testid="decision-explorer-panel" className="copilot-card p-4"><h2 className="text-base font-semibold">Decision Explorer</h2><p>Browse domain-scoped decisions with filters.</p><div>{total} matching decisions</div></section>;
}
