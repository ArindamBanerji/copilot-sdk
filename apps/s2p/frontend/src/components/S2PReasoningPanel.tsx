import type { FactorMap } from "../types";

function label(name: string): string {
  return name
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function color(value: number): string {
  if (value >= 0.7) return "bg-red-500";
  if (value >= 0.4) return "bg-amber-500";
  return "bg-emerald-500";
}

export function S2PReasoningPanel({
  factors,
  title = "Factor Reasoning"
}: {
  factors?: FactorMap | Record<string, number>;
  title?: string;
}) {
  const rows = Object.entries(factors || {})
    .filter(([, value]) => typeof value === "number" && Number.isFinite(value))
    .sort((a, b) => Number(b[1]) - Number(a[1]));

  return (
    <article className="copilot-card p-5">
      <h2 className="text-lg font-semibold text-slate-950">{title}</h2>
      {rows.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">No factor values available.</p>
      ) : (
        <div className="mt-4 space-y-3">
          {rows.map(([name, value]) => {
            const pct = Math.round(Number(value) * 100);
            return (
              <div key={name}>
                <div className="flex items-center justify-between gap-3 text-sm">
                  <span className="font-medium text-slate-700">{label(name)}</span>
                  <span className="font-semibold text-slate-950">{pct}%</span>
                </div>
                <div className="mt-1 h-2 rounded-full bg-slate-100">
                  <div
                    className={`h-2 rounded-full ${color(Number(value))}`}
                    style={{ width: `${Math.max(0, Math.min(100, pct))}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </article>
  );
}
