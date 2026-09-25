import {
  Area,
  ComposedChart,
  Label,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export interface FrozenTwinTrajectoryPoint {
  accuracy: number;
  timestamp: string;
}

export interface FrozenTwinComparisonPanelProps {
  liveData: FrozenTwinTrajectoryPoint[];
  frozenData: FrozenTwinTrajectoryPoint[];
  frozenAt?: string;
  gapPp?: number;
  accentColor?: string;
}

interface ComparisonPoint {
  label: string;
  live: number | null;
  frozen: number | null;
  gap: number;
}

const FROZEN_COLOR = "#94a3b8";

function toPercent(value: number): number {
  return value <= 1 ? value * 100 : value;
}

function formatDate(timestamp: string): string {
  const date = new Date(timestamp);
  return Number.isNaN(date.getTime()) ? timestamp : date.toLocaleDateString();
}

function comparisonPoints(
  liveData: FrozenTwinTrajectoryPoint[],
  frozenData: FrozenTwinTrajectoryPoint[],
): ComparisonPoint[] {
  const frozenByTimestamp = new Map(frozenData.map((point) => [point.timestamp, point]));
  const liveByTimestamp = new Map(liveData.map((point) => [point.timestamp, point]));
  const timestamps = Array.from(new Set([...liveByTimestamp.keys(), ...frozenByTimestamp.keys()])).sort();

  return timestamps.map((timestamp) => {
    const live = liveByTimestamp.get(timestamp);
    const frozen = frozenByTimestamp.get(timestamp);
    const liveAccuracy = live ? toPercent(live.accuracy) : null;
    const frozenAccuracy = frozen ? toPercent(frozen.accuracy) : null;
    return {
      label: formatDate(timestamp),
      live: liveAccuracy,
      frozen: frozenAccuracy,
      gap: liveAccuracy !== null && frozenAccuracy !== null ? Math.max(0, liveAccuracy - frozenAccuracy) : 0,
    };
  });
}

function calculatedGap(points: ComparisonPoint[]): number | undefined {
  const final = [...points].reverse().find((point) => point.live !== null && point.frozen !== null);
  return final && final.live !== null && final.frozen !== null ? final.live - final.frozen : undefined;
}

/**
 * Shows the measured live trajectory against its immutable Frozen Twin.
 * It follows TrajectoryChart's card, axis, and tooltip conventions while
 * adding a second series and the visible compounding gap.
 */
export default function FrozenTwinComparisonPanel({
  liveData,
  frozenData,
  frozenAt,
  gapPp,
  accentColor = "var(--copilot-accent)",
}: FrozenTwinComparisonPanelProps) {
  if (frozenData.length === 0) {
    return (
      <section className="copilot-card p-4">
        <h2 className="text-base font-semibold" style={{ color: "var(--copilot-text)" }}>
          Live vs Frozen Twin
        </h2>
        <div
          className="mt-4 grid h-56 place-items-center rounded-md border text-center text-sm"
          style={{ borderColor: "var(--copilot-border)", color: "var(--copilot-text-muted)" }}
        >
          <div>
            <p className="font-medium" style={{ color: "var(--copilot-text)" }}>
              No frozen twin initialized
            </p>
            <p className="mt-1">Initialize a frozen twin to measure compounding.</p>
          </div>
        </div>
      </section>
    );
  }

  const points = comparisonPoints(liveData, frozenData);
  const displayedGap = gapPp ?? calculatedGap(points);
  const frozenLabel = frozenAt ? `Frozen at ${formatDate(frozenAt)}` : "Frozen baseline";

  return (
    <section className="copilot-card p-4">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold" style={{ color: "var(--copilot-text)" }}>
            Live vs Frozen Twin
          </h2>
          <p className="text-sm" style={{ color: "var(--copilot-text-muted)" }}>
            The distance between trajectories is the measured compounding gap.
          </p>
        </div>
        {typeof displayedGap === "number" ? (
          <div className="rounded-md border px-3 py-2 text-right" style={{ borderColor: accentColor }}>
            <div className="text-lg font-semibold" style={{ color: accentColor }}>
              {displayedGap >= 0 ? "+" : ""}{displayedGap.toFixed(1)}pp compounding
            </div>
            <span className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--copilot-text-muted)" }}>
              MODELED
            </span>
          </div>
        ) : null}
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={points} margin={{ top: 12, right: 24, left: 0, bottom: 0 }}>
            <XAxis dataKey="label" stroke="var(--copilot-text-subtle)" tickLine={false} minTickGap={24} />
            <YAxis
              stroke="var(--copilot-text-subtle)"
              tickLine={false}
              width={42}
              domain={[0, 100]}
              tickFormatter={(value: number) => `${value}%`}
            />
            <Tooltip
              formatter={(value: number, name: string) => [`${Number(value).toFixed(1)}%`, name]}
              labelFormatter={(label: string) => `Checkpoint ${label}`}
            />
            <Legend />
            {/* Transparent baseline plus stacked gap shades only the area between curves. */}
            <Area type="monotone" dataKey="frozen" stackId="comparison" stroke="none" fill="transparent" legendType="none" />
            <Area type="monotone" dataKey="gap" stackId="comparison" stroke="none" fill={accentColor} fillOpacity={0.13} legendType="none" />
            <Line type="monotone" dataKey="live" name="LIVE" stroke={accentColor} strokeWidth={2.5} dot={false} connectNulls />
            <Line
              type="monotone"
              dataKey="frozen"
              name="FROZEN"
              stroke={FROZEN_COLOR}
              strokeWidth={2}
              strokeDasharray="6 4"
              dot={false}
              connectNulls
            >
              <Label value={frozenLabel} position="insideTopLeft" fill={FROZEN_COLOR} fontSize={11} />
            </Line>
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
