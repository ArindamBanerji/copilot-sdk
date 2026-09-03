import { useEffect, useState } from "react";

export interface AccuracyAlertsPanelProps { baseUrl?: string; }
interface AccuracyRow { category?: string; accuracy?: number; alert?: boolean; }

export default function AccuracyAlertsPanel({ baseUrl = "/api/self" }: AccuracyAlertsPanelProps) {
  const [rows, setRows] = useState<AccuracyRow[]>([]);
  useEffect(() => { fetch(`${baseUrl}/accuracy-alerts`).then((response) => response.json()).then((value: { categories?: unknown }) => setRows(Array.isArray(value.categories) ? value.categories.filter((item): item is AccuracyRow => typeof item === "object" && item !== null) : [])); }, [baseUrl]);
  return <section data-testid="accuracy-alerts-panel" className="copilot-card p-4"><h2 className="text-base font-semibold">Accuracy Alerts</h2>{rows.length === 0 ? <p>No category observations available.</p> : <ul>{rows.map((row) => <li key={row.category ?? "uncategorized"}>{row.category ?? "uncategorized"}: {typeof row.accuracy === "number" ? `${Math.round(row.accuracy * 100)}%` : "—"}{row.alert ? " · review" : ""}</li>)}</ul>}</section>;
}
