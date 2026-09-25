import {
  Area,
  AreaChart,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export interface TrajectoryPoint {
  decisions: number;
  iks: number;
  winRate: number;
  /** Unix seconds/milliseconds or an ISO timestamp from the trajectory API. */
  timestamp?: number | string;
}

export interface Annotation {
  decision: number;
  type: "disruption" | "milestone";
  label: string;
  description: string;
  recovery?: string;
}

export interface TrajectoryChartProps {
  points: TrajectoryPoint[];
  currentIks: number;
  currentWinRate: number;
  switchingCostLine?: number;
  annotations?: Annotation[];
  narrative: string;
  decisionsTotal: number;
  daysActive: number;
  /** Consecutive trajectory points farther apart than this form a verification gap. */
  gapThresholdDays?: number;
  /** Show the shaded and labelled no-verification interval. */
  showGapAnnotation?: boolean;
}

interface VerificationGap {
  startDecision: number;
  endDecision: number;
  winRatePct: number;
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function timestampMilliseconds(timestamp: TrajectoryPoint["timestamp"]): number | undefined {
  if (typeof timestamp === "number" && Number.isFinite(timestamp)) {
    return timestamp < 1_000_000_000_000 ? timestamp * 1000 : timestamp;
  }
  if (typeof timestamp === "string") {
    const parsed = Date.parse(timestamp);
    return Number.isNaN(parsed) ? undefined : parsed;
  }
  return undefined;
}

function findVerificationGaps(points: TrajectoryPoint[], thresholdDays: number): VerificationGap[] {
  const thresholdMilliseconds = thresholdDays * 24 * 60 * 60 * 1000;
  return points.flatMap((point, index) => {
    if (index === 0) return [];
    const previous = points[index - 1];
    const currentTimestamp = timestampMilliseconds(point.timestamp);
    const previousTimestamp = timestampMilliseconds(previous.timestamp);
    if (currentTimestamp === undefined || previousTimestamp === undefined) return [];
    const elapsed = currentTimestamp - previousTimestamp;
    if (elapsed <= thresholdMilliseconds) return [];
    return [{
      startDecision: previous.decisions,
      endDecision: point.decisions,
      winRatePct: previous.winRate * 100,
    }];
  });
}

export default function TrajectoryChart({
  points,
  currentIks,
  currentWinRate,
  switchingCostLine,
  annotations = [],
  narrative,
  decisionsTotal,
  daysActive,
  gapThresholdDays = 7,
  showGapAnnotation = true,
}: TrajectoryChartProps) {
  const chartData = points.map((point) => ({
    ...point,
    winRatePct: point.winRate * 100,
  }));
  const verificationGaps = findVerificationGaps(points, gapThresholdDays);

  return (
    <section className="copilot-card p-4">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold" style={{ color: "var(--copilot-text)" }}>
            Trajectory
          </h2>
          <p className="text-sm" style={{ color: "var(--copilot-text-muted)" }}>
            {narrative}
          </p>
        </div>
      </div>

      <div className="mb-4 grid gap-3 md:grid-cols-4">
        <Stat label="Current IKS" value={currentIks.toFixed(1)} />
        <Stat label="Win Rate" value={formatPercent(currentWinRate)} />
        <Stat label="Decisions" value={decisionsTotal.toString()} />
        <Stat label="Days Active" value={daysActive.toFixed(1)} />
      </div>

      {chartData.length === 0 ? (
        <div
          className="grid h-72 place-items-center rounded-md text-sm"
          style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-text-muted)" }}
        >
          No trajectory points available.
        </div>
      ) : (
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="iksFill" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="5%" stopColor="var(--copilot-chart-iks)" stopOpacity={0.28} />
                  <stop offset="95%" stopColor="var(--copilot-chart-iks)" stopOpacity={0.03} />
                </linearGradient>
                <linearGradient id="winRateFill" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="5%" stopColor="var(--copilot-chart-win-rate)" stopOpacity={0.24} />
                  <stop offset="95%" stopColor="var(--copilot-chart-win-rate)" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <XAxis dataKey="decisions" stroke="var(--copilot-text-subtle)" tickLine={false} />
              <YAxis stroke="var(--copilot-text-subtle)" tickLine={false} width={36} domain={[0, 100]} />
              <Tooltip
                formatter={(value: number, name: string) => [
                  name === "winRatePct" ? `${Number(value).toFixed(0)}%` : Number(value).toFixed(1),
                  name === "winRatePct" ? "Win rate" : "IKS",
                ]}
                labelFormatter={(label) => `Decision ${label}`}
              />
              {showGapAnnotation
                ? verificationGaps.map((gap) => (
                    <ReferenceArea
                      key={`verification-gap-area-${gap.startDecision}-${gap.endDecision}`}
                      x1={gap.startDecision}
                      x2={gap.endDecision}
                      fill="var(--copilot-text-subtle)"
                      fillOpacity={0.12}
                      ifOverflow="extendDomain"
                      label={{ value: "No verifications", position: "insideTop", fill: "var(--copilot-text-muted)", fontSize: 11 }}
                    />
                  ))
                : null}
              {typeof switchingCostLine === "number" ? (
                <ReferenceLine
                  y={switchingCostLine}
                  stroke="var(--copilot-warning)"
                  strokeDasharray="4 4"
                  label="Switching cost"
                />
              ) : null}
              <Area
                type="monotone"
                dataKey="iks"
                stroke="var(--copilot-chart-iks)"
                fill="url(#iksFill)"
                strokeWidth={2}
              />
              {showGapAnnotation
                ? verificationGaps.map((gap) => (
                    <ReferenceLine
                      key={`verification-gap-line-${gap.startDecision}-${gap.endDecision}`}
                      segment={[
                        { x: gap.startDecision, y: gap.winRatePct },
                        { x: gap.endDecision, y: gap.winRatePct },
                      ]}
                      stroke="var(--copilot-text-muted)"
                      strokeDasharray="6 4"
                      strokeWidth={2}
                    />
                  ))
                : null}
              <Area
                type="monotone"
                dataKey="winRatePct"
                stroke="var(--copilot-chart-win-rate)"
                fill="url(#winRateFill)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {annotations.length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {annotations.map((annotation) => (
            <div
              key={`${annotation.type}-${annotation.decision}-${annotation.label}`}
              className="rounded-md border px-3 py-2 text-xs"
              style={{
                borderColor:
                  annotation.type === "disruption"
                    ? "var(--copilot-warning)"
                    : "var(--copilot-accent)",
                color: "var(--copilot-text)",
              }}
            >
              <div className="font-semibold">
                {annotation.label} · decision {annotation.decision}
              </div>
              <div style={{ color: "var(--copilot-text-muted)" }}>{annotation.description}</div>
              {annotation.recovery ? <div>{annotation.recovery}</div> : null}
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border px-3 py-2" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs" style={{ color: "var(--copilot-text-muted)" }}>
        {label}
      </div>
      <div className="text-lg font-semibold" style={{ color: "var(--copilot-text)" }}>
        {value}
      </div>
    </div>
  );
}
