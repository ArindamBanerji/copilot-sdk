import type { OptionsFactors } from "../types";

type FactorKey = keyof OptionsFactors;

const rows: Array<{ key: FactorKey; label: string; low: string; mid: string; high: string }> = [
  {
    key: "ivRvRatio",
    label: "IV/RV ratio",
    low: "Cheap premium context",
    mid: "Neutral/default context",
    high: "High/expensive premium context",
  },
  {
    key: "greeksExposure",
    label: "Greeks exposure",
    low: "Misaligned exposure context",
    mid: "Neutral/default exposure",
    high: "Aligned exposure context",
  },
  {
    key: "thetaEfficiency",
    label: "Theta efficiency",
    low: "Low theta efficiency",
    mid: "Neutral/default efficiency",
    high: "High theta efficiency",
  },
];

function pct(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "-";
}

function textFor(value: number | null | undefined, row: (typeof rows)[number]): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return row.mid;
  if (value > 0.65) return row.high;
  if (value < 0.35) return row.low;
  return row.mid;
}

function hasValues(optionsFactors?: OptionsFactors | null): boolean {
  return rows.some((row) => typeof optionsFactors?.[row.key] === "number");
}

export default function OptionsFactorPanel({
  optionsFactors,
  analyticsOnly = true,
  showEmpty = false,
}: {
  optionsFactors?: OptionsFactors | null;
  analyticsOnly?: boolean;
  showEmpty?: boolean;
}) {
  const hasData = hasValues(optionsFactors);
  if (!hasData && !showEmpty) return null;

  return (
    <section className="copilot-card p-4" aria-label="Options Factors">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold">Options Factors</h3>
          <p className="mt-1 text-sm trading-muted">
            {analyticsOnly ? "Analytics-only - not scored by the engine." : "Options analytics context."}
          </p>
        </div>
        {analyticsOnly ? (
          <span className="rounded-full px-3 py-1 text-xs font-semibold" style={{ background: "var(--copilot-surface-muted)" }}>
            analytics-only
          </span>
        ) : null}
      </div>

      {!hasData ? (
        <p className="mt-4 rounded-md p-3 text-sm trading-muted" style={{ background: "var(--copilot-surface-muted)" }}>
          No options data available.
        </p>
      ) : (
        <div className="mt-4 grid gap-2 md:grid-cols-3">
          {rows.map((row) => {
            const value = optionsFactors?.[row.key];
            const normalized = typeof value === "number" && Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : 0.5;
            return (
              <div key={row.key} className="rounded-md p-3" style={{ background: "var(--copilot-surface-muted)" }}>
                <div className="flex items-center justify-between gap-3 text-xs">
                  <span className="font-semibold">{row.label}</span>
                  <span>{pct(value)}</span>
                </div>
                <div className="mt-2 h-2 rounded-full" style={{ background: "var(--copilot-border)" }}>
                  <div className="h-full rounded-full" style={{ width: `${normalized * 100}%`, background: "var(--copilot-primary)" }} />
                </div>
                <p className="mt-2 text-xs trading-muted">{textFor(value, row)}</p>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
