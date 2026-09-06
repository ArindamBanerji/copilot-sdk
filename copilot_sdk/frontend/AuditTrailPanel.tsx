import { useEffect, useState } from "react";

export interface AuditTrailPanelProps { baseUrl?: string; limit?: number; }

export default function AuditTrailPanel({ baseUrl = "/api/self", limit = 50 }: AuditTrailPanelProps) {
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  useEffect(() => { setLoading(true); setError(false); fetch(`${baseUrl}/audit-trail?limit=${limit}`, { signal: AbortSignal.timeout(10_000) }).then((response) => { if (!response.ok) throw new Error("Audit trail unavailable"); return response.json(); }).then((value: { total?: unknown }) => setTotal(typeof value.total === "number" ? value.total : 0)).catch(() => setError(true)).finally(() => setLoading(false)); }, [baseUrl, limit]);
  return <section data-testid="audit-trail-panel" data-panel-ready={String(!loading)} className="copilot-card p-4"><h2 className="text-base font-semibold">Audit Trail</h2><p>Immutable ledger entries for this domain.</p><div>{error ? "Audit trail unavailable" : `${total} entries`}</div></section>;
}
