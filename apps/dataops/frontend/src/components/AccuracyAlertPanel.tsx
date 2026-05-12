import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fetchAccuracyByCategory } from "../api";
import type { SelfAccuracyByCategoryResponse } from "../types";

export default function AccuracyAlertPanel() {
  const [data, setData] = useState<SelfAccuracyByCategoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);
    fetchAccuracyByCategory()
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError(true);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return null;
  }
  if (loading) {
    return <section className="copilot-card p-4 text-sm dataops-muted">Loading...</section>;
  }
  const categories = data?.categories || [];
  if (categories.length === 0) {
    return <section className="copilot-card p-4 text-sm dataops-muted">No verified decisions yet.</section>;
  }

  const threshold = data?.threshold ?? 0.7;
  const rows = categories.map((item) => ({
    category: humanize(item.category || "uncategorized"),
    accuracy: Math.round(Number(item.accuracy || 0) * 100),
    alert: Boolean(item.alert),
  }));

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            SC-12
          </p>
          <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
            Accuracy Alerts
          </h2>
          <p className="mt-1 text-sm dataops-muted">
            Threshold {Math.round(threshold * 100)}% across {data?.overallVerified ?? 0} verified decisions.
          </p>
        </div>
      </div>
      <div className="mt-4 h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.35)" />
            <XAxis dataKey="category" tick={{ fontSize: 12 }} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
            <Tooltip formatter={(value) => `${value}%`} />
            <Bar dataKey="accuracy" label={{ position: "top", formatter: (value: unknown) => `${value}%` }}>
              {rows.map((row) => (
                <Cell key={row.category} fill={row.alert ? "#dc2626" : "#16a34a"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

function humanize(value: string): string {
  return value.replace(/_/g, " ");
}
