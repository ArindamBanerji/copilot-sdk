import { useEffect, useState } from "react";
import { fetchPredictiveParWeek, type PredictiveParWeekResponse } from "../api";
import ProvenanceBadge from "./ProvenanceBadge";

function lbs(value?: number) {
  return Number.isFinite(value) ? `${Math.round(Number(value))} lbs` : "n/a";
}

function money(value?: number) {
  return Number.isFinite(value) ? `$${Math.round(Number(value)).toLocaleString()}` : "$0";
}

export default function PredictiveParCard() {
  const [data, setData] = useState<PredictiveParWeekResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchPredictiveParWeek();
        if (mounted) setData(result);
      } catch (caught) {
        if (mounted) setError(caught instanceof Error ? caught.message : "Connect POS to see par recommendations");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void load();
    return () => {
      mounted = false;
    };
  }, []);

  const items = data?.items ?? [];
  const tuesday = items.find((item) => item.day === "Tuesday" && item.category === "protein");
  const friday = items.find((item) => item.day === "Friday" && item.category === "protein");

  return (
    <section className="purchase-card">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Smart Par Levels</p>
          <h2 className="purchase-title">Stop ordering Tuesday like Friday</h2>
        </div>
        <ProvenanceBadge source={data?.provenance === "demo" ? "sample" : data?.provenance} />
      </div>
      {loading ? <p className="purchase-muted">Checking the week ahead...</p> : null}
      {error ? <p className="purchase-muted">{error}</p> : null}
      {!loading && !error && items.length === 0 ? <p className="purchase-muted">Connect POS to see par recommendations</p> : null}
      {items.length > 0 ? (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <div className="rounded-md border p-3" style={{ borderColor: "var(--purchase-border)" }}>
              <div className="purchase-muted text-sm">Tue-Thu par</div>
              <strong>{lbs(tuesday?.adjustedPar)}</strong>
              <p className="purchase-muted text-sm">Slow days stay lean.</p>
            </div>
            <div className="rounded-md border p-3" style={{ borderColor: "var(--purchase-border)" }}>
              <div className="purchase-muted text-sm">Fri-Sat par</div>
              <strong>{lbs(friday?.adjustedPar)}</strong>
              <p className="purchase-muted text-sm">Friday needs 40% more.</p>
            </div>
          </div>
          <p className="mt-3 text-sm font-semibold">{data?.summary ?? "Two-tier par saves about $180/week in protein waste."}</p>
          <p className="purchase-muted mt-1">Weekly waste reduction: {money(data?.dollarImpact)}</p>
          <div className="mt-4 space-y-2">
            {items.slice(0, 4).map((item) => (
              <div key={`${item.item}-${item.day}`} className="rounded-md border p-3 text-sm" style={{ borderColor: "var(--purchase-border)" }}>
                <strong>{item.day}: {item.item}</strong>
                <p className="purchase-muted">{item.explanation}</p>
              </div>
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}
