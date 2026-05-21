import { useEffect, useState } from "react";
import { getTransferStatus } from "../api";
import type { PatternTransfer, TransferStatusResponse } from "../types";

const STATUS_STYLES: Record<string, { background: string; color: string }> = {
  active: { background: "rgba(34, 197, 94, 0.12)", color: "var(--copilot-success)" },
  monitoring: { background: "var(--copilot-primary-light)", color: "var(--copilot-primary)" },
  pending_verification: { background: "var(--copilot-surface-muted)", color: "var(--copilot-text-muted)" },
  pending: { background: "var(--copilot-surface-muted)", color: "var(--copilot-text-muted)" },
};

export default function TransferStatusPanel() {
  const [data, setData] = useState<TransferStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setUnavailable(false);
    getTransferStatus()
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
          setUnavailable(!payload);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setData(null);
          setUnavailable(true);
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

  if (loading) {
    return <article className="copilot-card p-5 text-sm dataops-muted">Loading transfer status...</article>;
  }

  if (unavailable || !data) {
    return <article className="copilot-card p-5 text-sm dataops-muted">Transfer status unavailable.</article>;
  }

  const transfers = data.transfers || [];

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            Act 5
          </p>
          <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
            Pattern Transfer Status
          </h2>
          <p className="mt-1 text-sm dataops-muted">Transferred patterns currently monitored across target systems.</p>
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label="Total transfers" value={formatNumber(data.summary?.totalTransfers)} />
        <Metric label="Active" value={formatNumber(data.summary?.active)} />
        <Metric label="Monitoring" value={formatNumber(data.summary?.monitoring)} />
        <Metric label="Cumulative savings" value={formatCurrencyK(data.summary?.cumulativeSavings)} />
      </div>

      {transfers.length === 0 ? (
        <p className="mt-4 text-sm dataops-muted">No transfer records available.</p>
      ) : (
        <div className="mt-5 grid gap-3 lg:grid-cols-3">
          {transfers.map((transfer) => (
            <TransferCard key={transfer.transferId} transfer={transfer} />
          ))}
        </div>
      )}
    </article>
  );
}

function TransferCard({ transfer }: { transfer: PatternTransfer }) {
  const statusStyle = STATUS_STYLES[transfer.status] || STATUS_STYLES.pending;
  return (
    <section className="rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold" style={{ color: "var(--copilot-text)" }}>
            {formatSystem(transfer.sourceSystem)} to {formatSystem(transfer.targetSystem)}
          </h3>
          <p className="mt-1 text-xs dataops-muted">{transfer.transferId}</p>
        </div>
        <span className="rounded-full px-2 py-1 text-xs font-semibold" style={statusStyle}>
          {humanize(transfer.status)}
        </span>
      </div>

      <p className="mt-3 text-sm" style={{ color: "var(--copilot-text)" }}>{transfer.sourcePattern}</p>
      <p className="mt-2 text-sm dataops-muted">{transfer.description}</p>

      <div className="mt-4 grid gap-2 text-sm">
        <Fact label="Target action" value={humanize(transfer.targetAction)} />
        <Fact label="Confidence" value={formatPercent(transfer.confidence)} />
        <Fact label="Target accuracy" value={formatOptionalPercent(transfer.accuracyAtTarget)} />
        <Fact label="Decisions since transfer" value={formatNumber(transfer.decisionsSinceTransfer)} />
        {transfer.savingsEstimate !== null ? <Fact label="Savings" value={formatCurrencyK(transfer.savingsEstimate)} /> : null}
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border px-3 py-2" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs dataops-muted">{label}</div>
      <div className="text-lg font-semibold" style={{ color: "var(--copilot-text)" }}>
        {value}
      </div>
    </div>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md border px-3 py-2" style={{ borderColor: "var(--copilot-border)" }}>
      <span className="text-xs dataops-muted">{label}</span>
      <span className="text-sm font-semibold text-right" style={{ color: "var(--copilot-text)" }}>{value}</span>
    </div>
  );
}

function formatNumber(value: number | null | undefined): string {
  return Number.isFinite(value) ? String(value) : "0";
}

function formatPercent(value: number | null | undefined): string {
  return Number.isFinite(value) ? `${Math.round(Number(value) * 100)}%` : "0%";
}

function formatOptionalPercent(value: number | null | undefined): string {
  return value === null || value === undefined ? "Pending" : formatPercent(value);
}

function formatCurrencyK(value: number | null | undefined): string {
  if (!Number.isFinite(value)) {
    return "$0";
  }
  return `$${Math.round(Number(value) / 1000)}K`;
}

function formatSystem(value: string): string {
  return humanize(value);
}

function humanize(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
