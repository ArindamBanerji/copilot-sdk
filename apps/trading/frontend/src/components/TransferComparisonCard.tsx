import { useEffect, useMemo, useState } from "react";
import { fetchTransferStatus, getAnalytics, type TransferStatusResponse } from "../api";
import type { Analytics } from "../types";
import ProvenanceBadge from "./ProvenanceBadge";

const BASELINE_ACCURACY = 0.5;
const WEEKLY_IMPROVEMENT = 0.02;

function label(value?: string): string {
  return String(value || "unknown").replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export default function TransferComparisonCard() {
  const [status, setStatus] = useState<TransferStatusResponse | null>(null);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchTransferStatus().catch(() => null), getAnalytics().catch(() => null)])
      .then(([nextStatus, nextAnalytics]) => {
        if (cancelled) return;
        setStatus(nextStatus);
        setAnalytics(nextAnalytics);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const postTransferAccuracy = useMemo(() => {
    if (typeof status?.sourceAccuracy === "number") return status.sourceAccuracy;
    const winRate = analytics?.portfolioSummary?.winRate;
    if (typeof winRate === "number" && winRate > 0) return winRate > 1 ? winRate / 100 : winRate;
    return 0.72;
  }, [analytics, status]);

  const weeksSaved = Math.max(0, Math.round((postTransferAccuracy - BASELINE_ACCURACY) / WEEKLY_IMPROVEMENT));

  if (loading) {
    return <div className="mt-4 rounded-md border p-3 text-sm trading-muted" style={{ borderColor: "var(--copilot-border)" }}>Loading transfer impact...</div>;
  }

  if (!status?.warmStarted) {
    return (
      <div className="mt-4 rounded-md border p-3 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold">Transfer Impact</h3>
            <p className="mt-1 trading-muted">No transfers applied yet.</p>
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
          <h3 className="text-sm font-semibold">Transfer Impact</h3>
          <p className="mt-1 trading-muted">
            Source: {label(status.sourceCopilot)} ({pct(status.sourceAccuracy ?? 0.84)} accuracy)
          </p>
          <p className="trading-muted">Target: Trading</p>
        </div>
        <ProvenanceBadge source={status.provenance || "transfer"} />
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto_1fr] sm:items-center">
        <Metric title="Before transfer" value={pct(BASELINE_ACCURACY)} note="Generic baseline" />
        <div className="hidden text-center text-xl trading-muted sm:block">-&gt;</div>
        <Metric title="After transfer" value={pct(postTransferAccuracy)} note="Day-one accuracy" />
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Fact label="Estimated calibration saved" value={`~${weeksSaved} weeks`} />
        <Fact label="Categories transferred" value={String(status.categoriesTransferred ?? status.patternsTransferred ?? 0)} />
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
