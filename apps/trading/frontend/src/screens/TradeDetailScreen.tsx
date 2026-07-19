import { useEffect, useMemo, useState } from "react";
import { getHistory, getTicker, getTradeMetadata } from "../api";
import type { JoinedTrade, TickerData, TradeHistoryDecision, TradeMetadata } from "../types";

const factorOrder = [
  { camelKey: "signal_alignment", snakeKey: "signal_alignment", label: "Conviction" },
  { camelKey: "researchDepth", snakeKey: "market_regime", label: "Research depth" },
  { camelKey: "technicalSignal", snakeKey: "position_sizing", label: "Technical signal" },
  { camelKey: "positionSize", snakeKey: "timing_quality", label: "Position size" },
  { camelKey: "timeHorizon", snakeKey: "risk_reward_actual", label: "Time horizon" },
  { camelKey: "marketRegime", snakeKey: "emotional_indicator", label: "Market regime" },
] as const;

function getDecisionId(decision: TradeHistoryDecision): string | undefined {
  return decision.decisionId || (typeof decision.id === "string" ? decision.id : undefined);
}

function money(value: number | null | undefined): string {
  return typeof value === "number" ? `$${value.toLocaleString()}` : "-";
}

function pct(value: number | null | undefined): string {
  return typeof value === "number" ? `${value > 0 ? "+" : ""}${value.toFixed(2)}%` : "-";
}

function num(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function getFactorValue(
  trade: JoinedTrade,
  camelKey: keyof Pick<
    JoinedTrade,
    "signal_alignment" | "researchDepth" | "technicalSignal" | "positionSize" | "timeHorizon" | "marketRegime"
  >,
  snakeKey: string,
): number | undefined {
  // History/scorer factors use snake_case Trading preset keys; metadata/UI may use camelCase.
  return num(trade.factors?.[snakeKey]) ?? num(trade.factors?.[camelKey]) ?? num(trade[camelKey]);
}

function dots(value: number | null | undefined, count = 5) {
  const filled = Math.round(Math.max(0, Math.min(1, Number(value) || 0)) * count);
  return Array.from({ length: count }, (_, index) => (
    <span
      key={index}
      className="inline-block h-2 w-2 rounded-full"
      style={{ background: index < filled ? "var(--copilot-primary)" : "var(--copilot-surface-muted)" }}
    />
  ));
}

function joinTrade(
  tradeId: string,
  history: TradeHistoryDecision[],
  metadata: Record<string, TradeMetadata>,
  tickerData?: TickerData,
): JoinedTrade | undefined {
  const historyItem = history.find((decision) => getDecisionId(decision) === tradeId);
  const meta = metadata[tradeId];
  if (!historyItem && !meta) {
    return undefined;
  }
  return {
    ...(meta || {}),
    decisionId: tradeId,
    history: historyItem,
    ticker: meta?.ticker || (typeof historyItem?.ticker === "string" ? historyItem.ticker : undefined),
    tickerData,
    confidence: typeof historyItem?.confidence === "number" ? historyItem.confidence : undefined,
    scoreAction: historyItem?.action,
    factors: historyItem?.factors,
    reward: meta?.reward ?? historyItem?.reward,
  };
}

export default function TradeDetailScreen({
  tradeId,
  onBack,
}: {
  tradeId: string | null;
  onBack: () => void;
}) {
  const [history, setHistory] = useState<TradeHistoryDecision[]>([]);
  const [metadata, setMetadata] = useState<Record<string, TradeMetadata>>({});
  const [tickerData, setTickerData] = useState<TickerData | undefined>();
  const [loading, setLoading] = useState(Boolean(tradeId));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (!tradeId) {
        setLoading(false);
        return;
      }
      setLoading(true);
      setError(null);
      setTickerData(undefined);
      try {
        const [historyPayload, metadataPayload] = await Promise.all([getHistory(), getTradeMetadata()]);
        const meta = metadataPayload[tradeId];
        const historyItem = historyPayload.find((decision) => getDecisionId(decision) === tradeId);
        const ticker = meta?.ticker || (typeof historyItem?.ticker === "string" ? historyItem.ticker : undefined);
        const tickerPayload = ticker ? await getTicker(ticker) : undefined;
        if (!cancelled) {
          setHistory(historyPayload);
          setMetadata(metadataPayload);
          setTickerData(tickerPayload);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Trade detail load failed");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [tradeId]);

  const trade = useMemo(
    () => (tradeId ? joinTrade(tradeId, history, metadata, tickerData) : undefined),
    [history, metadata, tickerData, tradeId],
  );

  if (!tradeId) {
    return <EmptyState onBack={onBack} message="Select a trade from the dashboard to inspect it." />;
  }

  if (loading) {
    return <div data-screen-ready="false" className="copilot-card p-8 text-sm trading-muted">Loading trade detail...</div>;
  }

  if (error) {
    return (
      <section data-screen-ready="true" className="copilot-card p-6">
        <button type="button" className="copilot-button-secondary px-3 py-2 text-sm" onClick={onBack}>
          Back to Dashboard
        </button>
        <h2 className="mt-4 text-xl font-semibold">Trade detail unavailable</h2>
        <p className="mt-2 text-sm trading-muted">{error}</p>
      </section>
    );
  }

  if (!trade) {
    return <EmptyState onBack={onBack} message={`No trade data found for ${tradeId}.`} />;
  }

  const exposureDollars = typeof trade.shares === "number" && typeof trade.entryPrice === "number"
    ? trade.shares * trade.entryPrice
    : undefined;

  return (
    <div data-screen-ready="true" className="flex flex-col gap-4">
      <section className="copilot-card p-5">
        <button type="button" className="copilot-button-secondary px-3 py-2 text-sm" onClick={onBack}>
          Back to Dashboard
        </button>
        <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold">{trade.ticker || "Unknown"} Trade</h2>
            <p className="mt-1 text-sm trading-muted">
              {trade.direction || trade.scoreAction || trade.actionTaken || "trade"} · {trade.thesisType || trade.category || "unclassified"} · {trade.timeframe || "timeframe n/a"}
            </p>
          </div>
          <div className="text-right">
            <div className={typeof trade.pnlPct === "number" && trade.pnlPct < 0 ? "text-2xl font-semibold trading-negative" : "text-2xl font-semibold trading-positive"}>
              {pct(trade.pnlPct)}
            </div>
            <div className="text-sm trading-muted">{money(trade.pnlDollars)}</div>
          </div>
        </div>
      </section>

      <section className="copilot-card p-4">
        <h2 className="text-base font-semibold">Trade Economics</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          <Stat label="Entry" value={money(trade.entryPrice)} />
          <Stat label="Exit" value={money(trade.exitPrice)} />
          <Stat label="Shares" value={typeof trade.shares === "number" ? trade.shares.toLocaleString() : "-"} />
          <Stat label="Exposure" value={money(exposureDollars)} />
          <Stat label="Stop" value={money(trade.stopLoss)} />
          <Stat label="Target" value={money(trade.target)} />
          <Stat label="R:R" value={typeof trade.rrRatio === "number" ? trade.rrRatio.toFixed(2) : "-"} />
          <Stat label="Reward" value={typeof trade.reward === "number" ? trade.reward.toFixed(3) : "-"} />
        </div>
      </section>

      <section className="copilot-card p-4">
        <h2 className="text-base font-semibold">Research Checklist</h2>
        {trade.researchChecklist?.length ? (
          <div className="mt-4 grid gap-2 md:grid-cols-5">
            {trade.researchChecklist.map((checked, index) => (
              <div key={index} className="rounded-md border px-3 py-2 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
                <span className={checked ? "trading-positive" : "trading-muted"}>{checked ? "Complete" : "Missing"}</span>
                <div className="text-xs trading-muted">Item {index + 1}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-4 rounded-md p-4 text-sm trading-muted" style={{ background: "var(--copilot-surface-muted)" }}>
            No checklist data saved for this trade.
          </div>
        )}
        <div className="mt-4">
          <div className="text-xs trading-muted">Conviction</div>
          <div className="mt-1 flex gap-1">{dots(trade.signal_alignment)}</div>
        </div>
      </section>

      <section className="copilot-card p-4">
        <h2 className="text-base font-semibold">Factor Bars</h2>
        <div className="mt-4 grid gap-3">
          {factorOrder.map(({ camelKey, snakeKey, label }) => (
            <FactorBar key={snakeKey} label={label} value={getFactorValue(trade, camelKey, snakeKey)} />
          ))}
        </div>
      </section>
    </div>
  );
}

function EmptyState({ onBack, message }: { onBack: () => void; message: string }) {
  return (
    <section data-screen-ready="true" className="copilot-card p-6">
      <button type="button" className="copilot-button-secondary px-3 py-2 text-sm" onClick={onBack}>
        Back to Dashboard
      </button>
      <h2 className="mt-4 text-xl font-semibold">Trade Detail</h2>
      <p className="mt-2 text-sm trading-muted">{message}</p>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border px-3 py-2" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs trading-muted">{label}</div>
      <div className="text-sm font-semibold">{value}</div>
    </div>
  );
}

function FactorBar({ label, value }: { label: string; value?: number }) {
  const width = Math.max(0, Math.min(100, (value ?? 0) * 100));
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm">
        <span>{label}</span>
        <span className="font-semibold">{typeof value === "number" ? value.toFixed(2) : "-"}</span>
      </div>
      <div className="trading-bar-track">
        <div className="trading-bar-fill" style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}
