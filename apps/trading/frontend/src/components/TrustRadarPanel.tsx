import { useEffect, useMemo, useState } from "react";
import { getTrustAnalysis } from "../api";
import type { TrustAnalysisResponse, TrustScore } from "../types";

const neutralScore: TrustScore = {
  variance: 0,
  mean: 0.5,
  nSamples: 0,
  trustLabel: "insufficient_data",
  sigma: 0,
};

function labelForFactor(factor: string): string {
  return factor
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatTrustLabel(label: string): string {
  return label.replace(/_/g, " ");
}

function varianceWidth(variance: number): string {
  return `${Math.min(100, Math.round((Math.max(0, variance) / 0.15) * 100))}%`;
}

export default function TrustRadarPanel() {
  const [data, setData] = useState<TrustAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    let cancelled = false;

    getTrustAnalysis()
      .then((response) => {
        if (cancelled) return;
        setData(response);
        setUnavailable(!response);
      })
      .catch(() => {
        if (cancelled) return;
        setUnavailable(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const implemented = useMemo(() => new Set(data?.implemented ?? []), [data]);

  if (loading) {
    return (
      <section className="copilot-card p-5">
        <p className="text-sm uppercase tracking-wide trading-muted">Signal Trust Analysis</p>
        <h2 className="mt-1 text-xl font-semibold text-white">Loading signal trust...</h2>
      </section>
    );
  }

  if (unavailable || !data) {
    return (
      <section className="copilot-card p-5">
        <p className="text-sm uppercase tracking-wide trading-muted">Signal Trust Analysis</p>
        <h2 className="mt-1 text-xl font-semibold text-white">Trust analysis unavailable</h2>
        <p className="mt-2 text-sm trading-muted">Variance-based signal trust is not available right now.</p>
      </section>
    );
  }

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-wide trading-muted">Signal Trust Analysis</p>
          <h2 className="mt-1 text-xl font-semibold text-white">
            Which of your signals are stable across your outcomes?
          </h2>
          <p className="mt-2 text-sm trading-muted">
            Variance and noise across imported trades. This is a stability view, not a causal ranking.
          </p>
        </div>
        {data.totalTrades > 0 ? (
          <div className="rounded-md border border-white/10 px-3 py-2 text-right">
            <p className="text-2xl font-semibold text-white">{data.totalTrades}</p>
            <p className="text-xs uppercase tracking-wide trading-muted">trades analyzed</p>
          </div>
        ) : null}
      </div>

      {data.totalTrades === 0 ? (
        <div className="mt-4 rounded-md border border-dashed border-white/15 p-4 text-sm trading-muted">
          Import trades to see which signals you should trust.
        </div>
      ) : null}

      {data.heroInsight ? (
        <div className="mt-4 rounded-md border border-amber-400/30 bg-amber-400/10 p-4">
          <p className="text-sm font-semibold text-amber-100">{data.heroInsight.message}</p>
          <div className="mt-3 grid gap-2 text-xs trading-muted sm:grid-cols-2">
            <span>
              Noisiest: {labelForFactor(data.heroInsight.overusedFactor)} (
              {data.heroInsight.overusedSigma.toFixed(3)} sigma)
            </span>
            <span>
              Steadiest: {labelForFactor(data.heroInsight.underusedFactor)} (
              {data.heroInsight.underusedSigma.toFixed(3)} sigma)
            </span>
          </div>
        </div>
      ) : null}

      <div className="mt-5 space-y-3">
        {data.factors.map((factor) => {
          const score = data.trustScores[factor] ?? neutralScore;
          const isImplemented = implemented.has(factor);

          return (
            <div
              key={factor}
              className={`rounded-md border border-white/10 bg-white/[0.03] p-3 ${isImplemented ? "" : "opacity-60"}`}
            >
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-semibold text-white">{labelForFactor(factor)}</p>
                  <p className="text-xs trading-muted">
                    {isImplemented ? formatTrustLabel(score.trustLabel) : "not computed"} - {score.nSamples} samples
                  </p>
                </div>
                <div className="text-xs trading-muted sm:text-right">
                  <p>variance {score.variance.toFixed(3)}</p>
                  <p>sigma {score.sigma.toFixed(3)}</p>
                </div>
              </div>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
                <div className="h-full rounded-full bg-emerald-400" style={{ width: varianceWidth(score.variance) }} />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
