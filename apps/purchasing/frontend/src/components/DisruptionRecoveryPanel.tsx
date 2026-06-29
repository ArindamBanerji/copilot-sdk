import { useEffect, useState } from "react";
import { BASE } from "../api";

type RecoveryStatus = {
  status?: string;
  days_since_disruption?: number;
  categories_affected?: string[];
  gamma?: number;
  re_calibration_progress_pct?: number;
  estimated_days_to_green?: number;
  narrative?: string;
};

type RecoveryHistory = {
  disruption_id?: string;
  category?: string;
  days_to_green?: number;
  resolved?: boolean;
};

export default function DisruptionRecoveryPanel() {
  const [status, setStatus] = useState<RecoveryStatus | null>(null);
  const [history, setHistory] = useState<RecoveryHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | undefined>();

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const [statusResponse, historyResponse] = await Promise.all([
          fetch(`${BASE}/api/purchasing/disruption/status`),
          fetch(`${BASE}/api/purchasing/disruption/history`),
        ]);
        if (!statusResponse.ok || !historyResponse.ok) throw new Error("Purchasing backend unavailable");
        const nextStatus = (await statusResponse.json()) as RecoveryStatus;
        const nextHistory = (await historyResponse.json()) as RecoveryHistory[];
        if (mounted) {
          setStatus(nextStatus);
          setHistory(nextHistory);
        }
      } catch (caught) {
        if (mounted) setError(caught instanceof Error ? caught.message : "Purchasing backend unavailable");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, []);

  if (loading) {
    return (
      <section className="purchase-card">
        <p className="purchase-kicker">Supply recovery</p>
        <h2 className="purchase-title">Supply Disruption Recovery</h2>
        <p>Loading supply recovery...</p>
      </section>
    );
  }
  if (error) {
    return (
      <section className="purchase-card error-card">
        <p className="purchase-kicker">Supply recovery unavailable</p>
        <h2 className="purchase-title">Supply Disruption Recovery</h2>
        <p>{error}</p>
      </section>
    );
  }

  const progress = Number(status?.re_calibration_progress_pct ?? 0);
  return (
    <section className="purchase-card">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Supply recovery</p>
          <h2 className="purchase-title">Supply Disruption Recovery</h2>
        </div>
        <span className="pill">{status?.status ?? "unknown"}</span>
      </div>
      <p className="purchase-muted">{status?.narrative}</p>
      <div className="stats-row">
        <div><span>Recovery</span><strong>{progress}%</strong></div>
        <div><span>Days since disruption</span><strong>{status?.days_since_disruption ?? 0}</strong></div>
        <div><span>Gamma</span><strong>{Number(status?.gamma ?? 1).toFixed(1)}x</strong></div>
        <div><span>Days to green</span><strong>{status?.estimated_days_to_green ?? 0}</strong></div>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full" style={{ background: "rgba(148, 163, 184, 0.22)" }}>
        <div className="h-full rounded-full" style={{ width: `${Math.max(0, Math.min(progress, 100))}%`, background: "var(--purchase-primary)" }} />
      </div>
      <p className="mt-3 text-sm">Categories affected: {(status?.categories_affected || []).join(", ") || "none"}</p>
      <p className="mt-2 text-sm">Accelerated learning: {Number(status?.gamma ?? 1) > 1 ? "active" : "inactive"}</p>
      <div className="mt-4 grid gap-2 text-sm">
        {history.slice(0, 2).map((item) => (
          <div key={item.disruption_id} className="rounded-md border px-3 py-2">
            {item.category}: {item.days_to_green} days to green, {item.resolved ? "resolved" : "recovering"}
          </div>
        ))}
      </div>
    </section>
  );
}
