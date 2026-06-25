import { useEffect, useState } from "react";
import { fetchEventHistory, fetchEventPlan, type EventPlanResponse } from "../api";
import ProvenanceBadge from "./ProvenanceBadge";

function money(value?: number) {
  return Number.isFinite(value) ? `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : "$0";
}

export default function EventPlannerCard() {
  const [guests, setGuests] = useState(80);
  const [cuisine, setCuisine] = useState("mixed");
  const [plan, setPlan] = useState<EventPlanResponse | null>(null);
  const [historyCount, setHistoryCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [nextPlan, history] = await Promise.all([fetchEventPlan(guests, cuisine), fetchEventHistory()]);
        if (mounted) {
          setPlan(nextPlan);
          setHistoryCount(history.length);
        }
      } catch (caught) {
        if (mounted) setError(caught instanceof Error ? caught.message : "No events planned");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void load();
    return () => {
      mounted = false;
    };
  }, [guests, cuisine]);

  return (
    <section className="purchase-card">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Event Intelligence</p>
          <h2 className="purchase-title">Plan the next catering rush before service</h2>
        </div>
        <ProvenanceBadge source={plan?.provenance === "demo" ? "sample" : plan?.provenance} />
      </div>
      {loading ? <p className="purchase-muted">Building event plan...</p> : null}
      {error ? <p className="purchase-muted">{error}</p> : null}
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <label className="text-sm font-semibold">
          Guest count
          <input
            className="mt-1 w-full rounded-md border px-3 py-2"
            min={0}
            type="number"
            value={guests}
            onChange={(event) => setGuests(Number(event.target.value || 0))}
            style={{ borderColor: "var(--purchase-border)" }}
          />
        </label>
        <label className="text-sm font-semibold">
          Cuisine
          <select
            className="mt-1 w-full rounded-md border px-3 py-2"
            value={cuisine}
            onChange={(event) => setCuisine(event.target.value)}
            style={{ borderColor: "var(--purchase-border)" }}
          >
            <option value="mixed">Mixed</option>
            <option value="american">American</option>
            <option value="italian">Italian</option>
          </select>
        </label>
      </div>
      {!loading && !error && !plan ? <p className="purchase-muted">No events planned</p> : null}
      {plan ? (
        <>
          <p className="mt-3 text-sm font-semibold">
            For {plan.guestCount ?? 80} guests, you will need about {plan.categories?.[0]?.quantityLbs ?? 36} lbs protein.
          </p>
          <p className="purchase-muted mt-1">
            Based on {plan.similarEvents ?? historyCount} similar events. Expected waste: {Math.round(Number(plan.expectedWastePct ?? 0) * 100)}%.
          </p>
          <p className="purchase-muted mt-1">{plan.note ?? "Last unplanned event cost $1,200 in waste."}</p>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="purchase-muted">
                <tr>
                  <th className="py-2 pr-3">Category</th>
                  <th className="py-2 pr-3">Quantity</th>
                  <th className="py-2 pr-3">Est cost</th>
                </tr>
              </thead>
              <tbody>
                {(plan.categories ?? []).map((row) => (
                  <tr key={row.category} className="border-t" style={{ borderColor: "var(--purchase-border)" }}>
                    <td className="py-2 pr-3 font-semibold">{String(row.category ?? "").replace("_", " ")}</td>
                    <td className="py-2 pr-3">{row.quantityLbs} lbs</td>
                    <td className="py-2 pr-3">{money(row.estimatedCost)}</td>
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
