import { useEffect, useState } from "react";

export interface AuditTrailPanelProps { baseUrl?: string; limit?: number; }

export default function AuditTrailPanel({ baseUrl = "/api/self", limit = 50 }: AuditTrailPanelProps) {
  const [total, setTotal] = useState(0);
  useEffect(() => { fetch(`${baseUrl}/audit-trail?limit=${limit}`).then((response) => response.json()).then((value: { total?: unknown }) => setTotal(typeof value.total === "number" ? value.total : 0)); }, [baseUrl, limit]);
  return <section data-testid="audit-trail-panel" className="copilot-card p-4"><h2 className="text-base font-semibold">Audit Trail</h2><p>Immutable ledger entries for this domain.</p><div>{total} entries</div></section>;
}
