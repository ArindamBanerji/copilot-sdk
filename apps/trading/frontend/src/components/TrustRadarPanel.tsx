import { useEffect, useMemo, useState } from "react";
import { getTrustAnalysis } from "../api";
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
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

function scoreName(score: TrustScore | undefined, fallback = ""): string {
  return score?.name || fallback;
}

function scoreRows(data: TrustAnalysisResponse, selectedCategory: string): TrustScore[] {
  if (data.mode === "dk" && selectedCategory && data.perCategory?.[selectedCategory]) {
    return data.perCategory[selectedCategory];
  }
  if (data.factorDetails?.length) {
    return data.factorDetails;
  }
  return (data.factors ?? []).map((factor) => ({
    ...neutralScore,
    ...(data.trustScores[factor] ?? {}),
    name: factor,
  }));
}

function heroText(data: TrustAnalysisResponse): string | null {
  if (!data.heroInsight) return null;
  if (typeof data.heroInsight === "string") return data.heroInsight;
  return data.heroInsight.message;
}

export default function TrustRadarPanel() {
  const [data, setData] = useState<TrustAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const unavailable = Boolean(error) || !data;
  const [selectedCategory, setSelectedCategory] = useState("");

  const implemented = useMemo(() => new Set(data?.implemented ?? []), [data]);
  const factors = useMemo(() => (data ? scoreRows(data, selectedCategory) : []), [data, selectedCategory]);
  const isDkMode = data?.mode === "dk";
  const insight = data ? heroText(data) : null;
  const topSignal = selectedCategory ? scoreName(factors[0]) : data?.topSignal || scoreName(factors[0]);

  useEffect(() => {
    let cancelled = false;
    getTrustAnalysis()
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch((loadError) => {
        console.debug("trust analysis unavailable", loadError);
        if (!cancelled) setError("Trust analysis unavailable.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <section className="copilot-card p-5" data-testid="trust-radar-panel">
        <p className="text-sm uppercase tracking-wide trading-muted">Signal Trust Analysis</p>
        <h2 className="mt-1 text-xl font-semibold text-white">Loading signal trust...</h2>
      </section>
    );
  }

  if (unavailable || !data) {
    return (
      <section className="copilot-card p-5" data-testid="trust-radar-panel">
        <p className="text-sm uppercase tracking-wide trading-muted">Signal Trust Analysis</p>
        <h2 className="mt-1 text-xl font-semibold text-white">Trust analysis unavailable</h2>
        <p className="mt-2 text-sm trading-muted">Variance-based signal trust is not available right now.</p>
      </section>
    );
  }

  return (
    <section className="copilot-card p-5" data-testid="trust-radar-panel">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-wide trading-muted">Signal Trust Analysis</p>
          <h2 className="mt-1 text-xl font-semibold text-white">
            Which of your signals are stable across your outcomes?
          </h2>
          <p className="mt-2 text-sm trading-muted">
            {isDkMode
              ? "DK weights learned from verified outcomes. Lower weights are signals the engine learned to ignore."
              : "Variance and noise across imported trades. This is a stability view, not a causal ranking."}
          </p>
        </div>
        <div className="flex flex-col gap-2 text-right">
          {data.totalTrades > 0 ? (
            <div className="rounded-md border border-white/10 px-3 py-2">
              <p className="text-2xl font-semibold text-white">{data.totalTrades}</p>
              <p className="text-xs uppercase tracking-wide trading-muted">trades analyzed</p>
            </div>
          ) : null}
          <span className="rounded-md border border-white/10 px-3 py-1 text-xs uppercase tracking-wide trading-muted">
            Phase {data.phase || "A"} · {isDkMode ? "DK radar" : "variance"}
          </span>
        </div>
      </div>

      {!isDkMode && typeof data.decisionsUntilDk === "number" ? (
        <div className="mt-4 rounded-md border border-sky-400/25 bg-sky-400/10 p-3 text-sm text-sky-100">
          Building trust model - {data.decisionsUntilDk} more decisions needed for DK radar.
        </div>
      ) : null}

      {data.totalTrades === 0 ? (
        <div className="mt-4 rounded-md border border-dashed border-white/15 p-4 text-sm trading-muted">
          Import trades to see which signals you should trust.
        </div>
      ) : null}

      {insight ? (
        <div className="mt-4 rounded-md border border-amber-400/30 bg-amber-400/10 p-4">
          <p className="text-sm font-semibold text-amber-100">{insight}</p>
        </div>
      ) : null}

      {isDkMode ? (
        <>
          <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-white">
              Your most trusted signal: <span className="font-semibold">{topSignal ? labelForFactor(topSignal) : "n/a"}</span>
            </p>
            <label className="flex items-center gap-2 text-sm trading-muted">
              Category
              <select
                className="rounded-md border border-white/10 bg-slate-950 px-3 py-2 text-white"
                value={selectedCategory}
                onChange={(event) => setSelectedCategory(event.target.value)}
              >
                <option value="">Overall</option>
                {(data.availableCategories ?? []).map((category) => (
                  <option key={category} value={category}>
                    {labelForFactor(category)}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="mt-4 h-80 w-full">
            <ResponsiveContainer>
              <RadarChart
                data={factors.map((factor) => ({
                  name: labelForFactor(scoreName(factor)),
                  weight: factor.dkWeight ?? 0,
                }))}
                outerRadius="70%"
              >
                <PolarGrid />
                <PolarAngleAxis dataKey="name" tick={{ fontSize: 11, fill: "#CBD5E1" }} />
                <PolarRadiusAxis domain={[0, 1]} tick={{ fontSize: 10, fill: "#94A3B8" }} />
                <Tooltip
                  formatter={(value) => [
                    typeof value === "number" ? value.toFixed(3) : String(value),
                    "DK weight",
                  ]}
                />
                <Radar name="DK weight" dataKey="weight" stroke="#22C55E" fill="#22C55E" fillOpacity={0.22} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-5 grid gap-3 md:grid-cols-2">
            {factors.map((factor) => {
              const name = scoreName(factor);
              return (
                <div
                  key={name}
                  className={`rounded-md border p-3 ${
                    factor.isNoise ? "border-orange-400/40 bg-orange-400/10" : "border-white/10 bg-white/[0.03]"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-semibold text-white">{labelForFactor(name)}</p>
                    <span className={factor.isNoise ? "text-xs font-semibold text-orange-200" : "text-xs trading-muted"}>
                      {factor.isNoise ? "noise" : formatTrustLabel(factor.trustLabel)}
                    </span>
                  </div>
                  <p className="mt-2 text-xs trading-muted">DK weight {(factor.dkWeight ?? 0).toFixed(3)}</p>
                </div>
              );
            })}
          </div>
        </>
      ) : (
        <div className="mt-5 space-y-3">
          {factors.map((factor) => {
            const name = scoreName(factor);
            const isImplemented = implemented.has(name);

            return (
              <div
                key={name}
                className={`rounded-md border border-white/10 bg-white/[0.03] p-3 ${isImplemented ? "" : "opacity-60"}`}
              >
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-semibold text-white">{labelForFactor(name)}</p>
                    <p className="text-xs trading-muted">
                      {isImplemented ? formatTrustLabel(factor.trustLabel) : "not computed"} - {factor.nSamples} samples
                    </p>
                  </div>
                  <div className="text-xs trading-muted sm:text-right">
                    <p>variance {factor.variance.toFixed(3)}</p>
                    <p>sigma {factor.sigma.toFixed(3)}</p>
                  </div>
                </div>
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
                  <div className="h-full rounded-full bg-emerald-400" style={{ width: varianceWidth(factor.variance) }} />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
