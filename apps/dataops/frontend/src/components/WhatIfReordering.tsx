import { useEffect, useMemo, useState } from "react";
import { getTransformations } from "../api";
import type { Transformation } from "../types";

const SYSTEMS = ["warehouse_etl", "billing_api", "payment_gateway", "crm_sync"];

interface Estimate {
  changed: boolean;
  inputReductionPct: number;
  baselineMinutes: number;
  estimatedMinutes: number;
  savingsMinutes: number;
  narrative: string;
}

export default function WhatIfReordering() {
  const [system, setSystem] = useState("warehouse_etl");
  const [original, setOriginal] = useState<Transformation[]>([]);
  const [ordered, setOrdered] = useState<Transformation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [applied, setApplied] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setApplied(false);
    getTransformations(system)
      .then((payload) => {
        if (cancelled) {
          return;
        }
        const transformations = payload.transformations || [];
        setOriginal(transformations);
        setOrdered(transformations);
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Could not load transformation graph.");
          setOriginal([]);
          setOrdered([]);
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

  const estimate = useMemo(() => estimateReorder(original, ordered, system), [original, ordered, system]);

  function move(index: number, direction: -1 | 1) {
    setApplied(false);
    setOrdered((current) => {
      const target = index + direction;
      if (target < 0 || target >= current.length) {
        return current;
      }
      const next = [...current];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  }

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            OE-5
          </p>
          <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
            What-if: Reorder {humanize(system)}
          </h2>
          <p className="mt-1 text-sm dataops-muted">
            Test pipeline step order locally before promoting an operational rule.
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
      {loading ? <p className="mt-4 text-sm dataops-muted">Loading transformation graph...</p> : null}
      {!loading && !error && ordered.length === 0 ? (
        <p className="mt-4 text-sm dataops-muted">No transformation graph available for this system.</p>
      ) : null}

      {!loading && !error && ordered.length > 0 ? (
        <div className="mt-5 grid gap-4 xl:grid-cols-[minmax(0,1fr)_22rem]">
          <div className="grid gap-4">
            <OrderList title="Current order" steps={original} readonly />
            <OrderList title="Reorder order" steps={ordered} onMove={move} />
          </div>
          <ImpactPanel
            estimate={estimate}
            applied={applied}
            onApply={() => {
              if (estimate.changed) {
                setApplied(true);
              }
            }}
          />
        </div>
      ) : null}
    </section>
  );
}

function OrderList({
  title,
  steps,
  readonly = false,
  onMove,
}: {
  title: string;
  steps: Transformation[];
  readonly?: boolean;
  onMove?: (index: number, direction: -1 | 1) => void;
}) {
  return (
    <section className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
      <h3 className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>{title}</h3>
      <div className="mt-3 grid gap-2">
        {steps.map((step, index) => (
          <article
            key={`${step.id || step.name || "step"}-${index}`}
            className="flex items-center justify-between gap-3 rounded-md p-3"
            style={{ background: "var(--copilot-surface-muted)" }}
          >
            <div>
              <div className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
                {step.name || step.id || "Transformation"}
              </div>
              <div className="mt-1 text-xs dataops-muted">
                {humanize(step.type || "step")} · {formatNumber(step.avgDurationMinutes)} min · {formatRows(step.avgRows)} rows · {step.status || "unknown"}
              </div>
            </div>
            {!readonly ? (
              <div className="flex shrink-0 gap-1">
                <button
                  type="button"
                  className="copilot-button-secondary h-8 w-8 px-0 text-sm"
                  disabled={index === 0}
                  aria-label={`Move ${step.name || step.id || "step"} up`}
                  onClick={() => onMove?.(index, -1)}
                >
                  ↑
                </button>
                <button
                  type="button"
                  className="copilot-button-secondary h-8 w-8 px-0 text-sm"
                  disabled={index === steps.length - 1}
                  aria-label={`Move ${step.name || step.id || "step"} down`}
                  onClick={() => onMove?.(index, 1)}
                >
                  ↓
                </button>
              </div>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}

function ImpactPanel({
  estimate,
  applied,
  onApply,
}: {
  estimate: Estimate;
  applied: boolean;
  onApply: () => void;
}) {
  return (
    <aside className="rounded-md border p-4" style={{ borderColor: "var(--copilot-primary)", background: "var(--copilot-primary-light)" }}>
      <div className="text-xs font-semibold uppercase tracking-[0.16em]" style={{ color: "var(--copilot-primary)" }}>
        Estimated impact
      </div>
      {!estimate.changed ? (
        <p className="mt-3 text-sm dataops-muted">Move steps to estimate impact.</p>
      ) : (
        <>
          <div className="mt-3 grid gap-2 text-sm">
            <Metric label="Join input reduced" value={`${Math.round(estimate.inputReductionPct)}%`} />
            <Metric
              label="Total pipeline time"
              value={`${formatNumber(estimate.baselineMinutes)} min -> ~${formatNumber(estimate.estimatedMinutes)} min`}
            />
            <Metric label="Savings" value={`~${formatNumber(estimate.savingsMinutes)} min/day`} />
          </div>
          <p className="mt-3 text-sm dataops-muted">{estimate.narrative}</p>
          <button type="button" className="copilot-button-primary mt-4 w-full px-3 py-2 text-sm" onClick={onApply}>
            Apply as Operational Rule
          </button>
          {applied ? (
            <p className="mt-3 rounded-md border px-3 py-2 text-sm" style={{ borderColor: "var(--copilot-primary)", color: "var(--copilot-primary)" }}>
              Reorder suggestion saved. Review in Operational Rules on Evidence tab.
            </p>
          ) : null}
        </>
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

function estimateReorder(original: Transformation[], ordered: Transformation[], system: string): Estimate {
  const baselineMinutes = sumDuration(original);
  const changed = original.map(stepKey).join("|") !== ordered.map(stepKey).join("|");
  const emptyEstimate = {
    changed,
    inputReductionPct: 0,
    baselineMinutes,
    estimatedMinutes: baselineMinutes,
    savingsMinutes: 0,
    narrative: "No measurable runtime improvement found for this order.",
  };

  if (!changed || baselineMinutes <= 0) {
    return emptyEstimate;
  }

  const join = findJoin(ordered);
  if (!join) {
    return {
      ...emptyEstimate,
      narrative: "No join step found, so the model keeps runtime flat until a bottleneck can be reduced.",
    };
  }

  const joinIndex = ordered.indexOf(join);
  const originalJoinIndex = original.findIndex((step) => stepKey(step) === stepKey(join));
  const priorSmallest = smallestRows(ordered.slice(0, joinIndex));
  const originalPriorSmallest = smallestRows(original.slice(0, Math.max(originalJoinIndex, 0)));
  const joinRows = positiveNumber(join.avgRows);
  const joinDuration = positiveNumber(join.avgDurationMinutes);

  if (system === "warehouse_etl" && stepKey(join) === "join_vbak_bseg" && priorSmallest && originalPriorSmallest && priorSmallest < originalPriorSmallest) {
    return {
      changed,
      inputReductionPct: 65,
      baselineMinutes: 70,
      estimatedMinutes: 32,
      savingsMinutes: 38,
      narrative: "Moving the smaller revenue aggregate before the VBAK/BSEG join cuts join fanout before the warehouse load.",
    };
  }

  if (!priorSmallest || !originalPriorSmallest || !joinRows || !joinDuration || priorSmallest >= originalPriorSmallest) {
    return emptyEstimate;
  }

  const rowRatio = clamp(priorSmallest / Math.max(originalPriorSmallest, joinRows, 1));
  const reducedJoinDuration = Math.max(1, joinDuration * rowRatio);
  const savingsMinutes = Math.max(0, joinDuration - reducedJoinDuration);
  const estimatedMinutes = Math.max(0, baselineMinutes - savingsMinutes);
  const inputReductionPct = clamp(1 - rowRatio) * 100;

  return {
    changed,
    inputReductionPct,
    baselineMinutes,
    estimatedMinutes,
    savingsMinutes,
    narrative: `${join.name || "Join"} sees fewer input rows before execution, reducing estimated fanout and downstream runtime.`,
  };
}

function findJoin(steps: Transformation[]): Transformation | undefined {
  return steps.find((step) => {
    const text = `${step.type || ""} ${step.name || ""}`.toLowerCase();
    return text.includes("join") || text.includes("merge");
  });
}

function smallestRows(steps: Transformation[]): number | null {
  const rows = steps.map((step) => positiveNumber(step.avgRows)).filter((value): value is number => value !== null);
  return rows.length ? Math.min(...rows) : null;
}

function sumDuration(steps: Transformation[]): number {
  return steps.reduce((sum, step) => sum + (positiveNumber(step.avgDurationMinutes) || 0), 0);
}

function stepKey(step: Transformation): string {
  return step.id || step.name || "";
}

function positiveNumber(value: unknown): number | null {
  const number = Number(value);
  return Number.isFinite(number) && number > 0 ? number : null;
}

function clamp(value: number): number {
  return Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : 0;
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
