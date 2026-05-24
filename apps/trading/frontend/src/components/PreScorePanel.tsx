import { useEffect, useState } from "react";
import { prescoreTrade } from "../api";
import type { PrescoreResponse, TradingCategory } from "../types";
import OptionsFactorPanel from "./OptionsFactorPanel";

const categories: TradingCategory[] = ["trend_following", "mean_reversion", "event_driven", "income_strategy", "scalp_intraday"];

const factorLabels: Record<string, string> = {
  signal_alignment: "Signal alignment",
  market_regime: "Regime fit",
  position_sizing: "Position sizing",
  timing_quality: "Timing",
  risk_reward_actual: "Risk/reward",
  emotional_indicator: "Decision context",
  signal_confidence: "Signal confidence",
};

function label(value: string | undefined | null): string {
  return value ? value.replace(/_/g, " ") : "-";
}

function pct(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "-";
}

function recommendationClass(value: string): string {
  if (value === "proceed") return "bg-emerald-100 text-emerald-800";
  if (value === "skip") return "bg-red-100 text-red-800";
  return "bg-amber-100 text-amber-800";
}

function regimeClass(regime: string): string {
  if (regime === "trending") return "bg-emerald-100 text-emerald-800";
  if (regime === "volatile") return "bg-red-100 text-red-800";
  return "bg-amber-100 text-amber-800";
}

export default function PreScorePanel({
  ticker,
  category,
  sizePct,
}: {
  ticker: string;
  category: TradingCategory;
  sizePct: number;
}) {
  const [form, setForm] = useState({
    ticker,
    direction: "long",
    strategyTag: "",
    category,
    sizePct: Number.isFinite(sizePct) && sizePct > 0 ? Number(sizePct.toFixed(2)) : 2,
  });
  const [result, setResult] = useState<PrescoreResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setForm((current) => ({
      ...current,
      ticker,
      category,
      sizePct: Number.isFinite(sizePct) && sizePct > 0 ? Number(sizePct.toFixed(2)) : current.sizePct,
    }));
  }, [category, sizePct, ticker]);

  async function submit() {
    setLoading(true);
    setError(null);
    const payload = await prescoreTrade({
      ticker: form.ticker,
      direction: form.direction,
      strategyTag: form.strategyTag || undefined,
      category: form.category,
      sizePct: form.sizePct,
    });
    setResult(payload);
    setLoading(false);
    if (!payload) {
      setError("Pre-trade score is unavailable.");
    }
  }

  const recommendation = String(result?.recommendation || "");
  const regime = String(result?.regime?.regime || "ranging").toLowerCase();
  const factorEntries = Object.entries(result?.factors || {});

  return (
    <section className="copilot-card p-4">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">Pre-Trade Score</h2>
          <p className="text-sm trading-muted">Decision-quality guidance for a potential setup before it enters trade history.</p>
        </div>
        {result ? (
          <span className={`rounded-full px-3 py-1 text-xs font-semibold ${recommendationClass(recommendation)}`}>
            {recommendation.toUpperCase()}
          </span>
        ) : null}
      </div>

      <div className="grid gap-3 md:grid-cols-5">
        <label className="text-sm">
          <span className="mb-1 block trading-muted">Pre-score ticker</span>
          <input
            className="w-full rounded-md border px-3 py-2"
            placeholder="AAPL"
            style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)" }}
            value={form.ticker}
            onChange={(event) => setForm((current) => ({ ...current, ticker: event.target.value.toUpperCase() }))}
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block trading-muted">Pre-score direction</span>
          <select
            className="w-full rounded-md border px-3 py-2"
            style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)" }}
            value={form.direction}
            onChange={(event) => setForm((current) => ({ ...current, direction: event.target.value }))}
          >
            <option value="long">long</option>
            <option value="short">short</option>
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block trading-muted">Strategy tag</span>
          <input
            className="w-full rounded-md border px-3 py-2"
            placeholder="rsi_oversold"
            style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)" }}
            value={form.strategyTag}
            onChange={(event) => setForm((current) => ({ ...current, strategyTag: event.target.value }))}
          />
        </label>
        <label className="text-sm">
          <span className="mb-1 block trading-muted">Pre-score category</span>
          <select
            className="w-full rounded-md border px-3 py-2"
            style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)" }}
            value={form.category}
            onChange={(event) => setForm((current) => ({ ...current, category: event.target.value as TradingCategory }))}
          >
            {categories.map((item) => (
              <option key={item} value={item}>
                {label(item)}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block trading-muted">Size %</span>
          <input
            className="w-full rounded-md border px-3 py-2"
            type="number"
            min={0}
            step={0.1}
            style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)" }}
            value={form.sizePct}
            onChange={(event) => setForm((current) => ({ ...current, sizePct: Number(event.target.value) }))}
          />
        </label>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button type="button" className="copilot-button px-4 py-2 text-sm" onClick={() => void submit()} disabled={loading || !form.ticker.trim()}>
          {loading ? "Scoring..." : "Score Before Trade"}
        </button>
        {!result && !error ? <span className="text-sm trading-muted">Run a pre-trade score before recording an executed decision.</span> : null}
        {error ? <span className="text-sm trading-negative">{error}</span> : null}
      </div>

      {result ? (
        <div className="mt-4 grid gap-4">
          <div className="trading-grid trading-grid-3">
            <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
              <div className="text-xs trading-muted">Confidence</div>
              <div className="trading-stat-value">{pct(result.confidence)}</div>
            </div>
            <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
              <div className="text-xs trading-muted">Regime</div>
              <span className={`mt-1 inline-flex rounded-full px-2 py-1 text-xs font-semibold ${regimeClass(regime)}`}>{regime.toUpperCase()}</span>
            </div>
            <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
              <div className="text-xs trading-muted">Category</div>
              <div className="text-sm font-semibold">{label(result.category)}</div>
            </div>
          </div>

          {result.warnings?.length ? (
            <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
              <div className="text-xs font-semibold uppercase tracking-wide trading-muted">Warnings</div>
              <ul className="mt-2 grid gap-1 text-sm">
                {result.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="rounded-md border p-3 text-sm trading-muted" style={{ borderColor: "var(--copilot-border)" }}>
              No pre-trade warnings for this setup.
            </div>
          )}

          <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
            <div className="text-xs font-semibold uppercase tracking-wide trading-muted">Evidence</div>
            <p className="mt-2 text-sm leading-6">{result.evidence || "Evidence is unavailable for this setup."}</p>
          </div>

          {factorEntries.length ? (
            <div className="grid gap-2 md:grid-cols-2">
              {factorEntries.map(([name, value]) => (
                <div key={name} className="rounded-md p-3" style={{ background: "var(--copilot-surface-muted)" }}>
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold">{factorLabels[name] || label(name)}</span>
                    <span>{pct(value)}</span>
                  </div>
                  <div className="mt-2 h-2 rounded-full" style={{ background: "var(--copilot-border)" }}>
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${Math.max(0, Math.min(1, value)) * 100}%`,
                        background: "var(--copilot-primary)",
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : null}

          {result.optionsFactors ? (
            <OptionsFactorPanel
              optionsFactors={result.optionsFactors}
              analyticsOnly={result.optionsAnalyticsOnly !== false}
            />
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
