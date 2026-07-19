import { useEffect, useMemo, useState } from "react";
import { fetchVIXTiming } from "../api";
import type { VIXTimingBucket, VIXTimingCell, VIXTimingResponse } from "../types";

const holdOrder = ["intraday", "1_3_days", "1_2_weeks", "2_plus_weeks"];
const vixOrder = ["low", "medium", "high"];

function pct(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "-";
}

function cellClass(cell: VIXTimingCell | undefined): string {
  const count = Number(cell?.count || 0);
  if (count === 0) return "border-white/10 bg-white/5 text-slate-300";
  const accuracy = typeof cell?.accuracy === "number" ? cell.accuracy : 0;
  if (accuracy > 0.6) return "border-emerald-300/50 bg-emerald-500/10 text-emerald-100";
  if (accuracy >= 0.4) return "border-amber-300/50 bg-amber-500/10 text-amber-100";
  return "border-red-300/50 bg-red-500/10 text-red-100";
}

function bucketLabel(bucket: VIXTimingBucket | null | undefined, payload: VIXTimingResponse): string {
  if (!bucket) return "-";
  const hold = bucket.holdBucket || bucket.hold || "";
  const vix = bucket.vixBucket || bucket.vix || "";
  const holdLabel = payload.holdLabels?.[hold] || hold.replace(/_/g, " ");
  const vixLabel = payload.vixLabels?.[vix] || vix.replace(/_/g, " ");
  return `${holdLabel} / ${vixLabel}`;
}

function BucketCallout({ title, bucket, payload }: { title: string; bucket?: VIXTimingBucket | null; payload: VIXTimingResponse }) {
  return (
    <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs uppercase tracking-wide trading-muted">{title}</div>
      <div className="mt-1 font-semibold">{bucketLabel(bucket, payload)}</div>
      {bucket ? (
        <div className="mt-1 text-sm trading-muted">
          {pct(bucket.accuracy)} · {bucket.count ?? 0} trades
        </div>
      ) : (
        <div className="mt-1 text-sm trading-muted">No populated bucket yet.</div>
      )}
    </div>
  );
}

export default function VIXTimingPanel() {
  const [payload, setPayload] = useState<VIXTimingResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const matrix = payload?.matrix || {};
  const recommendations = useMemo(() => payload?.recommendations || [], [payload]);
  const hasAnalysis = Number(payload?.totalAnalyzed || 0) > 0;

  useEffect(() => {
    let cancelled = false;
    fetchVIXTiming()
      .then((data) => {
        if (!cancelled) setPayload(data);
      })
      .catch((loadError) => {
        console.debug("vix timing unavailable", loadError);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-wide trading-muted">Performance analysis</p>
          <h2 className="mt-1 text-xl font-semibold">VIX-Aware Hold Timing</h2>
          <p className="mt-2 text-sm trading-muted">
            Hold-period outcomes are grouped by VIX conditions to surface where historical results concentrated.
          </p>
        </div>
        <div className="rounded-md border px-3 py-2 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs uppercase tracking-wide trading-muted">Analyzed</div>
          <div className="font-semibold">{payload?.totalAnalyzed ?? 0}</div>
        </div>
      </div>

      {loading ? <div className="mt-4 text-sm trading-muted">Loading VIX timing analysis...</div> : null}

      {!loading && !payload ? (
        <div className="mt-4 rounded-md border border-dashed border-white/15 p-4 text-sm trading-muted">
          VIX timing analysis unavailable.
        </div>
      ) : null}

      {!loading && payload && !hasAnalysis ? (
        <div className="mt-4 rounded-md border border-dashed border-white/15 p-4 text-sm trading-muted">
          Score more trades with entry/exit times for VIX analysis.
        </div>
      ) : null}

      {!loading && payload && hasAnalysis ? (
        <div className="mt-4 grid gap-4">
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr>
                  <th className="p-2 text-left trading-muted">Hold period</th>
                  {vixOrder.map((vix) => (
                    <th key={vix} className="p-2 text-center trading-muted">
                      {payload.vixLabels?.[vix] || vix}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {holdOrder.map((hold) => (
                  <tr key={hold}>
                    <th className="p-2 text-left font-semibold">{payload.holdLabels?.[hold] || hold.replace(/_/g, " ")}</th>
                    {vixOrder.map((vix) => {
                      const cell = matrix[hold]?.[vix];
                      return (
                        <td key={`${hold}-${vix}`} className="p-1 text-center">
                          <div className={`rounded-md border px-3 py-2 ${cellClass(cell)}`}>
                            <div className="font-semibold">{pct(cell?.accuracy)}</div>
                            <div className="text-xs opacity-80">{cell?.count ?? 0} trades</div>
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <BucketCallout title="Best bucket" bucket={payload.bestBucket} payload={payload} />
            <BucketCallout title="Worst bucket" bucket={payload.worstBucket} payload={payload} />
          </div>
        </div>
      ) : null}

      {!loading && payload ? (
        <div className="mt-4 rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
          <h3 className="text-base font-semibold">Performance Observations</h3>
          {recommendations.length ? (
            <ul className="mt-3 grid gap-2 text-sm trading-muted">
              {recommendations.map((recommendation, index) => (
                <li key={`${index}-${recommendation}`} className="rounded-md bg-white/5 px-3 py-2">
                  {recommendation}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-sm trading-muted">No VIX timing observations available.</p>
          )}
        </div>
      ) : null}
    </section>
  );
}
