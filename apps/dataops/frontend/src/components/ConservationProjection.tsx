import type { ConservationState, TrajectoryPoint, TrajectoryResponse } from "../types";

interface ConservationProjectionProps {
  conservation: ConservationState | null;
  trajectory: TrajectoryResponse | null;
}

interface ProjectionRow {
  targetAlpha: number;
  status: "met" | "ready" | "accuracy" | "decisions" | "blocked";
  message: string;
}

const TARGETS = [0.55, 0.75, 0.9];
const CANONICAL_CONSTANT = 23.53;

export default function ConservationProjection({
  conservation,
  trajectory,
}: ConservationProjectionProps) {
  if (!conservation) {
    return (
      <section className="copilot-card p-4">
        <h2 className="dataops-section-title">Automation Projection</h2>
        <p className="mt-2 text-sm dataops-muted">Projection unavailable until conservation status is available.</p>
      </section>
    );
  }

  const q = extractAccuracy(conservation, trajectory);
  const verified = extractVerifiedCount(conservation, trajectory);
  const decisionsTotal = positiveNumber(
    readNumber(trajectory, ["decisionsTotal", "decisions_total"]) ??
      readNumber(conservation, ["totalDecisions", "total_decisions"]) ??
      verified,
  );
  const decisionsPerWeek = computeDecisionsPerWeek(trajectory, decisionsTotal);
  const currentAlpha = extractCurrentAlpha(conservation);
  const status = stringValue(conservation.status) || "UNKNOWN";

  if (!verified) {
    return (
      <section className="copilot-card p-4">
        <Header />
        <p className="mt-3 text-sm dataops-muted">Start making verified decisions to see projections.</p>
        <Footer />
      </section>
    );
  }

  if (!q) {
    return (
      <section className="copilot-card p-4">
        <Header />
        <p className="mt-3 text-sm dataops-muted">
          Accuracy is not available yet. The projection needs verified outcomes before raising automation.
        </p>
        <Footer />
      </section>
    );
  }

  const rows = TARGETS.map((targetAlpha) =>
    buildProjection(targetAlpha, q, verified, decisionsPerWeek, currentAlpha),
  );

  return (
    <section className="copilot-card p-4">
      <Header />

      <div className="mt-4 grid gap-3 sm:grid-cols-4">
        <Metric label="Current auto-resolve" value={currentAlpha ? formatPercent(currentAlpha) : "unknown"} />
        <Metric label="Status" value={status} />
        <Metric label="Accuracy" value={formatPercent(q)} />
        <Metric label="Verified decisions" value={String(Math.round(verified))} />
      </div>

      <div className="mt-4 grid gap-3">
        {rows.map((row) => (
          <ProjectionTarget key={row.targetAlpha} row={row} />
        ))}
      </div>

      <div className="mt-3 text-xs dataops-muted">
        Pace: {decisionsPerWeek > 0 ? `${decisionsPerWeek} decisions/week` : "not enough history to estimate pace"}.
      </div>
      <Footer />
    </section>
  );
}

function Header() {
  return (
    <div>
      <h2 className="dataops-section-title">Automation Projection</h2>
      <p className="mt-1 text-sm dataops-muted">
        Estimates when higher automation levels are safe, based on verified decisions and current accuracy.
      </p>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md p-3" style={{ background: "var(--copilot-surface-muted)" }}>
      <div className="text-xs dataops-muted">{label}</div>
      <div className="mt-1 text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
        {value}
      </div>
    </div>
  );
}

function ProjectionTarget({ row }: { row: ProjectionRow }) {
  const tone = toneForStatus(row.status);
  return (
    <div
      className="flex items-start gap-3 rounded-md border p-3"
      style={{ borderColor: tone.border, background: tone.background }}
    >
      <div
        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold"
        style={{ background: tone.badgeBackground, color: tone.color }}
        aria-hidden="true"
      >
        {tone.icon}
      </div>
      <div>
        <div className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
          Target {formatPercent(row.targetAlpha)} automation
        </div>
        <p className="mt-1 text-sm dataops-muted">{row.message}</p>
      </div>
    </div>
  );
}

function Footer() {
  return (
    <footer className="mt-4 text-xs font-semibold" style={{ color: "var(--copilot-primary)" }}>
      The system tells you WHEN. Not before.
    </footer>
  );
}

function buildProjection(
  targetAlpha: number,
  q: number,
  verified: number,
  decisionsPerWeek: number,
  currentAlpha: number | null,
): ProjectionRow {
  if (currentAlpha !== null && targetAlpha <= currentAlpha) {
    return {
      targetAlpha,
      status: "met",
      message: "Already met at the current automation level.",
    };
  }

  const vNeeded = CANONICAL_CONSTANT / (targetAlpha * q);
  const additionalDecisions = Math.max(0, Math.ceil(vNeeded - verified));
  const accuracyNeeded = CANONICAL_CONSTANT / (targetAlpha * Math.max(verified, 1));
  const needsAccuracy = q < accuracyNeeded && verified > 50;

  if (needsAccuracy) {
    const gap = Math.max(0, accuracyNeeded - q);
    return {
      targetAlpha,
      status: "accuracy",
      message: `Accuracy must improve by ${formatPercentagePoints(gap)} before this level is safe.`,
    };
  }

  if (additionalDecisions === 0) {
    return {
      targetAlpha,
      status: "ready",
      message: "Ready now. Current verified outcomes satisfy the conservation threshold.",
    };
  }

  const weeks =
    decisionsPerWeek > 0 ? Math.max(1, Math.ceil(additionalDecisions / decisionsPerWeek)) : null;
  return {
    targetAlpha,
    status: "decisions",
    message: weeks
      ? `Need ${additionalDecisions} more verified decisions, about ${weeks} week${weeks === 1 ? "" : "s"} at current pace.`
      : `Need ${additionalDecisions} more verified decisions before this target is achievable.`,
  };
}

function toneForStatus(status: ProjectionRow["status"]) {
  if (status === "met" || status === "ready") {
    return {
      icon: "OK",
      color: "var(--copilot-success)",
      border: "rgba(22, 163, 74, 0.35)",
      background: "rgba(22, 163, 74, 0.06)",
      badgeBackground: "rgba(22, 163, 74, 0.12)",
    };
  }
  if (status === "accuracy") {
    return {
      icon: "!",
      color: "var(--copilot-warning)",
      border: "rgba(217, 119, 6, 0.35)",
      background: "rgba(217, 119, 6, 0.07)",
      badgeBackground: "rgba(217, 119, 6, 0.14)",
    };
  }
  return {
    icon: "...",
    color: "var(--copilot-text-muted)",
    border: "var(--copilot-border)",
    background: "var(--copilot-surface)",
    badgeBackground: "var(--copilot-surface-muted)",
  };
}

function extractAccuracy(
  conservation: ConservationState,
  trajectory: TrajectoryResponse | null,
): number | null {
  const raw =
    readNumber(conservation, ["q", "accuracy", "currentAccuracy", "current_accuracy", "winRate", "win_rate"]) ??
    readNumber(trajectory, ["currentWinRate", "current_win_rate"]);
  return normalizeUnit(raw);
}

function extractVerifiedCount(
  conservation: ConservationState,
  trajectory: TrajectoryResponse | null,
): number | null {
  return positiveNumber(
    readNumber(conservation, ["verifiedCount", "verified_count", "v", "V", "verifiedDecisions", "verified_decisions"]) ??
      readNumber(trajectory, ["decisionsTotal", "decisions_total"]),
  );
}

function extractCurrentAlpha(conservation: ConservationState): number | null {
  return normalizeUnit(
    readNumber(conservation, ["alpha", "autoResolveRate", "auto_resolve_rate", "currentThreshold", "current_threshold"]),
  );
}

function computeDecisionsPerWeek(trajectory: TrajectoryResponse | null, decisionsTotal: number | null): number {
  const daysActive = positiveNumber(readNumber(trajectory, ["daysActive", "days_active"]));
  if (daysActive && decisionsTotal) {
    return Math.max(1, Math.round((decisionsTotal / daysActive) * 7));
  }

  const points = Array.isArray(trajectory?.points) ? trajectory?.points || [] : [];
  const timestampDays = daysFromPoints(points);
  if (timestampDays && decisionsTotal) {
    return Math.max(1, Math.round((decisionsTotal / timestampDays) * 7));
  }

  return decisionsTotal && decisionsTotal > 0 ? 21 : 0;
}

function daysFromPoints(points: TrajectoryPoint[]): number | null {
  const timestamps = points
    .map((point) => normalizeTimestamp(point.timestamp))
    .filter((value): value is number => value !== null)
    .sort((left, right) => left - right);
  if (timestamps.length < 2) {
    return null;
  }
  const spanMs = timestamps[timestamps.length - 1] - timestamps[0];
  const days = spanMs / (1000 * 60 * 60 * 24);
  return days > 0 ? days : null;
}

function normalizeTimestamp(timestamp: unknown): number | null {
  const value = Number(timestamp);
  if (!Number.isFinite(value) || value <= 0) {
    return null;
  }
  return value < 10_000_000_000 ? value * 1000 : value;
}

function readNumber(source: unknown, keys: string[]): number | null {
  if (!source || typeof source !== "object") {
    return null;
  }
  const record = source as Record<string, unknown>;
  for (const key of keys) {
    const value = Number(record[key]);
    if (Number.isFinite(value)) {
      return value;
    }
  }
  return null;
}

function stringValue(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function positiveNumber(value: number | null | undefined): number | null {
  return typeof value === "number" && Number.isFinite(value) && value > 0 ? value : null;
}

function normalizeUnit(value: number | null | undefined): number | null {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) {
    return null;
  }
  if (value > 1 && value <= 100) {
    return value / 100;
  }
  return value <= 1 ? value : null;
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatPercentagePoints(value: number): string {
  return `${Math.ceil(value * 100)} percentage points`;
}
