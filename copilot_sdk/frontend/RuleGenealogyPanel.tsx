import { useEffect, useState } from "react";

export interface RuleGenealogyPanelProps { baseUrl?: string; }

export default function RuleGenealogyPanel({ baseUrl = "/api/self" }: RuleGenealogyPanelProps) {
  const [total, setTotal] = useState(0);
  useEffect(() => { fetch(`${baseUrl}/rule-genealogy`).then((response) => response.json()).then((value: { total?: unknown }) => setTotal(typeof value.total === "number" ? value.total : 0)); }, [baseUrl]);
  return <section data-testid="rule-genealogy-panel" className="copilot-card p-4"><h2 className="text-base font-semibold">Rule Genealogy</h2><p>Evolution lineage from GraphStore state.</p><div>{total} evolution records</div></section>;
}
