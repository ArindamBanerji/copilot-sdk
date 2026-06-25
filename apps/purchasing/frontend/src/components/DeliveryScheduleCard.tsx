import { useEffect, useState } from "react";
import { fetchConsolidationSuggestions, fetchDeliveryToday, fetchDeliveryWeek, type DeliveryScheduleResponse, type DeliveryWeekResponse } from "../api";
import ProvenanceBadge from "./ProvenanceBadge";

function money(value?: number) {
  return Number.isFinite(value) ? `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : "$0";
}

export default function DeliveryScheduleCard() {
  const [today, setToday] = useState<DeliveryScheduleResponse | null>(null);
  const [week, setWeek] = useState<DeliveryWeekResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [day, weekSchedule, suggestions] = await Promise.all([
          fetchDeliveryToday(),
          fetchDeliveryWeek(),
          fetchConsolidationSuggestions(),
        ]);
        if (mounted) {
          setToday({ ...day, suggestions: day.suggestions ?? suggestions.suggestions });
          setWeek(weekSchedule);
        }
      } catch (caught) {
        if (mounted) setError(caught instanceof Error ? caught.message : "No deliveries scheduled");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void load();
    return () => {
      mounted = false;
    };
  }, []);

  const deliveries = today?.deliveries ?? [];
  const suggestion = today?.suggestions?.[0];

  return (
    <section className="purchase-card">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Delivery Schedule</p>
          <h2 className="purchase-title">Know who arrives before the rush</h2>
        </div>
        <ProvenanceBadge source={today?.provenance === "demo" ? "sample" : today?.provenance} />
      </div>
      {loading ? <p className="purchase-muted">Checking delivery schedule...</p> : null}
      {error ? <p className="purchase-muted">{error}</p> : null}
      {!loading && !error && deliveries.length === 0 ? <p className="purchase-muted">No deliveries scheduled</p> : null}
      {deliveries.length > 0 ? (
        <>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="purchase-muted">
                <tr>
                  <th className="py-2 pr-3">Supplier</th>
                  <th className="py-2 pr-3">Time window</th>
                  <th className="py-2 pr-3">Items</th>
                  <th className="py-2 pr-3">Amount</th>
                </tr>
              </thead>
              <tbody>
                {deliveries.map((delivery) => (
                  <tr key={`${delivery.supplier}-${delivery.window}`} className="border-t" style={{ borderColor: "var(--purchase-border)" }}>
                    <td className="py-2 pr-3 font-semibold">{delivery.supplier}</td>
                    <td className="py-2 pr-3">{delivery.window}</td>
                    <td className="py-2 pr-3">{delivery.items?.join(" + ")}</td>
                    <td className="py-2 pr-3">{money(delivery.amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {suggestion ? (
            <p className="purchase-muted mt-3">{suggestion.text}</p>
          ) : null}
          <p className="purchase-muted mt-2">
            This week: {week?.deliveryCount ?? deliveries.length} deliveries. {week?.opportunities ?? 0} consolidation opportunities. Save {week?.receivingHoursSaved ?? 0} hours receiving.
          </p>
          <p className="purchase-muted mt-2">Sysco under-delivers 3-6% in summer. Auto-flagged for receiving.</p>
        </>
      ) : null}
    </section>
  );
}
