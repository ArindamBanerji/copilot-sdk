import { useEffect, useMemo, useState } from "react";
import { fetchAnalytics, fetchSubcategoryAnalytics, fetchTradeDetail, fetchTrades, type TradeJournalFilters } from "../api";
import EarningsInsightCard from "../components/EarningsInsightCard";
import EvidencePanel from "../components/EvidencePanel";
import JournalQueryBar from "../components/JournalQueryBar";
import OptionsFactorPanel from "../components/OptionsFactorPanel";
import type { AnalyticsResponse, JournalAggregate, TradeJournalEntry, TradesResponse } from "../types";

const categories = [
  { value: "", label: "All categories" },
  { value: "trend_following", label: "Trend following" },
  { value: "mean_reversion", label: "Mean reversion" },
  { value: "event_driven", label: "Event driven" },
  { value: "income_strategy", label: "Income strategy" },
  { value: "scalp_intraday", label: "Scalp intraday" },
];

function money(value: number | null | undefined): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "-";
  return `${value < 0 ? "-" : ""}$${Math.abs(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function pct(value: number | null | undefined): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "-";
  return `${(value * 100).toFixed(1)}%`;
}

function dateLabel(value: string | null | undefined): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function label(value: unknown): string {
  return typeof value === "string" && value ? value.replace(/_/g, " ") : "-";
}

function categoryLabel(value: unknown): string {
  if (value === "event_driven") return "Event Driven";
  return label(value);
}

function factorEntries(trade?: TradeJournalEntry | null) {
  return Object.entries(trade?.factors || {}).filter(([, value]) => typeof value === "number");
}

export default function JournalScreen() {
  const [filters, setFilters] = useState<TradeJournalFilters>({ limit: 50 });
  const [tradesPayload, setTradesPayload] = useState<TradesResponse | null>(null);
  const [analyticsPayload, setAnalyticsPayload] = useState<AnalyticsResponse | null>(null);
  const [subcategoryAnalyticsPayload, setSubcategoryAnalyticsPayload] = useState<AnalyticsResponse | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedTrade, setSelectedTrade] = useState<TradeJournalEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [trades, analytics, subcategoryAnalytics] = await Promise.all([
          fetchTrades(filters),
          fetchAnalytics("category", filters),
          fetchSubcategoryAnalytics(filters),
        ]);
        if (cancelled) return;
        setTradesPayload(trades);
        setAnalyticsPayload(analytics);
        setSubcategoryAnalyticsPayload(subcategoryAnalytics);
        if (!trades || !analytics) {
          setError("Trade journal is unavailable.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [filters]);

  useEffect(() => {
    let cancelled = false;
    async function loadDetail() {
      if (!selectedId) {
        setSelectedTrade(null);
        return;
      }
      const detail = await fetchTradeDetail(selectedId);
      if (!cancelled) {
        setSelectedTrade(detail);
      }
    }
    void loadDetail();
    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  const trades = tradesPayload?.trades || [];
  const aggregate = tradesPayload?.aggregate;
  const selected = selectedTrade || trades.find((trade) => trade.tradeId === selectedId);
  const categoryGroups = useMemo(() => analyticsPayload?.groups || [], [analyticsPayload]);
  const subcategoryGroups = useMemo(() => subcategoryAnalyticsPayload?.groups || [], [subcategoryAnalyticsPayload]);

  function updateFilter<K extends keyof TradeJournalFilters>(key: K, value: TradeJournalFilters[K]) {
    setSelectedId(null);
    setFilters((current) => ({ ...current, offset: 0, [key]: value }));
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold">Trade Journal</h2>
          <p className="text-sm trading-muted">Review imported and persisted trades with journal filters and outcome analytics.</p>
        </div>
      </div>

      <section className="copilot-card p-4">
        <h3 className="text-base font-semibold">Journal Filters</h3>
        <div className="mt-4 grid gap-3 md:grid-cols-5">
          <label className="text-sm">
            <span className="trading-muted">Ticker</span>
            <input
              className="mt-1 w-full rounded-md border bg-transparent px-3 py-2"
              style={{ borderColor: "var(--copilot-border)" }}
              value={filters.ticker || ""}
              onChange={(event) => updateFilter("ticker", event.target.value || undefined)}
              placeholder="MSFT"
            />
          </label>
          <label className="text-sm">
            <span className="trading-muted">Category</span>
            <select
              className="mt-1 w-full rounded-md border bg-transparent px-3 py-2"
              style={{ borderColor: "var(--copilot-border)" }}
              value={filters.category || ""}
              onChange={(event) => updateFilter("category", event.target.value || undefined)}
            >
              {categories.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="trading-muted">Strategy</span>
            <input
              className="mt-1 w-full rounded-md border bg-transparent px-3 py-2"
              style={{ borderColor: "var(--copilot-border)" }}
              value={filters.strategyTag || ""}
              onChange={(event) => updateFilter("strategyTag", event.target.value || undefined)}
              placeholder="momentum"
            />
          </label>
          <label className="text-sm">
            <span className="trading-muted">Outcome</span>
            <select
              className="mt-1 w-full rounded-md border bg-transparent px-3 py-2"
              style={{ borderColor: "var(--copilot-border)" }}
              value={filters.outcome || ""}
              onChange={(event) => updateFilter("outcome", event.target.value as TradeJournalFilters["outcome"])}
            >
              <option value="">All</option>
              <option value="win">Win</option>
              <option value="loss">Loss</option>
            </select>
          </label>
          <label className="text-sm">
            <span className="trading-muted">Limit</span>
            <input
              className="mt-1 w-full rounded-md border bg-transparent px-3 py-2"
              style={{ borderColor: "var(--copilot-border)" }}
              type="number"
              min={1}
              max={200}
              value={filters.limit || 50}
              onChange={(event) => updateFilter("limit", Number(event.target.value) || 50)}
            />
          </label>
        </div>
      </section>

      <JournalQueryBar />

      {loading ? <section className="copilot-card p-6 text-sm trading-muted">Loading trade journal...</section> : null}
      {!loading && error ? (
        <section className="copilot-card p-6">
          <h3 className="text-base font-semibold">Journal unavailable</h3>
          <p className="mt-2 text-sm trading-muted">{error}</p>
        </section>
      ) : null}

      {!loading && !error ? (
        <>
          <AggregateCards aggregate={aggregate} total={tradesPayload?.total ?? trades.length} />
          <EarningsInsightCard groups={subcategoryGroups} />
          <section className="copilot-card p-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-base font-semibold">Trades</h3>
              <span className="text-sm trading-muted">{tradesPayload?.total ?? 0} matching trades</span>
            </div>
            {trades.length ? (
              <div className="mt-4 overflow-x-auto">
                <table className="w-full min-w-[780px] text-left text-sm">
                  <thead className="trading-muted">
                    <tr>
                      <th className="py-2 pr-3 font-medium">Date</th>
                      <th className="py-2 pr-3 font-medium">Ticker</th>
                      <th className="py-2 pr-3 font-medium">Direction</th>
                      <th className="py-2 pr-3 font-medium">P&L</th>
                      <th className="py-2 pr-3 font-medium">Category</th>
                      <th className="py-2 pr-3 font-medium">Strategy</th>
                      <th className="py-2 pr-3 font-medium">Confidence</th>
                      <th className="py-2 pr-3 font-medium">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trades.map((trade) => (
                      <tr
                        key={trade.tradeId || `${trade.ticker}-${trade.entryTime}`}
                        className="cursor-pointer border-t"
                        style={{ borderColor: "var(--copilot-border)" }}
                        onClick={() => setSelectedId(trade.tradeId || null)}
                      >
                        <td className="py-3 pr-3">{dateLabel(trade.entryTime)}</td>
                        <td className="py-3 pr-3 font-semibold">{trade.ticker || "-"}</td>
                        <td className="py-3 pr-3 capitalize">{label(trade.direction)}</td>
                        <td className={typeof trade.pnl === "number" && trade.pnl < 0 ? "py-3 pr-3 trading-negative" : "py-3 pr-3 trading-positive"}>{money(trade.pnl)}</td>
                        <td className="py-3 pr-3 capitalize">{label(trade.category)}</td>
                        <td className="py-3 pr-3 capitalize">{label(trade.strategyTag)}</td>
                        <td className="py-3 pr-3">{pct(trade.confidence)}</td>
                        <td className="py-3 pr-3 capitalize">{label(trade.action)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="mt-4 rounded-md p-6 text-sm trading-muted" style={{ background: "var(--copilot-surface-muted)" }}>
                No trades match these journal filters. Import trades or clear filters to populate the journal.
              </div>
            )}
          </section>

          <section className="copilot-card p-4">
            <h3 className="text-base font-semibold">Category Analytics</h3>
            {categoryGroups.length ? (
              <div className="mt-4 grid gap-3 md:grid-cols-3">
                {categoryGroups.map((group) => (
                  <div key={group.key} className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
                    <div className="text-sm font-semibold capitalize">{categoryLabel(group.key)}</div>
                    <div className="mt-2 text-xs trading-muted">{group.count ?? group.totalTrades ?? 0} trades</div>
                    <div className="mt-2 text-sm">Win rate <span className="font-semibold">{pct(group.winRate)}</span></div>
                    <div className="text-sm">Total P&L <span className="font-semibold">{money(group.totalPnl)}</span></div>
                    {group.key === "event_driven" ? <EventDrivenSubcategorySplit groups={subcategoryGroups} /> : null}
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-4 text-sm trading-muted">No category analytics available for the current filters.</p>
            )}
          </section>

          {selected ? <TradeDetailPanel trade={selected} /> : null}
          {selected?.tradeId ? <EvidencePanel tradeId={selected.tradeId} /> : null}
        </>
      ) : null}
    </div>
  );
}

function EventDrivenSubcategorySplit({ groups }: { groups: AnalyticsResponse["groups"] }) {
  if (!groups?.length) {
    return (
      <p className="mt-3 border-t pt-3 text-xs trading-muted" style={{ borderColor: "var(--copilot-border)" }}>
        No event-driven subcategory split yet.
      </p>
    );
  }
  const byKey = new Map(groups.map((group) => [group.key, group]));
  const rows = [
    { key: "directional", label: "Directional" },
    { key: "volatility", label: "Volatility" },
  ];
  return (
    <div className="mt-3 border-t pt-3" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs font-semibold uppercase trading-muted">Event Driven Split</div>
      <div className="mt-2 grid gap-2">
        {rows.map((row) => {
          const group = byKey.get(row.key);
          return (
            <div key={row.key} className="flex items-center justify-between gap-3 rounded-md px-2 py-1 text-xs" style={{ background: "var(--copilot-surface-muted)" }}>
              <span className="font-medium">{row.label}</span>
              <span className="trading-muted">
                {group?.count ?? group?.totalTrades ?? 0} trades, {pct(group?.winRate)} win rate
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function AggregateCards({ aggregate, total }: { aggregate?: JournalAggregate; total: number }) {
  return (
    <section className="trading-grid trading-grid-4">
      <Stat label="Total trades" value={String(aggregate?.totalTrades ?? total)} />
      <Stat label="Win rate" value={pct(aggregate?.winRate)} />
      <Stat label="Avg P&L" value={money(aggregate?.avgPnl)} />
      <Stat label="Total P&L" value={money(aggregate?.totalPnl)} />
    </section>
  );
}

function Stat({ label: statLabel, value }: { label: string; value: string }) {
  return (
    <div className="copilot-card p-4">
      <div className="text-xs trading-muted">{statLabel}</div>
      <div className="trading-stat-value">{value}</div>
    </div>
  );
}

function TradeDetailPanel({ trade }: { trade: TradeJournalEntry }) {
  const factors = factorEntries(trade);
  return (
    <section className="copilot-card p-4">
      <h3 className="text-base font-semibold">Trade Detail</h3>
      <p className="mt-1 text-sm trading-muted">
        {trade.ticker || "Unknown"} · {label(trade.category)} · {label(trade.strategyTag)}
      </p>
      <div className="mt-4 grid gap-3 md:grid-cols-4">
        <Stat label="Entry" value={money(trade.entryPrice)} />
        <Stat label="Exit" value={money(trade.exitPrice)} />
        <Stat label="Size" value={typeof trade.size === "number" ? trade.size.toLocaleString() : "-"} />
        <Stat label="Confidence" value={pct(trade.confidence)} />
      </div>
      <div className="mt-4">
        <h4 className="text-sm font-semibold">Factor Breakdown</h4>
        {factors.length ? (
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {factors.map(([name, value]) => (
              <div key={name} className="flex justify-between rounded-md border px-3 py-2 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
                <span className="capitalize">{label(name)}</span>
                <span className="font-semibold">{Number(value).toFixed(2)}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-2 text-sm trading-muted">No factor details available for this trade.</p>
        )}
      </div>
      {trade.optionsFactors ? (
        <div className="mt-4">
          <OptionsFactorPanel optionsFactors={trade.optionsFactors} analyticsOnly={trade.optionsAnalyticsOnly !== false} />
        </div>
      ) : null}
      <div className="mt-4">
        <h4 className="text-sm font-semibold">Metadata</h4>
        <pre className="mt-2 max-h-48 overflow-auto rounded-md p-3 text-xs" style={{ background: "var(--copilot-surface-muted)" }}>
          {JSON.stringify(trade.metadata || {}, null, 2)}
        </pre>
      </div>
    </section>
  );
}
