import type { ActionBreakdown, Resolution, SystemHistoryResponse } from "../types";

interface ResolutionTimelineProps {
  history: SystemHistoryResponse | null;
  loading: boolean;
}

export default function ResolutionTimeline({ history, loading }: ResolutionTimelineProps) {
  if (loading) {
    return (
      <section className="copilot-card p-4 text-sm dataops-muted">
        Loading resolution history...
      </section>
    );
  }

  const total = numberOr(history?.total, 0);
  if (!history || total === 0) {
    return (
      <section className="copilot-card p-4">
        <h2 className="dataops-section-title">Resolution History</h2>
        <div className="mt-3 rounded-md p-3 text-sm dataops-muted" style={{ background: "var(--copilot-surface-muted)" }}>
          No prior triage decisions for this system.
        </div>
      </section>
    );
  }

  const actionBreakdown = history.actionBreakdown || history.action_breakdown || {};
  const bestAction = history.bestAction ?? history.best_action ?? null;
  const worstAction = history.worstAction ?? history.worst_action ?? null;
  const accuracy = typeof history.accuracy === "number" ? history.accuracy : null;

  return (
    <section className="copilot-card p-4">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="dataops-section-title">Resolution History: {history.system || "unknown system"}</h2>
          <p className="mt-1 text-sm dataops-muted">{narrative(total, actionBreakdown, bestAction, worstAction)}</p>
        </div>
        <div className="grid gap-1 text-right text-xs">
          <Metric label="Prior decisions" value={String(total)} />
          <Metric label="Accuracy" value={formatPercent(accuracy)} color={accuracyColor(accuracy)} />
        </div>
      </div>

      <div className="mb-4 grid gap-2 md:grid-cols-2">
        <SummaryPill label="Best action" value={formatAction(bestAction)} />
        <SummaryPill label="Worst action" value={formatAction(worstAction)} />
      </div>

      <div className="grid gap-2">
        {Object.entries(actionBreakdown).map(([action, breakdown]) => (
          <ActionBar key={action} action={action} breakdown={breakdown} />
        ))}
      </div>

      <div className="mt-4 grid gap-2">
        {(history.resolutions || []).map((resolution, index) => (
          <ResolutionRow key={`${resolutionId(resolution)}-${index}`} resolution={resolution} />
        ))}
      </div>
    </section>
  );
}

function ActionBar({ action, breakdown }: { action: string; breakdown: ActionBreakdown }) {
  const winRate = numberOr(breakdown.winRate ?? breakdown.win_rate, 0);
  const width = `${Math.max(0, Math.min(winRate, 1)) * 100}%`;
  return (
    <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="mb-2 flex items-center justify-between gap-3 text-sm">
        <span className="font-semibold" style={{ color: "var(--copilot-text)" }}>{formatAction(action)}</span>
        <span className="dataops-muted">
          {numberOr(breakdown.correct, 0)}/{numberOr(breakdown.count, 0)} · {formatPercent(winRate)}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full" style={{ background: "var(--copilot-surface-muted)" }}>
        <div className="h-full rounded-full" style={{ width, background: accuracyColor(winRate) }} />
      </div>
    </div>
  );
}

function ResolutionRow({ resolution }: { resolution: Resolution }) {
  const correctness = getCorrectness(resolution);
  const status = correctnessStatus[correctness];
  const source = resolution.source === "live_decision" ? "live" : "seed";
  return (
    <div className="rounded-md border p-3 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="font-semibold" style={{ color: "var(--copilot-text)" }}>
            {resolution.alertId || resolution.alert_id || "unknown alert"} · {formatAction(resolution.actionTaken || resolution.action_taken)}
          </div>
          <div className="mt-1 text-xs dataops-muted">
            {formatCategory(resolution.category)} · {resolution.outcome || "unknown outcome"} · {resolution.date || "unknown date"}
          </div>
        </div>
        <div className="text-right">
          <div
            className="font-semibold"
            style={{ color: status.color }}
          >
            {status.icon} {status.label}
          </div>
          <div className="text-xs dataops-muted">{source}</div>
        </div>
      </div>
    </div>
  );
}

type Correctness = "correct" | "incorrect" | "unknown";

const correctnessStatus: Record<Correctness, { icon: string; label: string; color: string }> = {
  correct: { icon: "✓", label: "Correct", color: "var(--copilot-success)" },
  incorrect: { icon: "✗", label: "Incorrect", color: "var(--copilot-danger)" },
  unknown: { icon: "?", label: "Unknown", color: "var(--copilot-text-muted)" },
};

function getCorrectness(resolution: Resolution): Correctness {
  const isCorrect = resolution.isCorrect ?? resolution.is_correct;
  if (isCorrect === true) {
    return "correct";
  }
  if (isCorrect === false) {
    return "incorrect";
  }

  const outcome = String(resolution.outcome || "").toLowerCase();
  if (outcome === "correct") {
    return "correct";
  }
  if (outcome === "incorrect") {
    return "incorrect";
  }
  return "unknown";
}

function Metric({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <div className="dataops-muted">{label}</div>
      <div className="font-semibold" style={{ color: color || "var(--copilot-text)" }}>{value}</div>
    </div>
  );
}

function SummaryPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md p-3 text-sm" style={{ background: "var(--copilot-surface-muted)" }}>
      <div className="text-xs dataops-muted">{label}</div>
      <div className="mt-1 font-semibold" style={{ color: "var(--copilot-text)" }}>{value}</div>
    </div>
  );
}

function narrative(
  total: number,
  actionBreakdown: Record<string, ActionBreakdown>,
  bestAction: string | null,
  worstAction: string | null,
): string {
  if (total < 3) {
    return "Limited history. More decisions needed.";
  }
  const best = bestAction ? actionBreakdown[bestAction] : null;
  const worst = worstAction ? actionBreakdown[worstAction] : null;
  const bestRate = numberOr(best?.winRate ?? best?.win_rate, 0);
  const worstRate = numberOr(worst?.winRate ?? worst?.win_rate, 1);
  if (bestAction && bestRate > 0.7) {
    return `${formatAction(bestAction)} has worked for this system.`;
  }
  if (worstAction && worstRate < 0.3) {
    return `${formatAction(worstAction)} has failed repeatedly.`;
  }
  return "Historical outcomes are mixed for this system.";
}

function accuracyColor(value: number | null): string {
  if (value === null) {
    return "var(--copilot-text-muted)";
  }
  if (value >= 0.7) {
    return "var(--copilot-success)";
  }
  if (value >= 0.5) {
    return "var(--copilot-warning)";
  }
  return "var(--copilot-danger)";
}

function formatPercent(value: number | null): string {
  return value === null ? "--" : `${Math.round(value * 100)}%`;
}

function formatAction(value?: string | null): string {
  return value ? value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase()) : "Unknown action";
}

function formatCategory(value?: string): string {
  return value ? value.replace(/_/g, " ") : "uncategorized";
}

function numberOr(value: unknown, fallback: number): number {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function resolutionId(resolution: Resolution): string {
  return resolution.decisionId || resolution.decision_id || resolution.alertId || resolution.alert_id || "resolution";
}
