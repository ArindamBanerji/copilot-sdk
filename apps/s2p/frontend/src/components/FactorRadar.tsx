import {
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip
} from "recharts";
import type { FactorContribution } from "../types";

function label(value: string): string {
  return value.replace(/_/g, " ");
}

function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function directionLabel(value: string): string {
  if (value === "above_centroid") return "above centroid";
  if (value === "below_centroid") return "below centroid";
  if (value === "at_centroid") return "at centroid";
  return value.replace(/_/g, " ");
}

export function FactorRadar({
  factors,
  title,
  dkStatus,
  closestAction,
  recommendedAction
}: {
  factors: FactorContribution[];
  title?: string;
  dkStatus?: string;
  closestAction?: string;
  recommendedAction?: string;
}) {
  const rows = factors.map((factor) => ({
    factor: label(factor.factor_name),
    decision: factor.factor_value,
    centroid: factor.centroid_value,
    distance: factor.distance,
    dkWeight: factor.dk_weight,
    direction: directionLabel(factor.direction)
  }));

  const dkAvailable = dkStatus === "available";

  return (
    <section className="rounded-md border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Factor proximity</p>
          <h3 className="mt-1 text-base font-semibold text-slate-950">{title ?? "Decision vs centroid"}</h3>
          {closestAction || recommendedAction ? (
            <p className="mt-1 text-xs text-slate-500">
              Closest {closestAction ? label(closestAction) : "n/a"} · recommended{" "}
              {recommendedAction ? label(recommendedAction) : "n/a"}
            </p>
          ) : null}
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
          DK {dkAvailable ? "available" : "learning"}
        </span>
      </div>

      {rows.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">No factor contributions are available for this decision.</p>
      ) : (
        <>
          <div className="mt-4 h-72 w-full">
            <ResponsiveContainer>
              <RadarChart data={rows} outerRadius="70%">
                <PolarGrid />
                <PolarAngleAxis dataKey="factor" tick={{ fontSize: 11 }} />
                <PolarRadiusAxis tick={{ fontSize: 10 }} />
                <Tooltip
                  formatter={(value, name) => {
                    if (typeof value !== "number") return [String(value), String(name)];
                    return [value.toFixed(3), String(name)];
                  }}
                />
                <Legend />
                <Radar name="Decision" dataKey="decision" stroke="#D97706" fill="#D97706" fillOpacity={0.24} />
                <Radar name="Centroid" dataKey="centroid" stroke="#0F766E" fill="#0F766E" fillOpacity={0.18} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-4 grid gap-2 md:grid-cols-2">
            {factors.map((factor) => (
              <div key={factor.factor_name} className="rounded-md bg-slate-50 p-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs font-semibold capitalize text-slate-700">{label(factor.factor_name)}</span>
                  <span className="text-xs text-slate-500">{directionLabel(factor.direction)}</span>
                </div>
                <p className="mt-2 text-xs text-slate-600">
                  Decision {percent(factor.factor_value)} · centroid {percent(factor.centroid_value)} · distance{" "}
                  {factor.distance.toFixed(3)}
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  {dkAvailable
                    ? `DK weight ${factor.dk_weight.toFixed(3)}`
                    : "Trust weights unavailable; using uniform display ordering."}
                </p>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
