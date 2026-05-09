import { useEffect, useMemo, useState } from "react";
import { DecisionHistory } from "../../../../../copilot_sdk/frontend";
import {
  getAnalytics,
  getHistory,
  getMarketSnapshot,
  getTicker,
  getTradeMetadata,
} from "../api";
import CalendarHeatmap from "../components/CalendarHeatmap";
import MarketContext from "../components/MarketContext";
import PortfolioConcentration from "../components/PortfolioConcentration";
import PortfolioSummary from "../components/PortfolioSummary";
import ThesisBreakdown from "../components/ThesisBreakdown";
import TradeCard from "../components/TradeCard";
import type {
  Analytics,
  JoinedTrade,
  MarketSnapshot,
  TickerData,
  TradeHistoryDecision,
  TradeMetadata,
} from "../types";

interface DashboardState {
  analytics?: Analytics;
  history: TradeHistoryDecision[];
  metadata: Record<string, TradeMetadata>;
  market?: MarketSnapshot;
  tickers: Record<string, TickerData>;
}

function getDecisionId(decision: TradeHistoryDecision): string | undefined {
  return decision.decisionId || (typeof decision.id === "string" ? decision.id : undefined);
}

function isOpenTrade(trade: TradeMetadata): boolean {
  return trade.exitPrice === null || trade.outcome === null || trade.holdDays === null;
}

function joinTrades(
  history: TradeHistoryDecision[],
  metadata: Record<string, TradeMetadata>,
  tickers: Record<string, TickerData>,
): JoinedTrade[] {
  const ids = new Set<string>();
  history.forEach((decision) => {
    const id = getDecisionId(decision);
    if (id) {
      ids.add(id);
    }
  });
  Object.keys(metadata).forEach((id) => ids.add(id));

  return Array.from(ids).map((id) => {
    const historyItem = history.find((decision) => getDecisionId(decision) === id);
    const meta = metadata[id] || {};
    const ticker = meta.ticker || (typeof historyItem?.ticker === "string" ? historyItem.ticker : undefined);
    return {
      ...meta,
      decisionId: id,
      history: historyItem,
      ticker,
      tickerData: ticker ? tickers[ticker.toUpperCase()] : undefined,
      confidence: typeof historyItem?.confidence === "number" ? historyItem.confidence : undefined,
      scoreAction: historyItem?.action,
      factors: historyItem?.factors,
    };
  });
}

export default function DashboardScreen({
  onSelectTrade,
  onLogTrade,
}: {
  onSelectTrade: (tradeId: string) => void;
  onLogTrade: () => void;
}) {
  const [state, setState] = useState<DashboardState>({
    history: [],
    metadata: {},
    tickers: {},
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [analytics, history, metadata, market] = await Promise.all([
          getAnalytics(),
          getHistory(),
          getTradeMetadata(),
          getMarketSnapshot(),
        ]);

        const openTickers = Array.from(
          new Set(
            Object.values(metadata)
              .filter(isOpenTrade)
              .map((trade) => trade.ticker?.toUpperCase())
              .filter((ticker): ticker is string => Boolean(ticker)),
          ),
        );
        const tickerPairs = await Promise.all(
          openTickers.map(async (ticker) => [ticker, await getTicker(ticker)] as const),
        );
        if (!cancelled) {
          setState({
            analytics,
            history,
            metadata,
            market,
            tickers: Object.fromEntries(tickerPairs),
          });
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Dashboard load failed");
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
  }, []);

  const joinedTrades = useMemo(
    () => joinTrades(state.history, state.metadata, state.tickers),
    [state.history, state.metadata, state.tickers],
  );

  if (loading) {
    return <div className="copilot-card p-8 text-sm trading-muted">Loading trading dashboard...</div>;
  }

  if (error) {
    return (
      <div className="copilot-card p-8">
        <h2 className="text-base font-semibold">Dashboard unavailable</h2>
        <p className="mt-2 text-sm trading-muted">{error}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold">Dashboard</h2>
          <p className="text-sm trading-muted">Trading Backend v2 context, analytics, and decision history.</p>
        </div>
        <button type="button" className="copilot-button px-4 py-2 text-sm" onClick={onLogTrade}>
          Log New Trade
        </button>
      </div>

      <MarketContext snapshot={state.market} />
      <PortfolioSummary summary={state.analytics?.portfolioSummary} />

      <div className="trading-grid trading-grid-3">
        <PortfolioConcentration
          concentration={state.analytics?.portfolioConcentration}
          categoryCounts={state.analytics?.categoryCounts}
        />
        <ThesisBreakdown breakdown={state.analytics?.thesisBreakdown} />
        <div className="copilot-card p-4">
          <h2 className="text-base font-semibold">Dataset</h2>
          <div className="mt-4 grid gap-3">
            <div>
              <div className="text-xs trading-muted">Total trades</div>
              <div className="trading-stat-value">{state.analytics?.totalTrades ?? joinedTrades.length}</div>
            </div>
            <div>
              <div className="text-xs trading-muted">Open positions</div>
              <div className="trading-stat-value">{state.analytics?.openPositions ?? 0}</div>
            </div>
            <div>
              <div className="text-xs trading-muted">Source</div>
              <div className="text-sm font-semibold">{state.analytics?.source || "backend"}</div>
            </div>
          </div>
        </div>
      </div>

      <CalendarHeatmap trades={joinedTrades} calendar={state.analytics?.calendarHeatmap} />

      <DecisionHistory
        title="Decision History"
        emptyMessage="No trading decisions yet."
        decisions={joinedTrades}
        maxVisible={20}
        renderCard={(trade) => (
          <TradeCard
            trade={trade}
            onClick={() => onSelectTrade(trade.decisionId)}
          />
        )}
      />
    </div>
  );
}
