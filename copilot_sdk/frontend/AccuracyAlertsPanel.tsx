import { useEffect, useState } from "react";

export interface AccuracyAlertsPanelProps { baseUrl?: string; }
interface AccuracyRow { category?: string; accuracy?: number; alert?: boolean; }

export default function AccuracyAlertsPanel({ baseUrl = "/api/self" }: AccuracyAlertsPanelProps) {
  const [rows, setRows] = useState<AccuracyRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  useEffect(() => { setLoading(true); setError(false); fetch(`${baseUrl}/accuracy-alerts`, { signal: AbortSignal.timeout(10_000) }).then((response) => { if (!response.ok) throw new Error("Accuracy alerts unavailable"); return response.json(); }).then((value: { categories?: unknown }) => setRows(Array.isArray(value.categories) ? value.categories.filter((item): item is AccuracyRow => typeof item === "object" && item !== null) : [])).catch(() => setError(true)).finally(() => setLoading(false)); }, [baseUrl]);
  return <section data-testid="accuracy-alerts-panel" data-panel-ready={String(!loading)} className="copilot-card p-4"><h2 className="text-base font-semibold">Accuracy Alerts</h2>{error ? <p>Accuracy alerts unavailable.</p> : rows.length === 0 ? <p>No category observations available.</p> : <ul>{rows.map((row) => <li key={row.category ?? "uncategorized"}>{row.category ?? "uncategorized"}: {typeof row.accuracy === "number" ? `${Math.round(row.accuracy * 100)}%` : "—"}{row.alert ? " · review" : ""}</li>)}</ul>}</section>;
}
