import { useEffect, useMemo, useState } from "react";
import { fetchPromotion } from "../api";
import type { PromotionEvent, PromotionResponse, PromotionStrategy } from "../types";

const thresholds: Record<string, { verified: number; winRate: number }> = {
  paper: { verified: 50, winRate: 0.55 },
  small_live: { verified: 100, winRate: 0.58 },
  full_live: { verified: 100, winRate: 0.58 },
};

function pct(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "-";
}

function label(value: string | null | undefined): string {
  return value ? value.replace(/_/g, " ") : "-";
}

function strategyKey(strategy: PromotionStrategy): string {
  return strategy.strategyKey || strategy.key || `${strategy.category || "strategy"}:${strategy.strategyTag || "default"}`;
}

function tierClass(tier: string): string {
  if (tier === "full_live") return "border-emerald-400/40 bg-emerald-400/10 text-emerald-100";
  if (tier === "small_live") return "border-amber-400/40 bg-amber-400/10 text-amber-100";
  return "border-sky-400/40 bg-sky-400/10 text-sky-100";
}

function readiness(strategy: PromotionStrategy): string {
  const tier = String(strategy.tier || "paper");
  if (tier === "full_live") return "Full evidence threshold met.";
  const target = thresholds[tier] || thresholds.paper;
  const verified = Number(strategy.verified || 0);
  const winRate = typeof strategy.winRate === "number" ? strategy.winRate : 0;
  return `${verified}/${target.verified} verified, ${pct(winRate)} win rate.`;
}

function EventRow({ event }: { event: PromotionEvent }) {
  return (
    <li className="rounded-md border p-3 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-semibold">{label(event.strategyKey)}</span>
        <span className="rounded-md border px-2 py-1 text-xs trading-muted" style={{ borderColor: "var(--copilot-border)" }}>
          {label(event.action)}
        </span>
      </div>
      <div className="mt-2 trading-muted">
        {label(event.fromTier)} to {label(event.toTier)} · {event.verifiedCount ?? 0} verified · {pct(event.winRate)}
      </div>
      {event.reason ? <div className="mt-1 trading-muted">{event.reason}</div> : null}
    </li>
  );
}

export default function PromotionPanel() {
  const [payload, setPayload] = useState<PromotionResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      const response = await fetchPromotion();
      if (!cancelled) {
        setPayload(response);
        setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const strategies = useMemo(() => payload?.strategies || [], [payload]);
  const history = useMemo(() => (payload?.history || []).slice(-3).reverse(), [payload]);

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-wide trading-muted">Tier readiness</p>
          <h2 className="mt-1 text-xl font-semibold">Strategy Promotion</h2>
          <p className="mt-2 text-sm trading-muted">Promotion tiers use verified outcomes and conservation-safe evidence thresholds.</p>
        </div>
      </div>

      {loading ? <div className="mt-4 text-sm trading-muted">Loading promotion tiers...</div> : null}

      {!loading && !payload ? (
        <div className="mt-4 rounded-md border border-dashed border-white/15 p-4 text-sm trading-muted">
          Promotion data is unavailable.
        </div>
      ) : null}

      {!loading && payload && strategies.length === 0 ? (
        <div className="mt-4 rounded-md border border-dashed border-white/15 p-4 text-sm trading-muted">
          Score trades to begin tier tracking.
        </div>
      ) : null}

      {!loading && strategies.length ? (
        <div className="mt-4 grid gap-3 lg:grid-cols-2">
          {strategies.map((strategy) => {
            const tier = String(strategy.tier || "paper");
            return (
              <article key={strategyKey(strategy)} className="rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h3 className="text-base font-semibold">{label(strategyKey(strategy))}</h3>
                    <p className="mt-1 text-sm trading-muted">
                      {label(strategy.category)} · {label(strategy.strategyTag || "default")}
                    </p>
                  </div>
                  <span className={`rounded-md border px-2 py-1 text-xs font-semibold ${tierClass(tier)}`}>{label(tier)}</span>
                </div>
                <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
                  <div>
                    <p className="text-xs uppercase tracking-wide trading-muted">Verified</p>
                    <p className="font-semibold">{strategy.verified ?? 0}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide trading-muted">Win rate</p>
                    <p className="font-semibold">{pct(strategy.winRate)}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide trading-muted">Tier</p>
                    <p className="font-semibold">{label(tier)}</p>
                  </div>
                </div>
                <p className="mt-3 text-sm trading-muted">{readiness(strategy)}</p>
              </article>
            );
          })}
        </div>
      ) : null}

      <div className="mt-4 rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
        <h3 className="text-base font-semibold">Promotion History</h3>
        {history.length ? (
          <ul className="mt-3 grid gap-2">
            {history.map((event, index) => <EventRow key={`${event.strategyKey || "event"}-${event.timestamp || index}`} event={event} />)}
          </ul>
        ) : (
          <p className="mt-2 text-sm trading-muted">No promotion events yet.</p>
        )}
      </div>
    </section>
  );
}
