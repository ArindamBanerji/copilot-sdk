import { useEffect, useMemo, useState } from "react";
import { fetchAlerts, type PurchasingAlert } from "../api";
import ProvenanceBadge from "./ProvenanceBadge";

const severityClass: Record<string, string> = {
  critical: "#dc2626",
  warning: "#d97706",
  info: "#2563eb",
};

export default function AlertDashboardCard() {
  const [alerts, setAlerts] = useState<PurchasingAlert[]>([]);
  const [provenance, setProvenance] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchAlerts();
        if (mounted) {
          setAlerts(result.alerts ?? []);
          setProvenance(result.provenance);
        }
      } catch (caught) {
        if (mounted) setError(caught instanceof Error ? caught.message : "All clear. No active alerts.");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void load();
    return () => {
      mounted = false;
    };
  }, []);

  const counts = useMemo(() => alerts.reduce<Record<string, number>>((acc, alert) => {
    const key = alert.severity ?? "info";
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {}), [alerts]);

  return (
    <section className="purchase-card">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Active Alerts</p>
          <h2 className="purchase-title">What needs a manager today</h2>
        </div>
        <ProvenanceBadge source={provenance === "demo" ? "sample" : provenance} />
      </div>
      {loading ? <p className="purchase-muted">Checking kitchen alerts...</p> : null}
      {error ? <p className="purchase-muted">{error}</p> : null}
      {!loading && !error && alerts.length === 0 ? <p className="purchase-muted">All clear. No active alerts.</p> : null}
      {alerts.length > 0 ? (
        <>
          <div className="mt-4 flex flex-wrap gap-2">
            {["critical", "warning", "info"].map((severity) => (
              <span key={severity} className="rounded-full px-3 py-1 text-sm font-semibold" style={{ background: `${severityClass[severity]}22`, color: severityClass[severity] }}>
                {severity}: {counts[severity] ?? 0}
              </span>
            ))}
          </div>
          <div className="mt-4 space-y-3">
            {alerts.map((alert) => (
              <div key={`${alert.alertType}-${alert.title}`} className="rounded-md border p-3" style={{ borderColor: "var(--purchase-border)" }}>
                <div className="text-sm font-semibold" style={{ color: severityClass[alert.severity ?? "info"] }}>
                  {alert.severity ?? "info"}
                </div>
                <strong>{alert.title}</strong>
                <p className="purchase-muted mt-1 text-sm">{alert.recommendation}</p>
              </div>
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}
