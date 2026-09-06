import { useEffect, useState } from "react";

export interface RuleGenealogyPanelProps { baseUrl?: string; }

export default function RuleGenealogyPanel({ baseUrl = "/api/self" }: RuleGenealogyPanelProps) {
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  useEffect(() => { setLoading(true); setError(false); fetch(`${baseUrl}/rule-genealogy`, { signal: AbortSignal.timeout(10_000) }).then((response) => { if (!response.ok) throw new Error("Rule genealogy unavailable"); return response.json(); }).then((value: { total?: unknown }) => setTotal(typeof value.total === "number" ? value.total : 0)).catch(() => setError(true)).finally(() => setLoading(false)); }, [baseUrl]);
  return <section data-testid="rule-genealogy-panel" data-panel-ready={String(!loading)} className="copilot-card p-4"><h2 className="text-base font-semibold">Rule Genealogy</h2><p>Evolution lineage from GraphStore state.</p><div>{error ? "Rule genealogy unavailable" : `${total} evolution records`}</div></section>;
}
