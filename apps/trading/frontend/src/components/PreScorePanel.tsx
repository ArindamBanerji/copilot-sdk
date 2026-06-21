import { useEffect, useMemo, useState } from "react";
import { preScore, prescoreTrade, type PreScoreResponse } from "../api";
import type { PrescoreResponse, TradingCategory } from "../types";
import OptionsFactorPanel from "./OptionsFactorPanel";

const categories: TradingCategory[] = ["trend_following", "mean_reversion", "event_driven", "income_strategy", "scalp_intraday"];

const requiredFactors = [
  "signal_alignment",
  "market_regime",
  "position_sizing",
  "timing_quality",
  "risk_reward_actual",
  "emotional_indicator",
  "signal_confidence",
  "options_delta_exposure",
  "options_iv_percentile",
  "options_gamma_risk",
];

const factorLabels: Record<string, string> = {
  signal_alignment: "Signal alignment",
  market_regime: "Regime fit",
  position_sizing: "Position sizing",
  timing_quality: "Timing",
  risk_reward_actual: "Risk/reward",
  emotional_indicator: "Decision context",
  signal_confidence: "Signal confidence",
  options_delta_exposure: "Options exposure",
  options_iv_percentile: "Options volatility",
  options_gamma_risk: "Options gamma risk",
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

function actionClass(action: string): string {
  if (action === "strong_execution") return "bg-emerald-100 text-emerald-800";
  if (action === "poor_execution" || action === "skip_recommended") return "bg-red-100 text-red-800";
  return "bg-amber-100 text-amber-800";
}

function clamp01(value: number): number {
  if (!Number.isFinite(value)) return 0.5;
  return Math.max(0, Math.min(1, value));
}

function correctnessLabel(value: boolean | null | undefined): string {
  if (value === true) return "correct";
  if (value === false) return "incorrect";
  return "unverified";
}

export default function PreScorePanel({
  ticker,
  category,
  sizePct,
  factors,
}: {
  ticker: string;
  category: TradingCategory;
  sizePct: number;
  factors: Record<string, number>;
}) {
  const [form, setForm] = useState({
    ticker,
    direction: "long",
    strategyTag: "",
    category,
    sizePct: Number.isFinite(sizePct) && sizePct > 0 ? Number(sizePct.toFixed(2)) : 2,
  });
  const [legacyResult, setLegacyResult] = useState<PrescoreResponse | null>(null);
  const [preview, setPreview] = useState<PreScoreResponse | null>(null);
  const [legacyLoading, setLegacyLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setForm((current) => ({
      ...current,
      ticker,
      category,
      sizePct: Number.isFinite(sizePct) && sizePct > 0 ? Number(sizePct.toFixed(2)) : current.sizePct,
    }));
  }, [category, sizePct, ticker]);

  const previewFactors = useMemo(() => {
    const output: Record<string, number> = {};
    for (const name of requiredFactors) {
      output[name] = clamp01(typeof factors[name] === "number" ? factors[name] : 0.5);
    }
    return output;
  }, [factors]);

  async function submitPreview() {
    setPreviewLoading(true);
    setError(null);
    try {
      setPreview(await preScore(category, previewFactors));
    } catch (previewError) {
      setPreview(null);
      setError(previewError instanceof Error ? previewError.message : "Preview score is unavailable.");
    } finally {
      setPreviewLoading(false);
    }
  }

  async function submitLegacy() {
    setLegacyLoading(true);
    setError(null);
    const payload = await prescoreTrade({
      ticker: form.ticker,
      direction: form.direction,
      strategyTag: form.strategyTag || undefined,
      category: form.category,
      sizePct: form.sizePct,
    });
    setLegacyResult(payload);
    setLegacyLoading(false);
    if (!payload) {
      setError("Pre-trade score is unavailable.");
    }
  }

  const recommendation = String(legacyResult?.recommendation || "");
  const regime = String(legacyResult?.regime?.regime || "ranging").toLowerCase();
  const factorEntries = Object.entries(legacyResult?.factors || {});
  const previewAction = String(preview?.recommendedAction || "");
  const previewRegime = String(preview?.currentRegime || "unknown").toLowerCase();
  const similarTrades = preview?.similarTrades || [];

  return (
    <section data-testid="pre-score-panel" className="copilot-card p-4">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">Pre-Trade Score</h2>
          <p className="text-sm trading-muted">Preview the recommendation before recording a trade.</p>
        </div>
        <span data-testid="pre-score-indicator" className="rounded-full border px-3 py-1 text-xs trading-muted" style={{ borderColor: "var(--copilot-border)" }}>
          Preview only - no decision recorded
        </span>
      </div>

      <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide trading-muted">Realtime preview</div>
            <p className="mt-1 text-sm trading-muted">Uses the current category and factor vector from the trade form.</p>
          </div>
          <button
            type="button"
            data-testid="pre-score-button"
            className="copilot-button px-4 py-2 text-sm"
            onClick={() => void submitPreview()}
            disabled={previewLoading}
          >
            {previewLoading ? "Previewing..." : "Preview Score"}
          </button>
        </div>

        {preview ? (
          <div className="mt-4 grid gap-4">
            <div className="trading-grid trading-grid-3">
              <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
                <div className="text-xs trading-muted">Recommended</div>
                <span data-testid="pre-score-action" className={`mt-1 inline-flex rounded-full px-2 py-1 text-xs font-semibold ${actionClass(previewAction)}`}>
                  {label(previewAction)}
                </span>
              </div>
              <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
                <div className="text-xs trading-muted">Confidence</div>
                <div data-testid="pre-score-confidence" className="trading-stat-value">{pct(preview.confidence)}</div>
              </div>
              <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
                <div className="text-xs trading-muted">Current regime</div>
                <div data-testid="pre-score-regime" className="text-sm font-semibold">{label(previewRegime)}</div>
              </div>
            </div>

            {preview.warning ? (
              <div data-testid="pre-score-warning" className="rounded-md border border-amber-300/50 bg-amber-500/10 p-3 text-sm text-amber-100">
                {preview.warning}
              </div>
            ) : null}

            <div className="trading-grid trading-grid-3">
              <div data-testid="pre-score-accuracy" className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
                <div className="text-xs trading-muted">Category accuracy</div>
                <div className="trading-stat-value">{pct(preview.categoryAccuracy)}</div>
              </div>
              <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
                <div className="text-xs trading-muted">Regime accuracy</div>
                <div className="trading-stat-value">{pct(preview.regimeAccuracy)}</div>
              </div>
              <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
                <div className="text-xs trading-muted">Preview status</div>
                <div className="text-sm font-semibold">{preview.message || "preview - no decision recorded"}</div>
              </div>
            </div>

            <div data-testid="pre-score-similar" className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
              <div className="text-xs font-semibold uppercase tracking-wide trading-muted">Similar trades</div>
              {similarTrades.length ? (
                <div className="mt-3 overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="text-left trading-muted">
                        <th className="py-1 pr-3">#</th>
                        <th className="py-1 pr-3">Action</th>
                        <th className="py-1 pr-3">Result</th>
                        <th className="py-1 pr-3">Similarity</th>
                      </tr>
                    </thead>
                    <tbody>
                      {similarTrades.slice(0, 5).map((trade, index) => (
                        <tr key={`${trade.decisionId || "trade"}-${index}`}>
                          <td className="py-1 pr-3">{index + 1}</td>
                          <td className="py-1 pr-3">{label(trade.action)}</td>
                          <td className="py-1 pr-3">{correctnessLabel(trade.isCorrect)}</td>
                          <td className="py-1 pr-3">{pct(trade.similarity)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="mt-2 text-sm trading-muted">No similar verified trades yet.</p>
              )}
            </div>
          </div>
        ) : null}
      </div>

      <div className="mt-4 rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
        <div className="mb-3">
          <div className="text-xs font-semibold uppercase tracking-wide trading-muted">Setup context</div>
          <p className="mt-1 text-sm trading-muted">Optional read-only context score for ticker, strategy, and sizing.</p>
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
          <button type="button" className="copilot-button px-4 py-2 text-sm" onClick={() => void submitLegacy()} disabled={legacyLoading || !form.ticker.trim()}>
            {legacyLoading ? "Scoring..." : "Score Before Trade"}
          </button>
          {!legacyResult && !error ? <span className="text-sm trading-muted">Run a setup context score before recording an executed decision.</span> : null}
          {error ? <span className="text-sm trading-negative">{error}</span> : null}
        </div>

        {legacyResult ? (
          <div className="mt-4 grid gap-4">
            <div className="trading-grid trading-grid-3">
              <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
                <div className="text-xs trading-muted">Confidence</div>
                <div className="trading-stat-value">{pct(legacyResult.confidence)}</div>
              </div>
              <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
                <div className="text-xs trading-muted">Regime</div>
                <span className={`mt-1 inline-flex rounded-full px-2 py-1 text-xs font-semibold ${regimeClass(regime)}`}>{regime.toUpperCase()}</span>
              </div>
              <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
                <div className="text-xs trading-muted">Category</div>
                <div className="text-sm font-semibold">{label(legacyResult.category)}</div>
              </div>
            </div>

            {legacyResult.warnings?.length ? (
              <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
                <div className="text-xs font-semibold uppercase tracking-wide trading-muted">Warnings</div>
                <ul className="mt-2 grid gap-1 text-sm">
                  {legacyResult.warnings.map((warning) => (
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
              <p className="mt-2 text-sm leading-6">{legacyResult.evidence || "Evidence is unavailable for this setup."}</p>
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

            {legacyResult.optionsFactors ? (
              <OptionsFactorPanel
                optionsFactors={legacyResult.optionsFactors}
                analyticsOnly={legacyResult.optionsAnalyticsOnly !== false}
              />
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  );
}
