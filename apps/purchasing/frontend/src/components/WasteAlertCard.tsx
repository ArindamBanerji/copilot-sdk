import { useEffect, useState } from "react";
import { getWasteAnalysis, getWasteSummary, type WasteItemProfile, type WasteSummaryResponse } from "../api";

function money(value?: number) {
  return Number.isFinite(value) ? `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : "$0";
}

function pct(value?: number) {
  return Number.isFinite(value) ? `${(Number(value) * 100).toFixed(1)}%` : "-";
}

export default function WasteAlertCard() {
  const [items, setItems] = useState<WasteItemProfile[]>([]);
  const [summary, setSummary] = useState<WasteSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [profiles, totals] = await Promise.all([getWasteAnalysis(), getWasteSummary()]);
        if (mounted) {
          setItems(profiles);
          setSummary(totals);
        }
      } catch (caught) {
        if (mounted) setError(caught instanceof Error ? caught.message : "No waste data recorded yet");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void load();
    return () => {
      mounted = false;
    };
  }, []);

  const top = items.slice(0, 5);

  return (
    <section className="purchase-card">
      <p className="purchase-kicker">Waste Intelligence</p>
      <h2 className="purchase-title">Prep waste has a dollar target</h2>
      {loading ? <p className="purchase-muted">Loading waste cost...</p> : null}
      {error ? <p className="purchase-muted">{error}</p> : null}
      {!loading && !error && top.length === 0 ? <p className="purchase-muted">No waste data recorded yet</p> : null}
      {top.length > 0 ? (
        <>
          <p className="mt-3 text-sm font-semibold">
            Weekly waste cost: {money(summary?.weeklyWasteCost)}. Top 3 = {money(summary?.topThreeAddressable)} addressable.
          </p>
          <p className="purchase-muted mt-1">We prevented {money(summary?.preventedThisWeek)} in waste this week.</p>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="purchase-muted">
                <tr>
                  <th className="py-2 pr-3">Item</th>
                  <th className="py-2 pr-3">Waste</th>
                  <th className="py-2 pr-3">Kitchen benchmark</th>
                  <th className="py-2 pr-3">Trend</th>
                  <th className="py-2 pr-3">Cost</th>
                  <th className="py-2 pr-3">Recommendation</th>
                </tr>
              </thead>
              <tbody>
                {top.map((item) => (
                  <tr key={item.item} className="border-t" style={{ borderColor: "var(--purchase-border)" }}>
                    <td className="py-2 pr-3 font-semibold">{item.item}</td>
                    <td className="py-2 pr-3">{pct(item.averageWastePct)}</td>
                    <td className="py-2 pr-3">{pct(item.benchmarkPct)}</td>
                    <td className="py-2 pr-3">{item.trend}</td>
                    <td className="py-2 pr-3">{money(item.weeklyWasteCost)}</td>
                    <td className="py-2 pr-3">{item.recommendation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : null}
    </section>
  );
}
