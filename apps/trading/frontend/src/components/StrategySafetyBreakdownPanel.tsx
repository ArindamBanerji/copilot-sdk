import { useEffect, useState } from "react";
import { getConservationBreakdown } from "../api";
import type { CategoryConservation, ConservationBreakdownResponse } from "../types";

function labelForCategory(category: string): string {
  return category
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function pct(value: number | null | undefined): string {
  return typeof value === "number" ? `${Math.round(Math.max(0, value) * 100)}%` : "-";
}

function statusTone(status: string): string {
  if (status === "RED") return "border-red-400/40 bg-red-400/10 text-red-100";
  if (status === "AMBER") return "border-amber-400/40 bg-amber-400/10 text-amber-100";
  if (status === "GREEN") return "border-emerald-400/40 bg-emerald-400/10 text-emerald-100";
  return "border-sky-400/40 bg-sky-400/10 text-sky-100";
}

function CategoryRow({ category }: { category: CategoryConservation }) {
  const accuracy = Math.max(0, Math.min(1, Number(category.accuracy) || 0));
  const thetaPosition = Math.max(0, Math.min(100, Math.round((Number(category.thetaMinProxy) || 0) * 100)));

  return (
    <article className="rounded-md border border-white/10 bg-white/[0.03] p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-base font-semibold text-white">{labelForCategory(category.category)}</h3>
          <p className="mt-1 text-sm trading-muted">
            {category.verified} verified of {category.totalTrades} trades
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className={`rounded-md border px-2 py-1 text-xs font-semibold ${statusTone(category.status)}`}>
            {category.status}
          </span>
          <span className="rounded-md border border-white/10 px-2 py-1 text-xs trading-muted">
            {category.canTrade ? "Can trade" : "Paused"}
          </span>
        </div>
      </div>

      <div className="mt-4">
        <div className="mb-2 flex items-center justify-between text-xs trading-muted">
          <span>Accuracy {pct(category.accuracy)}</span>
          <span>theta min proxy {category.thetaMinProxy.toFixed(2)}</span>
        </div>
        <div className="relative h-2 overflow-hidden rounded-full bg-white/10">
          <div className="h-full rounded-full bg-emerald-400" style={{ width: pct(accuracy) }} />
          <div
            className="absolute top-0 h-full w-0.5 bg-white/80"
            style={{ left: `${thetaPosition}%` }}
            aria-hidden="true"
          />
        </div>
      </div>

      <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
        <div>
          <p className="text-xs uppercase tracking-wide trading-muted">Correct</p>
          <p className="font-semibold text-white">{category.correct}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide trading-muted">Verified</p>
          <p className="font-semibold text-white">{category.verified}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide trading-muted">Decision</p>
          <p className="font-semibold text-white">{category.canTrade ? "Allowed" : "Blocked"}</p>
        </div>
      </div>

      {category.note ? <p className="mt-3 text-sm text-amber-100">{category.note}</p> : null}
    </article>
  );
}

export default function StrategySafetyBreakdownPanel() {
  const [data, setData] = useState<ConservationBreakdownResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getConservationBreakdown()
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch((loadError) => {
        console.debug("strategy safety breakdown unavailable", loadError);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <section className="copilot-card p-5">
        <p className="text-sm uppercase tracking-wide trading-muted">Strategy Safety Breakdown</p>
        <p className="mt-2 text-sm trading-muted">Loading strategy safety proxy...</p>
      </section>
    );
  }

  if (!data) {
    return (
      <section className="copilot-card p-5">
        <h2 className="text-base font-semibold">Strategy Safety Breakdown</h2>
        <p className="mt-2 text-sm trading-muted">Strategy safety breakdown is not available right now.</p>
      </section>
    );
  }

  const categories = data.categories ?? [];
  const hasCategories = categories.length > 0;

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-wide trading-muted">Simplified conservation proxy</p>
          <h2 className="mt-1 text-xl font-semibold">Strategy Safety Breakdown</h2>
          <p className="mt-2 text-sm trading-muted">
            Per-strategy safety uses imported trade outcomes. Global conservation remains authoritative.
          </p>
        </div>
        <span className={`rounded-md border px-3 py-2 text-sm font-semibold ${data.overallSafe ? statusTone("GREEN") : statusTone("RED")}`}>
          {data.overallSafe ? "All strategies safe" : "Some strategies paused"}
        </span>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-5">
        <Summary label="Categories" value={String(data.totalCategories)} />
        <Summary label="Verified" value={String(data.totalVerified)} />
        <Summary label="RED" value={String(data.redCategories)} />
        <Summary label="AMBER" value={String(data.amberCategories)} />
        <Summary label="GREEN" value={String(data.greenCategories)} />
      </div>

      {!hasCategories ? (
        <div className="mt-4 rounded-md border border-dashed border-white/15 p-4 text-sm trading-muted">
          No strategy categories are available yet.
        </div>
      ) : (
        <div className="mt-4 grid gap-3 lg:grid-cols-2">
          {categories.map((category) => (
            <CategoryRow key={category.category} category={category} />
          ))}
        </div>
      )}

      <footer className="mt-4 rounded-md border border-white/10 bg-white/[0.03] p-3 text-sm trading-muted">
        {data.methodology}
      </footer>
    </section>
  );
}

function Summary({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-white/10 px-3 py-2">
      <div className="text-xs uppercase tracking-wide trading-muted">{label}</div>
      <div className="text-lg font-semibold text-white">{value}</div>
    </div>
  );
}
