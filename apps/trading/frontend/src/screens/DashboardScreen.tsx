import { useCallback, useEffect, useMemo, useState } from "react";
import { DecisionHistory, TransferBadge } from "../../../../../copilot_sdk/frontend";
import DayZeroCard from "../../../../../copilot_sdk/frontend/components/DayZeroCard";
import {
  API_BASE,
  getAnalytics,
  getHistory,
  getMarketSnapshot,
  getTradeMetadata,
  getTicker,
} from "../api";
import AccuracyByCategory from "../components/AccuracyByCategory";
import ArchetypeSelector from "../components/ArchetypeSelector";
import CalendarHeatmap from "../components/CalendarHeatmap";
import MarketContext from "../components/MarketContext";
import PatternBadge from "../components/PatternBadge";
import PortfolioConcentration from "../components/PortfolioConcentration";
import PortfolioSummary from "../components/PortfolioSummary";
import ProvenanceBadge from "../components/ProvenanceBadge";
import RegimePanel from "../components/RegimePanel";
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
  tickers: Record<string, TickerData>;
}

interface TickerPanelProps {
  metadata: Record<string, TradeMetadata>;
  disabled: boolean;
  onTickers: (tickers: Record<string, TickerData>) => void;
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

function scrollToArchetypes() {
  document.getElementById("archetype-select")?.scrollIntoView({ behavior: "smooth", block: "center" });
}

function TickerPanel({ metadata, disabled, onTickers }: TickerPanelProps) {
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setError(null);
      try {
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
          onTickers(Object.fromEntries(tickerPairs));
        }
      } catch (loadError) {
        console.debug("dashboard ticker context unavailable", loadError);
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Ticker context unavailable");
          onTickers({});
        }
      }
    }

    if (!disabled) {
      void load();
    }
    return () => {
      cancelled = true;
    };
  }, [metadata, disabled, onTickers]);

  if (!error) {
    return null;
  }

  return (
    <div className="rounded-md border px-3 py-2 text-sm trading-muted" style={{ borderColor: "var(--copilot-border)" }}>
      Ticker context unavailable: {error}
    </div>
  );
}

export default function DashboardScreen({
  onSelectTrade,
  onLogTrade,
}: {
  onSelectTrade: (tradeId: string) => void;
  onLogTrade: () => void;
}) {
  const [analytics, setAnalytics] = useState<Analytics | undefined>();
  const [history, setHistory] = useState<TradeHistoryDecision[]>([]);
  const [metadata, setMetadata] = useState<Record<string, TradeMetadata>>({});
  const [market, setMarket] = useState<MarketSnapshot | undefined>();
  const [state, setState] = useState<DashboardState>({
    tickers: {},
  });
  const [loading, setLoading] = useState(true);
  const [tabError, setTabError] = useState<string | null>(null);
  const updateTickers = useCallback((tickers: Record<string, TickerData>) => {
    setState({ tickers });
  }, []);

  const joinedTrades = useMemo(
    () => joinTrades(history, metadata, state.tickers),
    [history, metadata, state.tickers],
  );

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([getAnalytics(), getHistory(), getTradeMetadata(), getMarketSnapshot()])
      .then(([nextAnalytics, nextHistory, nextMetadata, nextMarket]) => {
        if (cancelled) return;
        setAnalytics(nextAnalytics);
        setHistory(nextHistory);
        setMetadata(nextMetadata);
        setMarket(nextMarket);
        setTabError(null);
      })
      .catch((loadError) => {
        console.debug("dashboard data unavailable", loadError);
        if (!cancelled) {
          setTabError(loadError instanceof Error ? loadError.message : "Dashboard unavailable");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return <div data-screen-ready="false" className="copilot-card p-8 text-sm trading-muted">Loading trading dashboard...</div>;
  }

  if (tabError) {
    return (
      <div data-screen-ready="true" className="copilot-card p-8">
        <h2 className="text-base font-semibold">Dashboard unavailable</h2>
        <p className="mt-2 text-sm trading-muted">{tabError}</p>
      </div>
    );
  }

  return (
    <div data-screen-ready="true" className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold">Dashboard</h2>
          <p className="text-sm trading-muted">Trading Backend v2 context, analytics, and decision history.</p>
          <div className="mt-3">
            <TransferBadge apiBase={API_BASE} />
          </div>
        </div>
        <button type="button" className="copilot-button px-4 py-2 text-sm" onClick={onLogTrade}>
          Log New Trade
        </button>
      </div>

      {joinedTrades.length === 0 ? (
        <div className="copilot-card p-4">
          <h2 className="text-base font-semibold">Get started faster</h2>
          <p className="mt-2 max-w-2xl text-sm trading-muted">
            No decisions yet. Select an industry template to start with calibrated centroids instead of generic 50% priors.
          </p>
          <button type="button" className="copilot-button mt-4 px-4 py-2 text-sm" onClick={scrollToArchetypes}>
            Browse Industry Templates
          </button>
        </div>
      ) : null}

      <ArchetypeSelector />
      <DayZeroCard
        apiBase={API_BASE}
        copilot="trading"
        renderProvenance={(source) => <ProvenanceBadge source={source} />}
      />
      <MarketContext snapshot={market} />
      <TickerPanel metadata={metadata} disabled={loading} onTickers={updateTickers} />
      <RegimePanel />
      <PortfolioSummary summary={analytics?.portfolioSummary} />
      <PatternBadge />
      <AccuracyByCategory />

      <div className="trading-grid trading-grid-3">
        <PortfolioConcentration
          concentration={analytics?.portfolioConcentration}
          categoryCounts={analytics?.categoryCounts}
        />
        <ThesisBreakdown breakdown={analytics?.thesisBreakdown} />
        <div className="copilot-card p-4">
          <h2 className="text-base font-semibold">Dataset</h2>
          <div className="mt-4 grid gap-3">
            <div>
              <div className="text-xs trading-muted">Total trades</div>
              <div className="trading-stat-value">{analytics?.totalTrades ?? joinedTrades.length}</div>
            </div>
            <div>
              <div className="text-xs trading-muted">Open positions</div>
              <div className="trading-stat-value">{analytics?.openPositions ?? 0}</div>
            </div>
            <div>
              <div className="text-xs trading-muted">Source</div>
              <div className="text-sm font-semibold">{analytics?.source || "backend"}</div>
            </div>
          </div>
        </div>
      </div>

      <CalendarHeatmap trades={joinedTrades} calendar={analytics?.calendarHeatmap} />

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
