import { useEffect, useState } from "react";
import { getMenuAlerts, getMenuAnalysis, getMenuSummary, type MenuAlert, type MenuItemAnalysis, type MenuSummary } from "../api";
import ProvenanceBadge from "./ProvenanceBadge";

function money(value?: number) {
  return Number.isFinite(value) ? `$${Number(value).toFixed(2)}` : "-";
}

function pct(value?: number) {
  return Number.isFinite(value) ? `${(Number(value) * 100).toFixed(0)}%` : "-";
}

export default function MenuMatrixCard() {
  const [items, setItems] = useState<MenuItemAnalysis[]>([]);
  const [alerts, setAlerts] = useState<MenuAlert[]>([]);
  const [summary, setSummary] = useState<MenuSummary | null>(null);
  const [provenance, setProvenance] = useState<string | undefined>();
  const [note, setNote] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [analysis, nextAlerts, nextSummary] = await Promise.all([getMenuAnalysis(), getMenuAlerts(), getMenuSummary()]);
        if (mounted) {
          setItems(analysis.items ?? []);
          setAlerts(nextAlerts.alerts ?? []);
          setSummary(nextSummary);
          setProvenance(analysis.provenance ?? nextSummary.provenance);
          setNote(analysis.note ?? nextSummary.note);
        }
      } catch (caught) {
        if (mounted) setError(caught instanceof Error ? caught.message : "Connect POS to see menu intelligence");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void load();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <section className="purchase-card">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Menu Intelligence</p>
          <h2 className="purchase-title">Know which dishes deserve attention</h2>
        </div>
        {provenance ? (
          <div className="flex flex-col items-end gap-1">
            <ProvenanceBadge source={provenance === "demo" ? "sample" : provenance} />
            {provenance === "demo" ? <span className="text-xs purchase-muted">Sample data</span> : null}
          </div>
        ) : null}
      </div>
      {note ? <p className="purchase-muted mt-2">{note}</p> : null}
      {loading ? <p className="purchase-muted">Loading menu intelligence...</p> : null}
      {error ? <p className="purchase-muted">{error}</p> : null}
      {!loading && !error && items.length === 0 ? <p className="purchase-muted">Connect POS to see menu intelligence</p> : null}
      {items.length > 0 ? (
        <>
          {alerts[0] ? (
            <div className="mt-3 rounded-md border p-3 text-sm" style={{ borderColor: "var(--purchase-border)" }}>
              {alerts[0].message}
            </div>
          ) : null}
          <div className="mt-4 grid gap-3 md:grid-cols-4">
            <Summary label="Stars" value={summary?.stars} />
            <Summary label="Puzzles" value={summary?.puzzles} />
            <Summary label="Plows" value={summary?.plowhorses} />
            <Summary label="Dogs" value={summary?.dogs} />
          </div>
          <div className="mt-4 rounded-md border p-3" style={{ borderColor: "var(--purchase-border)" }}>
            <div className="mb-2 flex items-center justify-between text-xs purchase-muted">
              <span>Y: Margin</span>
              <span>X: Popularity</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Quadrant
                title="Puzzles"
                tone="text-amber-700"
                note="Low popularity + high margin"
                items={items.filter((item) => item.classification === "puzzle")}
              />
              <Quadrant
                title="Stars"
                tone="text-emerald-700"
                note="High popularity + high margin"
                items={items.filter((item) => item.classification === "star")}
              />
              <Quadrant
                title="Dogs"
                tone="text-red-700"
                note="Low popularity + low margin"
                items={items.filter((item) => item.classification === "dog")}
              />
              <Quadrant
                title="Plows"
                tone="text-blue-700"
                note="High popularity + low margin"
                items={items.filter((item) => item.classification === "plowhorse")}
              />
            </div>
          </div>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="purchase-muted">
                <tr>
                  <th className="py-2 pr-3">Item</th>
                  <th className="py-2 pr-3">Price</th>
                  <th className="py-2 pr-3">Food cost</th>
                  <th className="py-2 pr-3">Margin</th>
                  <th className="py-2 pr-3">Class</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.name} className="border-t" style={{ borderColor: "var(--purchase-border)" }}>
                    <td className="py-2 pr-3 font-semibold">{item.name}</td>
                    <td className="py-2 pr-3">{money(item.price)}</td>
                    <td className="py-2 pr-3">{pct(item.foodCostPct)}</td>
                    <td className="py-2 pr-3">{money(item.contributionMargin)}</td>
                    <td className="py-2 pr-3">{item.classification}</td>
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

function Quadrant({
  title,
  tone,
  note,
  items,
}: {
  title: string;
  tone: string;
  note: string;
  items: MenuItemAnalysis[];
}) {
  return (
    <div className="rounded-md border p-3 min-h-32" style={{ borderColor: "var(--purchase-border)" }}>
      <h3 className={`text-sm font-semibold ${tone}`}>{title}</h3>
      <p className="text-xs purchase-muted">{note}</p>
      <ul className="mt-2 text-sm purchase-muted">
        {items.length > 0 ? items.map((item) => <li key={item.name}>{item.name}</li>) : <li>No dishes here</li>}
      </ul>
    </div>
  );
}

function Summary({ label, value }: { label: string; value?: number }) {
  return (
    <div className="rounded-md border p-3" style={{ borderColor: "var(--purchase-border)" }}>
      <div className="purchase-muted text-sm">{label}</div>
      <strong>{value ?? 0}</strong>
    </div>
  );
}
