import { useEffect, useMemo, useState } from "react";
import { fetchArchetype, type ArchetypeDetail } from "../api";
import ProvenanceBadge from "./ProvenanceBadge";

const GENERIC_ACCURACY = 0.5;
const WEEKLY_IMPROVEMENT = 0.02;

function displayName(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export default function ArchetypeComparisonCard({ currentName }: { currentName?: string }) {
  const [name, setName] = useState(currentName || "default");
  const [detail, setDetail] = useState<ArchetypeDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const nextName = currentName || "default";
    setName(nextName);
    if (nextName === "default") {
      setDetail(null);
      setLoading(false);
      return () => {
        cancelled = true;
      };
    }
    fetchArchetype(nextName)
      .then((payload) => {
        if (!cancelled) setDetail(payload);
      })
      .catch(() => {
        if (!cancelled) setDetail(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [currentName]);

  const archetypeAccuracy = detail?.expectedInitialAccuracy ?? 0.65;
  const weeksHeadStart = useMemo(
    () => Math.max(0, Math.round((archetypeAccuracy - GENERIC_ACCURACY) / WEEKLY_IMPROVEMENT)),
    [archetypeAccuracy],
  );

  if (loading) {
    return <div className="mt-4 rounded-md border p-3 text-sm trading-muted" style={{ borderColor: "var(--copilot-border)" }}>Loading archetype advantage...</div>;
  }

  if (name === "default") {
    return (
      <div className="mt-4 rounded-md border p-3 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold">Archetype Advantage</h3>
            <p className="mt-1 trading-muted">Using generic start.</p>
          </div>
          <ProvenanceBadge source="default" />
        </div>
      </div>
    );
  }

  return (
    <div className="mt-4 rounded-md border p-3 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold">Archetype Advantage</h3>
          <p className="mt-1 trading-muted">Current: {displayName(name)}</p>
        </div>
        <ProvenanceBadge source="transfer" />
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto_1fr] sm:items-center">
        <Metric title="Generic start" value={pct(GENERIC_ACCURACY)} note="Uniform prior" />
        <div className="hidden text-center text-xl trading-muted sm:block">-&gt;</div>
        <Metric title="Archetype start" value={pct(archetypeAccuracy)} note="Expected initial accuracy" />
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Fact label="Estimated head start" value={`~${weeksHeadStart} weeks`} />
        <Fact label="Calibrated for" value={detail?.calibrationNote || "Selected industry workflow"} />
      </div>
    </div>
  );
}

function Metric({ title, value, note }: { title: string; value: string; note: string }) {
  return (
    <div>
      <div className="text-xs trading-muted">{title}</div>
      <div className="trading-stat-value">{value}</div>
      <div className="text-xs trading-muted">{note}</div>
    </div>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs trading-muted">{label}</div>
      <div className="font-semibold">{value}</div>
    </div>
  );
}
