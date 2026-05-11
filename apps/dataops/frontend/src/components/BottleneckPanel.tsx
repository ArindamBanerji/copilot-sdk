import { useEffect, useState } from "react";
import { getBottleneck } from "../api";
import type { BottleneckResponse, BottleneckStep } from "../types";

const SYSTEMS = ["warehouse_etl", "billing_api", "payment_gateway", "crm_sync"];

export default function BottleneckPanel() {
  const [system, setSystem] = useState("warehouse_etl");
  const [data, setData] = useState<BottleneckResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getBottleneck(system)
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Could not load bottleneck data.");
          setData(null);
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
  }, [system]);

  const steps = data?.allStepsRanked || [];
  const bottleneckId = data?.bottleneck?.id;

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            OE-2
          </p>
          <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
            Pipeline Bottleneck: {humanize(system)}
          </h2>
          <p className="mt-1 text-sm dataops-muted">
            {loading ? "Finding the slowest transformation..." : `${formatNumber(data?.totalDurationMinutes)} minutes across ${steps.length} steps`}
          </p>
        </div>
        <label className="grid gap-1 text-xs font-semibold dataops-muted">
          System
          <select
            className="rounded-md border px-2 py-2 text-sm"
            style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)", color: "var(--copilot-text)" }}
            value={system}
            onChange={(event) => setSystem(event.target.value)}
          >
            {SYSTEMS.map((option) => (
              <option key={option} value={option}>
                {humanize(option)}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error ? <p className="mt-4 text-sm" style={{ color: "var(--copilot-danger)" }}>{error}</p> : null}
      {!loading && !error && steps.length === 0 ? <p className="mt-4 text-sm dataops-muted">No transformation graph available for this system.</p> : null}

      {!error && steps.length > 0 ? (
        <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(0,1fr)_20rem]">
          <div className="grid gap-3">
            {steps.map((step) => (
              <StepRow
                key={step.id || step.name || "step"}
                step={step}
                highlighted={step.id === bottleneckId}
                totalDurationMinutes={data?.totalDurationMinutes}
              />
            ))}
          </div>
          <Recommendation data={data} />
        </div>
      ) : null}
    </section>
  );
}

function StepRow({
  step,
  highlighted,
  totalDurationMinutes,
}: {
  step: BottleneckStep;
  highlighted: boolean;
  totalDurationMinutes?: number;
}) {
  const pct = resolveStepPct(step, totalDurationMinutes);
  return (
    <article className="rounded-md border p-3" style={{ borderColor: highlighted ? "var(--copilot-primary)" : "var(--copilot-border)" }}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>{step.name || step.id || "Transformation"}</h3>
          <p className="mt-1 text-xs dataops-muted">
            {humanize(step.type || "step")} · {formatRows(step.rows)} rows
          </p>
        </div>
        <span className="text-sm font-semibold" style={{ color: highlighted ? "var(--copilot-primary)" : "var(--copilot-text)" }}>
          {formatNumber(step.durationMinutes)} min
        </span>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full" style={{ background: "var(--copilot-primary-light)" }}>
        <div className="h-full rounded-full" style={{ width: `${pct * 100}%`, background: highlighted ? "var(--copilot-primary)" : "var(--copilot-text-muted)" }} />
      </div>
      <div className="mt-1 text-xs dataops-muted">{Math.round(pct * 100)}% of runtime</div>
    </article>
  );
}

function Recommendation({ data }: { data: BottleneckResponse | null }) {
  const recommendation = data?.recommendation;
  return (
    <aside className="rounded-md border p-4" style={{ borderColor: "var(--copilot-primary)", background: "var(--copilot-primary-light)" }}>
      <div className="text-xs font-semibold uppercase tracking-[0.16em]" style={{ color: "var(--copilot-primary)" }}>Recommendation</div>
      {recommendation ? (
        <>
          <h3 className="mt-2 text-base font-semibold" style={{ color: "var(--copilot-text)" }}>{humanize(recommendation.action || "optimize")}</h3>
          <p className="mt-2 text-sm dataops-muted">{recommendation.detail}</p>
          <div className="mt-4 grid gap-2 text-sm">
            <Metric label="Speedup" value={recommendation.estimatedSpeedup || "n/a"} />
            <Metric label="Savings" value={`${formatNumber(recommendation.estimatedSavingsMinutes)} min`} />
          </div>
        </>
      ) : (
        <p className="mt-2 text-sm dataops-muted">No recommendation available.</p>
      )}
    </aside>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border px-3 py-2" style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)" }}>
      <div className="text-xs dataops-muted">{label}</div>
      <div className="mt-1 font-semibold" style={{ color: "var(--copilot-text)" }}>{value}</div>
    </div>
  );
}

function clamp(value: number): number {
  return Number.isFinite(value) ? Math.max(0, Math.min(value, 1)) : 0;
}

function resolveStepPct(step: BottleneckStep, totalDurationMinutes?: number): number {
  const explicit = Number(step.pctOfTotal);
  if (Number.isFinite(explicit)) {
    return clamp(explicit);
  }

  const duration = Number(step.durationMinutes);
  const total = Number(totalDurationMinutes);
  if (Number.isFinite(duration) && Number.isFinite(total) && total > 0) {
    return clamp(duration / total);
  }

  return 0;
}

function formatNumber(value: unknown): string {
  const number = Number(value);
  return Number.isFinite(number) ? String(Math.round(number * 10) / 10) : "0";
}

function formatRows(value: unknown): string {
  const number = Number(value);
  return Number.isFinite(number) ? Intl.NumberFormat("en-US", { notation: "compact" }).format(number) : "n/a";
}

function humanize(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
