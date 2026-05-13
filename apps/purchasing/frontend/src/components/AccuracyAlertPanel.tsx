import { useEffect, useState } from "react";

import { fetchAccuracyByCategory } from "../api";
import type { CategoryAccuracy } from "../types";

function label(value: string): string {
  return value.replace(/_/g, " ");
}

export function AccuracyAlertPanel() {
  const [categories, setCategories] = useState<CategoryAccuracy[] | null>(null);
  const [threshold, setThreshold] = useState(0.7);

  useEffect(() => {
    let active = true;
    fetchAccuracyByCategory(0.7).then((response) => {
      if (!active) return;
      setCategories(response?.categories ?? []);
      setThreshold(response?.threshold ?? 0.7);
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <section className="purchase-card">
      <p className="purchase-kicker">SC-12 Accuracy</p>
      <h3 className="purchase-title">Category accuracy alerts</h3>
      <p className="purchase-muted">Threshold {Math.round(threshold * 100)}%</p>
      {!categories ? (
        <p className="purchase-muted mt-4">Loading...</p>
      ) : categories.length === 0 ? (
        <p className="purchase-muted mt-4">No verified decisions yet.</p>
      ) : (
        <div className="mt-4 space-y-3">
          {categories.map((item) => (
            <div key={item.category ?? "uncategorized"}>
              <div className="flex items-center justify-between text-sm">
                <span className="capitalize text-slate-700">{label(item.category ?? "uncategorized")}</span>
                <span className={item.alert ? "font-semibold text-rose-600" : "font-semibold text-emerald-600"}>
                  {Math.round((item.accuracy ?? 0) * 100)}%
                </span>
              </div>
              <div className="mt-1 h-2 rounded-full bg-slate-200">
                <div
                  className={`h-2 rounded-full ${item.alert ? "bg-rose-500" : "bg-emerald-500"}`}
                  style={{ width: `${Math.max(4, Math.min(100, (item.accuracy ?? 0) * 100))}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
