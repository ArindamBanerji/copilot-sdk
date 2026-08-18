import { useEffect, useState } from "react";
import { fetchAccuracyByCategory } from "../api";
import type { CategoryAccuracy, SelfAccuracyByCategoryResponse } from "../types";
import EvidenceTierBadge from "./EvidenceTierBadge";

export default function AccuracyByCategory() {
  const [data, setData] = useState<SelfAccuracyByCategoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchAccuracyByCategory()
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch((loadError) => {
        console.debug("category accuracy unavailable", loadError);
        if (!cancelled) setError("Category accuracy unavailable.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return <section className="copilot-card p-4 text-sm trading-muted">Category accuracy unavailable.</section>;
  }
  if (loading) {
    return <section className="copilot-card p-4 text-sm trading-muted">Loading category accuracy...</section>;
  }

  const categories = Array.isArray(data?.categories) ? data.categories : [];
  if (categories.length === 0) {
    return <section className="copilot-card p-4 text-sm trading-muted">No category accuracy yet. Confirm more trades to build history.</section>;
  }

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            SC-12
          </p>
          <h2 className="mt-1 text-xl font-semibold">Accuracy by Category</h2>
          <p className="mt-1 text-sm trading-muted">
            Threshold {Math.round((data?.threshold ?? 0.7) * 100)}% across {data?.overallVerified ?? 0} verified trading decisions.
          </p>
          <div className="mt-2"><EvidenceTierBadge tier={data?.evidenceTier} label={data?.evidenceLabel} /></div>
        </div>
      </div>
      <div className="mt-4 grid gap-3">
        {categories.map((item, index) => (
          <CategoryRow key={`${item.category || "category"}-${index}`} item={item} />
        ))}
      </div>
    </section>
  );
}

function CategoryRow({ item }: { item: CategoryAccuracy }) {
  const pct = Math.max(0, Math.min(100, Math.round(Number(item.accuracy || 0) * 100)));
  const total = Number(item.total || 0);
  const correct = Number(item.correct || 0);
  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-3 text-sm">
        <div>
          <span className="font-medium">{humanize(item.category || "uncategorized")}</span>
          <span className="ml-2 text-xs trading-muted">
            {correct}/{total} correct
          </span>
        </div>
        <strong className={item.alert ? "trading-negative" : "trading-positive"}>{pct}%</strong>
      </div>
      <div className="trading-bar-track">
        <div className="trading-bar-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function humanize(value: string): string {
  return value.replace(/_/g, " ");
}
