import { useEffect, useState } from "react";

export interface RuleLifecyclePanelProps { ruleId: string; baseUrl?: string; }

export default function RuleLifecyclePanel({ ruleId, baseUrl = "/api/self" }: RuleLifecyclePanelProps) {
  const [hasEvolution, setHasEvolution] = useState(false);
  const [hasPromotion, setHasPromotion] = useState(false);
  useEffect(() => { fetch(`${baseUrl}/rule-lifecycle/${encodeURIComponent(ruleId)}`).then((response) => response.json()).then((value: { evolution?: unknown; promotion?: unknown }) => { setHasEvolution(value.evolution !== null && value.evolution !== undefined); setHasPromotion(value.promotion !== null && value.promotion !== undefined); }); }, [baseUrl, ruleId]);
  return <section data-testid="rule-lifecycle-panel" className="copilot-card p-4"><h2 className="text-base font-semibold">Rule Lifecycle</h2><p>{ruleId}</p><div>Evolution: {hasEvolution ? "recorded" : "not recorded"} · Promotion: {hasPromotion ? "recorded" : "not recorded"}</div></section>;
}
