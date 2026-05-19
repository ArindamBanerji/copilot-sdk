import { useEffect, useMemo, useState } from "react";
import { BASE } from "../api";
import type { ProcessTimelineActivity, ProcessTimelineResponse } from "../types";

export function ProcessTimelinePanel() {
  const [data, setData] = useState<ProcessTimelineResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetch(`${BASE}/api/context/process-timeline`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`${response.status} ${response.statusText}`);
        }
        return response.json();
      })
      .then(normalizeTimeline)
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Could not load process timeline.");
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
  }, []);

  const activities = data?.activities || [];
  const slowdown = useMemo(() => resolveSlowdown(data), [data]);
  const bottleneck = activities.find((activity) => activity.isBottleneck);

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            Process Timeline
          </p>
          <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
            Tire Procure-to-Pay Flow
          </h2>
          <p className="mt-1 text-sm dataops-muted">
            {loading
              ? "Loading process timing..."
              : bottleneck
                ? `${bottleneck.name || "Bottleneck"} is running ${formatMultiplier(slowdown)} slower than normal.`
                : "No active bottleneck flagged."}
          </p>
        </div>
        <SlowdownBadge slowdown={slowdown} />
      </div>

      {error ? <p className="mt-4 text-sm" style={{ color: "var(--copilot-danger)" }}>{error}</p> : null}
      {!loading && !error && activities.length === 0 ? (
        <p className="mt-4 text-sm dataops-muted">No process timeline data available.</p>
      ) : null}

      {!error && activities.length > 0 ? (
        <div className="mt-5 grid gap-3 md:grid-cols-4">
          {activities.map((activity, index) => (
            <TimelineActivityCard
              key={activity.id || activity.name || `activity-${index}`}
              activity={activity}
              index={index}
            />
          ))}
        </div>
      ) : null}
    </section>
  );
}

export default ProcessTimelinePanel;

function TimelineActivityCard({
  activity,
  index,
}: {
  activity: ProcessTimelineActivity;
  index: number;
}) {
  const highlighted = Boolean(activity.isBottleneck);
  return (
    <article
      className="relative rounded-md border p-4"
      style={{
        borderColor: highlighted ? "var(--copilot-primary)" : "var(--copilot-border)",
        background: highlighted ? "var(--copilot-primary-light)" : "var(--copilot-surface)",
      }}
    >
      <div
        className="mb-3 flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold"
        style={{
          background: highlighted ? "var(--copilot-primary)" : "var(--copilot-surface-muted)",
          color: highlighted ? "white" : "var(--copilot-text)",
        }}
      >
        {index + 1}
      </div>
      <h3 className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
        {activity.name || "Process activity"}
      </h3>
      <div className="mt-3 grid gap-2 text-sm">
        <Metric label="Duration" value={formatDuration(activity.avgDuration ?? activity.currentDuration)} strong={highlighted} />
        <Metric label="Automation" value={formatPercent(activity.automationRate)} />
        <Metric label="Rework" value={formatPercent(activity.reworkRate)} />
      </div>
      {highlighted ? (
        <div className="mt-3 rounded-md px-3 py-2 text-xs font-semibold" style={{ background: "var(--copilot-surface)", color: "var(--copilot-primary)" }}>
          Active bottleneck
        </div>
      ) : null}
    </article>
  );
}

function SlowdownBadge({ slowdown }: { slowdown: number | null }) {
  return (
    <div className="rounded-md border px-4 py-3 text-right" style={{ borderColor: "var(--copilot-primary)", background: "var(--copilot-primary-light)" }}>
      <div className="text-xs font-semibold uppercase dataops-muted">Slowdown</div>
      <div className="mt-1 text-2xl font-semibold" style={{ color: "var(--copilot-primary)" }}>
        {formatMultiplier(slowdown)}
      </div>
    </div>
  );
}

function Metric({ label, value, strong = false }: { label: string; value: string; strong?: boolean }) {
  return (
    <div>
      <div className="text-xs dataops-muted">{label}</div>
      <div className="font-semibold" style={{ color: strong ? "var(--copilot-primary)" : "var(--copilot-text)" }}>
        {value}
      </div>
    </div>
  );
}

function resolveSlowdown(data: ProcessTimelineResponse | null): number | null {
  const explicit = Number(data?.slowdownMultiplier);
  if (Number.isFinite(explicit) && explicit > 0) {
    return explicit;
  }

  const current = Number(data?.currentDuration);
  const normal = Number(data?.normalDuration);
  if (Number.isFinite(current) && Number.isFinite(normal) && normal > 0) {
    return current / normal;
  }

  return null;
}

function normalizeTimeline(raw: Record<string, unknown>): ProcessTimelineResponse {
  const activities = Array.isArray(raw.activities)
    ? raw.activities.map((activity) => normalizeActivity(activity as Record<string, unknown>))
    : [];

  return {
    processModels: Array.isArray(raw.process_models) ? raw.process_models as Array<Record<string, unknown>> : [],
    activities,
    bottleneckId: stringOr(raw.bottleneck_id),
    normalDuration: numberOrNull(raw.normal_duration) ?? undefined,
    currentDuration: numberOrNull(raw.current_duration) ?? undefined,
    slowdownMultiplier: numberOrNull(raw.slowdown_multiplier),
    dollarCalibration: isRecord(raw.dollar_calibration) ? raw.dollar_calibration as Record<string, number> : {},
    crossGraphRefs: isRecord(raw.cross_graph_refs) ? raw.cross_graph_refs : {},
  };
}

function normalizeActivity(raw: Record<string, unknown>): ProcessTimelineActivity {
  return {
    id: stringOr(raw.id),
    name: stringOr(raw.name),
    avgDuration: numberOrNull(raw.avg_duration) ?? undefined,
    normalDuration: numberOrNull(raw.normal_duration) ?? undefined,
    currentDuration: numberOrNull(raw.current_duration) ?? undefined,
    automationRate: numberOrNull(raw.automation_rate) ?? undefined,
    reworkRate: numberOrNull(raw.rework_rate) ?? undefined,
    isBottleneck: Boolean(raw.is_bottleneck),
    slowdownMultiplier: numberOrNull(raw.slowdown_multiplier),
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function stringOr(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function numberOrNull(value: unknown): number | null {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function formatDuration(value: unknown): string {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "n/a";
  }
  return `${Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(number)} sec`;
}

function formatPercent(value: unknown): string {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "n/a";
  }
  return `${Math.round(number * 100)}%`;
}

function formatMultiplier(value: number | null): string {
  if (!value || !Number.isFinite(value)) {
    return "n/a";
  }
  return `${Math.round(value * 10) / 10}x`;
}
