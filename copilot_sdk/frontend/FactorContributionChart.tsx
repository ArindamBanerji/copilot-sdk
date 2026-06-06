import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TooltipProps } from "recharts";

export interface ContributionEntry {
  factor: string;
  factor_index?: number;
  value: number;
  distance_to_actions?: Record<string, number | null | undefined> | null;
}

export interface FactorContributionChartProps {
  contributions: ContributionEntry[];
  category?: string;
  scoredAction?: string;
  actions?: string[];
  accentColor?: string;
  height?: number;
  title?: string;
}

interface ChartEntry extends ContributionEntry {
  displayValue: number;
  strength: number;
  tone: "supports" | "opposes" | "neutral";
  label: string;
}

const SUPPORT_COLOR = "#0f766e";
const OPPOSE_COLOR = "#be123c";
const NEUTRAL_COLOR = "#64748b";
const AXIS_COLOR = "#94a3b8";

function displayName(name: string): string {
  return name.replace(/_/g, " ");
}

function finiteNumber(value: unknown): number | null {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function classify(value: number): ChartEntry["tone"] {
  if (value > 0.55) {
    return "supports";
  }
  if (value < 0.45) {
    return "opposes";
  }
  return "neutral";
}

function contributionColor(entry: ChartEntry, accentColor?: string): string {
  if (entry.tone === "supports") {
    return accentColor || SUPPORT_COLOR;
  }
  if (entry.tone === "opposes") {
    return OPPOSE_COLOR;
  }
  return NEUTRAL_COLOR;
}

function normalize(contributions: ContributionEntry[]): ChartEntry[] {
  return contributions
    .map((entry) => {
      const value = finiteNumber(entry.value);
      if (value === null) {
        return null;
      }
      const displayValue = value - 0.5;
      return {
        ...entry,
        value,
        displayValue,
        strength: Math.abs(displayValue),
        tone: classify(value),
        label: displayName(entry.factor),
      };
    })
    .filter((entry): entry is ChartEntry => entry !== null)
    .sort((a, b) => b.strength - a.strength);
}

function formatValue(value: number): string {
  return value.toFixed(3);
}

function formatSigned(value: number): string {
  return `${value >= 0 ? "+" : ""}${value.toFixed(3)}`;
}

function ContributionTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload?.length) {
    return null;
  }

  const entry = payload[0]?.payload as ChartEntry | undefined;
  if (!entry) {
    return null;
  }

  const distances = Object.entries(entry.distance_to_actions || {}).filter(([, value]) => finiteNumber(value) !== null);

  return (
    <div className="max-w-xs rounded-md border border-slate-200 bg-white p-3 text-xs shadow-lg">
      <div className="font-semibold capitalize text-slate-950">{entry.label}</div>
      <div className="mt-1 text-slate-600">Value {formatValue(entry.value)}</div>
      <div className="text-slate-600">Centered {formatSigned(entry.displayValue)}</div>
      {distances.length > 0 ? (
        <div className="mt-2 space-y-1">
          <div className="font-semibold text-slate-700">Distance to actions</div>
          {distances.map(([action, value]) => (
            <div key={action} className="flex justify-between gap-4 text-slate-600">
              <span className="capitalize">{displayName(action)}</span>
              <span>{formatValue(Number(value))}</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="mt-2 text-slate-500">No action distances available.</div>
      )}
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-xs text-slate-600">
      <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} aria-hidden="true" />
      {label}
    </span>
  );
}

export default function FactorContributionChart({
  contributions,
  category,
  scoredAction,
  actions,
  accentColor,
  height = 320,
  title = "Factor Contributions",
}: FactorContributionChartProps) {
  const rows = normalize(contributions || []);
  const allNeutral = rows.length > 0 && rows.every((entry) => entry.tone === "neutral");
  const resolvedHeight = Math.max(height, Math.min(520, 92 + rows.length * 34));

  return (
    <section className="copilot-card p-4" data-testid="factor-contribution-chart">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-slate-950">{title}</h2>
          {category || scoredAction ? (
            <p className="mt-1 text-sm text-slate-600">
              {category ? <span className="capitalize">{displayName(category)}</span> : null}
              {category && scoredAction ? " · " : null}
              {scoredAction ? (
                <span>
                  scored action <span className="capitalize">{displayName(scoredAction)}</span>
                </span>
              ) : null}
            </p>
          ) : null}
        </div>
        {actions?.length ? (
          <div className="text-right text-xs text-slate-500">{actions.length} actions compared</div>
        ) : null}
      </div>

      <div className="mt-3 flex flex-wrap gap-3">
        <LegendItem color={accentColor || SUPPORT_COLOR} label="Supports action" />
        <LegendItem color={OPPOSE_COLOR} label="Opposes action" />
        <LegendItem color={NEUTRAL_COLOR} label="Neutral" />
      </div>

      {rows.length === 0 ? (
        <div className="mt-4 rounded-md bg-slate-50 p-4 text-sm text-slate-600">
          No factor contribution data available.
        </div>
      ) : (
        <>
          {allNeutral ? (
            <div className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-600">
              All factors are near neutral for this action.
            </div>
          ) : null}
          <div className="mt-4" style={{ height: resolvedHeight }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={rows} layout="vertical" margin={{ top: 8, right: 24, bottom: 8, left: 24 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
                <XAxis
                  type="number"
                  domain={[-0.5, 0.5]}
                  tickFormatter={formatSigned}
                  tick={{ fill: AXIS_COLOR, fontSize: 12 }}
                />
                <YAxis
                  dataKey="label"
                  type="category"
                  width={150}
                  tick={{ fill: AXIS_COLOR, fontSize: 12 }}
                  tickLine={false}
                />
                <ReferenceLine x={0} stroke="#334155" strokeWidth={1.5} />
                <Tooltip content={<ContributionTooltip />} cursor={{ fill: "rgba(148, 163, 184, 0.12)" }} />
                <Bar dataKey="displayValue" radius={[3, 3, 3, 3]} isAnimationActive={false}>
                  {rows.map((entry) => (
                    <Cell key={entry.factor} fill={contributionColor(entry, accentColor)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </section>
  );
}
