import { useEffect, useMemo, useState } from "react";

type Recommendation = {
  source?: string;
  provider?: string;
  cost?: number;
  annual_value?: number;
  roi?: number | string;
  priority?: string;
  narrative?: string;
};

type AcquisitionResponse = {
  recommendations?: Recommendation[];
  narrative?: string;
  monetization?: { narrative?: string; opportunities?: Array<Record<string, unknown>> };
};

function money(value: unknown) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "N/A";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(numeric);
}

function roiLabel(value: unknown) {
  if (value === "infinite") return "infinite ROI";
  const numeric = Number(value);
  return Number.isFinite(numeric) ? `${numeric.toFixed(1)}x ROI` : "ROI pending";
}

export default function AcquisitionPanel() {
  const [data, setData] = useState<AcquisitionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch("http://127.0.0.1:8030/api/dataops/di/acquisitions");
        if (!response.ok) throw new Error("Acquisition recommendations unavailable");
        const payload = (await response.json()) as AcquisitionResponse;
        if (!cancelled) setData(payload);
      } catch (caught) {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "Acquisition recommendations unavailable");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const recommendations = useMemo(() => data?.recommendations || [], [data]);
  const top = recommendations[0];

  if (loading) return <section className="copilot-card p-5 text-sm dataops-muted">Loading acquisition recommendations...</section>;

  return (
    <section className="copilot-card p-5">
      <div className="mb-4">
        <p className="dataops-kicker">External data strategy</p>
        <h2 className="dataops-title">Data Acquisition Recommendations</h2>
      </div>
      {error ? <p className="text-sm" style={{ color: "var(--copilot-danger)" }}>{error}</p> : null}
      {top ? (
        <p className="mb-4 rounded-md border px-3 py-2 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
          Priority: {top.source} ({Number(top.cost) === 0 ? "free, " : `${money(top.cost)}, `}{roiLabel(top.roi)})
        </p>
      ) : null}
      <div className="grid gap-3">
        {recommendations.map((item) => {
          const isFree = Number(item.cost) === 0;
          return (
            <article key={`${item.source}-${item.provider}`} className="rounded-md border p-3" style={{ borderColor: isFree ? "var(--copilot-primary)" : "var(--copilot-border)" }}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold">{item.source}</h3>
                  <p className="text-xs dataops-muted">{item.provider}</p>
                </div>
                <span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: isFree ? "var(--copilot-primary-light)" : "var(--copilot-surface-muted)", color: isFree ? "var(--copilot-primary)" : "var(--copilot-text)" }}>
                  {isFree ? "free" : item.priority || "priority"}
                </span>
              </div>
              <div className="mt-3 grid gap-2 text-sm md:grid-cols-3">
                <div><span className="dataops-muted">Cost</span><strong className="block">{money(item.cost)}</strong></div>
                <div><span className="dataops-muted">Annual value</span><strong className="block">{money(item.annual_value)}</strong></div>
                <div><span className="dataops-muted">ROI</span><strong className="block">{roiLabel(item.roi)}</strong></div>
              </div>
              {item.narrative ? <p className="mt-3 text-sm">{item.narrative}</p> : null}
            </article>
          );
        })}
      </div>
      {data?.monetization?.narrative ? <p className="mt-4 text-sm dataops-muted">{data.monetization.narrative}</p> : null}
    </section>
  );
}
