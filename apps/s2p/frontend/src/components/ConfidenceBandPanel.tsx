import { useEffect, useState } from "react";

type ThresholdBand = {
  min_amount: number;
  max_amount: number | null;
  auto_threshold: number;
  calibration: "geometry_derived";
};

type ThresholdPayload = {
  thresholds: ThresholdBand[];
  k14_noise_rate: number;
  calibration_source: "geometry_derived";
  calibration_note: string;
};

type ConfidenceBandPanelProps = {
  invoiceAmount?: number;
};

function formatAmount(amount: number): string {
  if (amount >= 1000) return `$${amount / 1000}K`;
  return `$${amount}`;
}

function formatRange(band: ThresholdBand): string {
  return band.max_amount === null
    ? `${formatAmount(band.min_amount)}+`
    : `${formatAmount(band.min_amount)}–${formatAmount(band.max_amount)}`;
}

function bandColor(index: number): string {
  return ["bg-emerald-500", "bg-lime-500", "bg-amber-500", "bg-rose-500"][index] ?? "bg-slate-500";
}

function isHighlighted(band: ThresholdBand, invoiceAmount: number | undefined): boolean {
  if (invoiceAmount === undefined || invoiceAmount < band.min_amount) return false;
  return band.max_amount === null || invoiceAmount < band.max_amount;
}

export function ConfidenceBandPanel({ invoiceAmount }: ConfidenceBandPanelProps) {
  const [payload, setPayload] = useState<ThresholdPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/s2p/confidence/thresholds")
      .then((response) => {
        if (!response.ok) throw new Error(`Threshold request failed (${response.status})`);
        return response.json() as Promise<ThresholdPayload>;
      })
      .then((body) => {
        if (!cancelled) setPayload(body);
      })
      .catch((requestError: unknown) => {
        if (!cancelled) setError(requestError instanceof Error ? requestError.message : "Unable to load thresholds");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <article data-testid="confidence-band-panel" className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Dollar confidence routing</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">Confidence bands by invoice value</h2>
          <p className="mt-1 text-sm text-slate-600">
            Higher-value invoices require stronger geometry-derived evidence before auto-approval.
          </p>
        </div>
        <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
          92% noise — geometry-calibrated
        </span>
      </div>

      {error ? (
        <p className="mt-5 rounded-md bg-rose-50 p-4 text-sm text-rose-700">{error}</p>
      ) : payload === null ? (
        <p className="mt-5 text-sm text-slate-500">Loading confidence bands...</p>
      ) : (
        <div className="mt-5 space-y-3">
          {payload.thresholds.map((band, index) => {
            const highlighted = isHighlighted(band, invoiceAmount);
            return (
              <div
                key={`${band.min_amount}-${band.max_amount ?? "plus"}`}
                className={`rounded-lg border p-3 ${highlighted ? "border-slate-900 bg-slate-50" : "border-slate-200"}`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
                  <span className="font-semibold text-slate-900">{formatRange(band)}</span>
                  <span className="text-slate-600">{Math.round(band.auto_threshold * 100)}% threshold</span>
                  <span className="font-semibold text-slate-700">
                    {band.auto_threshold <= 0.8 ? "auto" : "manual unless highly confident"}
                  </span>
                </div>
                <div className="mt-2 h-2 rounded-full bg-slate-100">
                  <div className={`h-2 rounded-full ${bandColor(index)}`} style={{ width: `${band.auto_threshold * 100}%` }} />
                </div>
                {highlighted && invoiceAmount !== undefined ? (
                  <p className="mt-2 text-xs font-medium text-slate-700">
                    ${invoiceAmount.toLocaleString()} falls in this band
                  </p>
                ) : null}
              </div>
            );
          })}
        </div>
      )}

      <p className="mt-4 text-xs text-slate-500">Calibration source: {payload?.calibration_source ?? "geometry_derived"}</p>
    </article>
  );
}

export default ConfidenceBandPanel;
