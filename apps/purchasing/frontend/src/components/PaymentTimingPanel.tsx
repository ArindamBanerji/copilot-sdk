import { useEffect, useState } from "react";
import { BASE } from "../api";

type PaymentRow = {
  supplier?: string;
  avg_payment_days?: number;
  early_pay_discount_pct?: number;
  discount_capture_rate?: number;
  annual_discount_value?: number;
  recommendation?: string;
};

type PaymentSummary = {
  avg_dpo?: number;
  capture_rate_pct?: number;
  annual_opportunity?: number;
  narrative?: string;
};

function money(value: unknown) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? `$${numeric.toLocaleString(undefined, { maximumFractionDigits: 0 })}` : "$0";
}

export default function PaymentTimingPanel() {
  const [rows, setRows] = useState<PaymentRow[]>([]);
  const [summary, setSummary] = useState<PaymentSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | undefined>();

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const [timingResponse, summaryResponse] = await Promise.all([
          fetch(`${BASE}/api/purchasing/payment/timing`),
          fetch(`${BASE}/api/purchasing/payment/summary`),
        ]);
        if (!timingResponse.ok || !summaryResponse.ok) throw new Error("Purchasing backend unavailable");
        const nextRows = (await timingResponse.json()) as PaymentRow[];
        const nextSummary = (await summaryResponse.json()) as PaymentSummary;
        if (mounted) {
          setRows(nextRows);
          setSummary(nextSummary);
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
        <p className="purchase-kicker">Supplier payments</p>
        <h2 className="purchase-title">Payment Timing Intelligence</h2>
        <p>Loading payment timing...</p>
      </section>
    );
  }
  if (error) {
    return (
      <section className="purchase-card error-card">
        <p className="purchase-kicker">Payment timing unavailable</p>
        <h2 className="purchase-title">Payment Timing Intelligence</h2>
        <p>{error}</p>
      </section>
    );
  }

  return (
    <section className="purchase-card">
      <p className="purchase-kicker">Supplier payments</p>
      <h2 className="purchase-title">Payment Timing Intelligence</h2>
      <p className="purchase-muted">{summary?.narrative}</p>
      <div className="stats-row">
        <div><span>DPO</span><strong>{Number(summary?.avg_dpo ?? 0).toFixed(1)}</strong></div>
        <div><span>Capture rate</span><strong>{Number(summary?.capture_rate_pct ?? 0).toFixed(1)}%</strong></div>
        <div><span>Annual opportunity</span><strong>{money(summary?.annual_opportunity)}</strong></div>
      </div>
      <div className="mt-4 grid gap-2">
        {rows.map((row) => (
          <article key={row.supplier} className="rounded-md border px-3 py-2 text-sm">
            <strong>{row.supplier}</strong>: pays in {row.avg_payment_days} days. {row.early_pay_discount_pct}% discount. Capture rate {Math.round(Number(row.discount_capture_rate ?? 0) * 100)}%.
            <p className="purchase-muted">{row.recommendation}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
