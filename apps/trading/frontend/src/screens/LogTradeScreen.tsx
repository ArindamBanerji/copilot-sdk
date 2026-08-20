import { useEffect, useMemo, useState } from "react";
import { ReasoningPanel, ScoreResultCard, type RewardLine } from "../../../../../copilot_sdk/frontend";
import {
  getAnalytics,
  getFingerprint,
  getMarketSnapshot,
  getRegimeCurrent,
  getSimilarTrades,
  learnTrade,
  saveTradeMetadata,
  scoreTrade,
} from "../api";
import EngineAssessment from "../components/EngineAssessment";
import EvidencePanel from "../components/EvidencePanel";
import OptionsFactorPanel from "../components/OptionsFactorPanel";
import PositionSizer, { computePositionSizing } from "../components/PositionSizer";
import PreScorePanel from "../components/PreScorePanel";
import ResearchChecklist from "../components/ResearchChecklist";
import SimilarTradesPanel from "../components/SimilarTradesPanel";
import TickerLookup from "../components/TickerLookup";
import { SituationalAbstentionBanner } from "../components/DemoBeatPanels";
import type {
  Analytics,
  FingerprintResponse,
  MarketSnapshot,
  ScoreResponse,
  SimilarTrade,
  TickerData,
  TradeFormState,
  TradingAction,
  TradingCategory,
} from "../types";

const categories: TradingCategory[] = ["trend_following", "mean_reversion", "event_driven", "income_strategy", "scalp_intraday"];
const directions: TradingAction[] = ["strong_execution", "partial_execution", "poor_execution"];
const thesisTypes = ["momentum", "event", "mean_reversion", "technical", "fundamental"];
const timeframes: TradeFormState["timeframe"][] = ["intraday", "swing", "position", "long"];
const tradingActionNames = ["strong_execution", "partial_execution", "poor_execution"];
const tradingActionLabels: Record<string, string> = {
  strong_execution: "Strong execution",
  partial_execution: "Partial execution",
  poor_execution: "Poor execution",
};
const tradingFactorNames = [
  "signal_alignment",
  "market_regime",
  "position_sizing",
  "timing_quality",
  "risk_reward_actual",
  "emotional_indicator",
];
const tradingFactorLabels: Record<string, string> = {
  signal_alignment: "Signal alignment",
  market_regime: "Market regime",
  position_sizing: "Position sizing",
  timing_quality: "Timing quality",
  risk_reward_actual: "Risk/reward actual",
  emotional_indicator: "Decision context",
};

const initialForm: TradeFormState = {
  ticker: "MSFT",
  direction: "strong_execution",
  category: "trend_following",
  thesisType: "momentum",
  timeframe: "swing",
  researchChecklist: [false, false, false, false, false],
  signal_alignment: 3,
  shares: 10,
  entryPrice: 0,
  portfolioValue: 250000,
  stopLoss: 0,
  target: 0,
};

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function timeframeFactor(timeframe: TradeFormState["timeframe"]): number {
  return { intraday: 0.1, swing: 0.4, position: 0.7, long: 0.9 }[timeframe];
}

function computeTechnicalSignal(ticker?: TickerData): number {
  if (!ticker || ticker.source === "unknown") {
    return 0.3;
  }
  const rsi = typeof ticker.rsi === "number" ? ticker.rsi : 50;
  const change = typeof ticker.change30dPct === "number" ? ticker.change30dPct : 0;
  return clamp(
    0.3 +
      (ticker.above50ma ? 0.25 : 0) +
      clamp((rsi - 30) / 40, 0, 1) * 0.25 +
      clamp(change / 10, -0.2, 0.2),
    0,
    1,
  );
}

function computeMarketRegime(snapshot?: MarketSnapshot): number {
  const vixValue = typeof snapshot?.vix?.value === "number" ? snapshot.vix.value : snapshot?.vix?.price;
  const spyChange = typeof snapshot?.spy?.change30dPct === "number" ? snapshot.spy.change30dPct : 0;
  const vixScore = typeof vixValue !== "number" ? 0.55 : vixValue < 18 ? 0.75 : vixValue > 25 ? 0.25 : 0.55;
  return clamp(vixScore + clamp(spyChange / 20, -0.1, 0.1), 0, 1);
}

function getSimilarAction(trade: SimilarTrade): string | undefined {
  const record = trade as SimilarTrade & Record<string, unknown>;
  for (const key of ["actionTaken", "action_taken", "action", "actualAction", "confirmedAction", "recommendedAction", "scoreAction"]) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) {
      return value;
    }
  }
  return undefined;
}

function isOptionsContext(form: TradeFormState): boolean {
  if (form.category === "income_strategy") return true;
  const text = `${form.thesisType} ${form.category}`.toLowerCase().replace(/[-\s]/g, "_");
  return [
    "option",
    "straddle",
    "strangle",
    "iron_condor",
    "credit",
    "debit",
    "covered",
    "wheel",
    "calendar",
    "butterfly",
    "premium",
    "iv",
  ].some((token) => text.includes(token));
}

export default function LogTradeScreen() {
  const [form, setForm] = useState<TradeFormState>(initialForm);
  const [ticker, setTicker] = useState<TickerData | undefined>();
  const [market, setMarket] = useState<MarketSnapshot | null>(null);
  const [fingerprint, setFingerprint] = useState<FingerprintResponse | null>(null);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [score, setScore] = useState<ScoreResponse | undefined>();
  const [evidenceReady, setEvidenceReady] = useState(false);
  const [similar, setSimilar] = useState<SimilarTrade[]>([]);
  const [similarCount, setSimilarCount] = useState(0);
  const [rewardLine, setRewardLine] = useState<RewardLine | undefined>();
  const [iksDelta, setIksDelta] = useState<number | undefined>();
  const [initialReady, setInitialReady] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getMarketSnapshot(), getFingerprint(), getAnalytics()])
      .then(([nextMarket, nextFingerprint, nextAnalytics]) => {
        if (cancelled) return;
        setMarket(nextMarket);
        setFingerprint(nextFingerprint);
        setAnalytics(nextAnalytics);
      })
      .catch((loadError) => {
        console.debug("log trade context unavailable", loadError);
      })
      .finally(() => {
        if (!cancelled) setInitialReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (ticker?.price && !form.entryPrice) {
      setForm((current) => ({ ...current, entryPrice: ticker.price || current.entryPrice }));
    }
  }, [ticker, form.entryPrice]);

  const sizing = useMemo(
    () =>
      computePositionSizing({
        shares: form.shares,
        price: form.entryPrice,
        portfolioValue: form.portfolioValue,
        stopLoss: form.stopLoss,
        target: form.target,
      }),
    [form.entryPrice, form.portfolioValue, form.shares, form.stopLoss, form.target],
  );

  const factors = useMemo(
    () => ({
      signal_alignment: clamp(form.signal_alignment / 5, 0, 1),
      market_regime: form.researchChecklist.filter(Boolean).length / 5,
      position_sizing: computeTechnicalSignal(ticker),
      timing_quality: clamp(sizing.exposurePct / 100, 0, 1),
      risk_reward_actual: timeframeFactor(form.timeframe),
      emotional_indicator: computeMarketRegime(market ?? undefined),
    }),
    [form.signal_alignment, form.researchChecklist, form.timeframe, market, sizing.exposurePct, ticker],
  );

  function update<K extends keyof TradeFormState>(key: K, value: TradeFormState[K]) {
    setEvidenceReady(false);
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function submitScore() {
    setError(null);
    setStatus("Scoring trade...");
    setEvidenceReady(false);
    setRewardLine(undefined);
    setIksDelta(undefined);
    try {
      let currentRegime: string | null = null;
      try {
        const regimePayload = await getRegimeCurrent();
        currentRegime = typeof regimePayload.regime === "string" ? regimePayload.regime : null;
      } catch (regimeError) {
        console.debug("Regime context unavailable for score metadata", regimeError);
      }
      const scoreContext = {
        ticker: form.ticker,
        thesis_type: form.thesisType,
        timeframe: form.timeframe,
        current_regime: currentRegime,
      };
      const result = await scoreTrade({
        category: form.category,
        factors,
        context: scoreContext,
        metadata: {
          current_regime: currentRegime,
          context: scoreContext,
        },
      });
      setScore(result);
      await saveTradeMetadata({
        decisionId: result.decisionId,
        ticker: form.ticker,
        direction: form.direction,
        category: form.category,
        thesisType: form.thesisType,
        timeframe: form.timeframe,
        currentRegime,
        researchChecklist: form.researchChecklist,
        researchDepth: factors.market_regime,
        signal_alignment: factors.signal_alignment,
        technicalSignal: factors.position_sizing,
        positionSize: factors.timing_quality,
        timeHorizon: factors.risk_reward_actual,
        marketRegime: factors.emotional_indicator,
        shares: form.shares,
        entryPrice: form.entryPrice,
        portfolioValue: form.portfolioValue,
        exposurePct: sizing.exposurePct,
        stopLoss: form.stopLoss || null,
        target: form.target || null,
        rrRatio: sizing.rrRatio,
        exitPrice: null,
        pnlPct: null,
        pnlDollars: null,
        holdDays: null,
        outcome: null,
        actionTaken: result.action,
        createdAt: new Date().toISOString(),
      });
      setEvidenceReady(true);
      const similarPayload = await getSimilarTrades(
        {
          category: form.category,
          signal_alignment: factors.signal_alignment,
          researchDepth: factors.market_regime,
          technicalSignal: factors.position_sizing,
          positionSize: factors.timing_quality,
          timeHorizon: factors.risk_reward_actual,
          marketRegime: factors.emotional_indicator,
        },
        5,
      );
      setSimilar(similarPayload.similar);
      setSimilarCount(similarPayload.count);
      setStatus("Score ready. Review the engine assessment and similar trades before confirming.");
    } catch (submitError) {
      setEvidenceReady(false);
      setError(submitError instanceof Error ? submitError.message : "Score failed");
      setStatus(null);
    }
  }

  async function confirm(decisionId: string, action = score?.action || form.direction) {
    setError(null);
    try {
      const learn = await learnTrade(decisionId, action, "confirmed");
      if (typeof learn.reward === "number") {
        setRewardLine({
          reward: learn.reward,
          previousReward: learn.previousReward ?? null,
          rewardMultiplier: learn.rewardMultiplier ?? 1,
        });
      }
      if (typeof learn.iksAfter === "number" && typeof learn.iksBefore === "number") {
        setIksDelta(learn.iksAfter - learn.iksBefore);
      } else if (typeof learn.iksDelta === "number") {
        setIksDelta(learn.iksDelta);
      }
      setStatus("Trade confirmed and learner updated.");
    } catch (confirmError) {
      setError(confirmError instanceof Error ? confirmError.message : "Learn failed");
    }
  }

  return (
    <div data-screen-ready={String(initialReady)} className="flex flex-col gap-4">
      <div>
        <h2 className="text-2xl font-semibold">Log Trade</h2>
        <p className="text-sm trading-muted">Score a trade with research, sizing, market context, and similar setups.</p>
      </div>

      <TickerLookup
        value={form.ticker}
        onChange={(value) => update("ticker", value)}
        onTicker={setTicker}
      />

      {isOptionsContext(form) ? <OptionsFactorPanel showEmpty analyticsOnly /> : null}

      <section className="copilot-card p-4">
        <h2 className="text-base font-semibold">Trade Thesis</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <Select label="Direction" value={form.direction} options={directions} onChange={(value) => update("direction", value as TradingAction)} />
          <Select label="Category" value={form.category} options={categories} onChange={(value) => update("category", value as TradingCategory)} />
          <Select label="Thesis" value={form.thesisType} options={thesisTypes} onChange={(value) => update("thesisType", value)} />
          <Select label="Timeframe" value={form.timeframe} options={timeframes} onChange={(value) => update("timeframe", value as TradeFormState["timeframe"])} />
          <label className="text-sm">
            <span className="mb-1 block trading-muted">Signal alignment</span>
            <input
              type="range"
              min={1}
              max={5}
              value={form.signal_alignment}
              onChange={(event) => update("signal_alignment", Number(event.target.value))}
              className="w-full"
            />
            <span className="text-xs trading-muted">{form.signal_alignment}/5</span>
          </label>
          <label className="text-sm">
            <span className="mb-1 block trading-muted">Entry Price</span>
            <input
              type="number"
              className="w-full rounded-md border px-3 py-2"
              style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)" }}
              value={form.entryPrice}
              onChange={(event) => update("entryPrice", Number(event.target.value))}
            />
          </label>
        </div>
      </section>

      <ResearchChecklist value={form.researchChecklist} onChange={(value) => update("researchChecklist", value)} />
      <SituationalAbstentionBanner />
      <PositionSizer
        shares={form.shares}
        price={form.entryPrice}
        portfolioValue={form.portfolioValue}
        stopLoss={form.stopLoss}
        target={form.target}
        onChange={(field, value) => update(field, value)}
      />

      <section className="copilot-card p-4">
        <div>
          <div>
            <h2 className="text-base font-semibold">Factor Vector</h2>
            <p className="text-sm trading-muted">signal alignment, regime, sizing, timing, risk/reward, emotion</p>
          </div>
        </div>
        <div className="mt-4 grid gap-2 md:grid-cols-6">
          {Object.entries(factors).map(([name, value]) => (
            <div key={name} className="rounded-md border p-2" style={{ borderColor: "var(--copilot-border)" }}>
              <div className="text-xs trading-muted">{name.replace(/_/g, " ")}</div>
              <div className="font-semibold">{value.toFixed(2)}</div>
            </div>
          ))}
        </div>
      </section>

      <PreScorePanel ticker={form.ticker} category={form.category} sizePct={sizing.exposurePct || 2} factors={factors} />

      <section className="copilot-card p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold">Record Trade Decision</h2>
            <p className="text-sm trading-muted">Submit only when you are ready to record this decision.</p>
          </div>
          <button type="button" className="copilot-button px-4 py-2 text-sm" onClick={submitScore}>
            Score This Trade
          </button>
        </div>
      </section>

      {status ? <div className="rounded-md border p-3 text-sm trading-muted" style={{ borderColor: "var(--copilot-border)" }}>{status}</div> : null}
      {error ? <div className="rounded-md border p-3 text-sm trading-negative" style={{ borderColor: "var(--copilot-border)" }}>{error}</div> : null}

      {score ? (
        <>
          <EngineAssessment factors={factors} fingerprint={fingerprint ?? undefined} analytics={analytics ?? undefined} similarCount={similarCount} />
          <SimilarTradesPanel similar={similar} count={similarCount} />
          <ScoreResultCard
            result={score}
            onConfirm={(decisionId) => void confirm(decisionId)}
            onOverride={(decisionId, action) => void confirm(decisionId, action)}
            rewardLine={rewardLine}
            iksDelta={iksDelta}
          />
          {score.decisionId && evidenceReady ? <EvidencePanel tradeId={score.decisionId} /> : null}
          <ReasoningPanel
            scoreResult={score}
            similarItems={similar.map((trade) => ({
              ...trade,
              action: getSimilarAction(trade),
              correct: trade.isCorrect,
            }))}
            fingerprint={fingerprint ?? undefined}
            factorValues={factors}
            actionNames={score.actionNames?.length ? score.actionNames : tradingActionNames}
            factorNames={tradingFactorNames}
            actionLabels={tradingActionLabels}
            factorLabels={tradingFactorLabels}
          />
        </>
      ) : null}
    </div>
  );
}

function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="text-sm">
      <span className="mb-1 block trading-muted">{label}</span>
      <select
        className="w-full rounded-md border px-3 py-2"
        style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)" }}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option.replace(/_/g, " ")}
          </option>
        ))}
      </select>
    </label>
  );
}
