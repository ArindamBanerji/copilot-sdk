import { useEffect, useState } from "react";
import { fetchAccuracyByCategory } from "../api";
import type { SelfAccuracyByCategoryResponse } from "../types";

export default function AccuracyAlertPanel() {
  const [data, setData] = useState<SelfAccuracyByCategoryResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchAccuracyByCategory()
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const categories = data?.categories || [];
  if (loading) return <section className="copilot-card p-4 text-sm trading-muted">Loading accuracy alerts...</section>;
  if (categories.length === 0) return <section className="copilot-card p-4 text-sm trading-muted">No verified trading decisions yet.</section>;

  return (
    <section className="copilot-card p-5">
      <p className="text-xs font-semibold uppercase" style={{ color: "var(--copilot-primary)" }}>SC-12</p>
      <h2 className="mt-1 text-xl font-semibold">Accuracy Alerts</h2>
      <p className="mt-1 text-sm trading-muted">Threshold {Math.round((data?.threshold ?? 0.7) * 100)}% across {data?.overallVerified ?? 0} verified decisions.</p>
      <div className="mt-4 grid gap-3">
        {categories.map((item) => {
          const pct = Math.round(Number(item.accuracy || 0) * 100);
          return (
            <div key={item.category || "category"}>
              <div className="mb-1 flex justify-between text-sm">
                <span>{String(item.category || "uncategorized").replace(/_/g, " ")}</span>
                <strong className={item.alert ? "trading-negative" : "trading-positive"}>{pct}%</strong>
              </div>
              <div className="trading-bar-track"><div className="trading-bar-fill" style={{ width: `${pct}%` }} /></div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
