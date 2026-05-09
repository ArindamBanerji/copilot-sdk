import type { Analytics } from "../types";

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function num(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function pct(value: unknown): string {
  return typeof value === "number" ? `${(value * 100).toFixed(0)}%` : "-";
}

export default function CounterfactualCard({ analytics }: { analytics?: Analytics }) {
  const counterfactual = asRecord(analytics?.counterfactual);
  const tradesSkipped = num(counterfactual.tradesSkipped) ?? num(counterfactual.skippedTradeCount);
  const dollarsSaved = num(counterfactual.dollarsSaved);
  const explanation = typeof counterfactual.explanation === "string"
    ? counterfactual.explanation
    : typeof counterfactual.scenario === "string"
      ? counterfactual.scenario
      : "No counterfactual scenario is available yet.";

  return (
    <section className="copilot-card p-4">
      <h2 className="text-base font-semibold">Counterfactual</h2>
      <p className="mt-1 text-sm trading-muted">{explanation}</p>
      <div className="mt-4 grid gap-3 md:grid-cols-4">
        <Stat label="Dollars saved" value={typeof dollarsSaved === "number" ? `$${dollarsSaved.toLocaleString()}` : "-"} />
        <Stat label="Trades skipped" value={typeof tradesSkipped === "number" ? String(tradesSkipped) : "-"} />
        <Stat label="Original win rate" value={pct(counterfactual.originalWinRate)} />
        <Stat label="Adjusted win rate" value={pct(counterfactual.adjustedWinRate)} />
      </div>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border px-3 py-2" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs trading-muted">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}
