import { useEffect, useState } from "react";

export interface RuleLifecyclePanelProps { ruleId: string; baseUrl?: string; }

export default function RuleLifecyclePanel({ ruleId, baseUrl = "/api/self" }: RuleLifecyclePanelProps) {
  const [hasEvolution, setHasEvolution] = useState(false);
  const [hasPromotion, setHasPromotion] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  useEffect(() => { setLoading(true); setError(false); fetch(`${baseUrl}/rule-lifecycle/${encodeURIComponent(ruleId)}`, { signal: AbortSignal.timeout(10_000) }).then((response) => { if (!response.ok) throw new Error("Rule lifecycle unavailable"); return response.json(); }).then((value: { evolution?: unknown; promotion?: unknown }) => { setHasEvolution(value.evolution !== null && value.evolution !== undefined); setHasPromotion(value.promotion !== null && value.promotion !== undefined); }).catch(() => setError(true)).finally(() => setLoading(false)); }, [baseUrl, ruleId]);
  return <section data-testid="rule-lifecycle-panel" data-panel-ready={String(!loading)} className="copilot-card p-4"><h2 className="text-base font-semibold">Rule Lifecycle</h2><p>{ruleId}</p><div>{error ? "Rule lifecycle unavailable" : `Evolution: ${hasEvolution ? "recorded" : "not recorded"} · Promotion: ${hasPromotion ? "recorded" : "not recorded"}`}</div></section>;
}
