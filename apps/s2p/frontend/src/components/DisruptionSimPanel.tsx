import { useEffect, useState } from "react";
import { getImpactSummary, getSimulationScenarios } from "../api";
import type { ImpactSummaryResponse, SimulationScenario, SimulationScenariosResponse } from "../types";

function formatCurrency(value?: number): string {
  if (typeof value !== "number") return "n/a";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function impactClass(value?: string): string {
  if (value === "RED") return "border-red-200 bg-red-50 text-red-700";
  if (value === "AMBER") return "border-amber-200 bg-amber-50 text-amber-700";
  if (value === "GREEN") return "border-emerald-200 bg-emerald-50 text-emerald-700";
  return "border-slate-200 bg-slate-50 text-slate-700";
}

function label(value: string): string {
  return value.replace(/_/g, " ");
}

export function DisruptionSimPanel() {
  const [scenarios, setScenarios] = useState<SimulationScenariosResponse | null>(null);
  const [summary, setSummary] = useState<ImpactSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    Promise.all([getSimulationScenarios(), getImpactSummary()])
      .then(([scenarioResponse, summaryResponse]) => {
        if (cancelled) return;
        if (!scenarioResponse || !summaryResponse) {
          setError("Disruption simulation is unavailable.");
          setScenarios(null);
          setSummary(null);
          return;
        }
        setScenarios(scenarioResponse);
        setSummary(summaryResponse);
      })
      .catch(() => {
        if (!cancelled) {
          setError("Disruption simulation is unavailable.");
          setScenarios(null);
          setSummary(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const rows = scenarios?.scenarios ?? [];

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Scenario planning</p>
          <h2 className="mt-1 text-xl font-semibold text-slate-950">Disruption Simulation</h2>
        </div>
        {loading ? <span className="text-sm text-slate-500">Loading scenarios...</span> : null}
      </div>

      {error ? <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}

      {!loading && !error && rows.length === 0 ? (
        <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-500">
          No disruption scenarios are available.
        </p>
      ) : null}

      {!loading && !error && rows.length > 0 && summary ? (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-5">
            <Metric label="Total exposure" value={formatCurrency(summary.total_quarterly_exposure)} />
            <Metric label="Worst recovery" value={`${summary.worst_case_recovery_days} days`} />
            <Metric label="RED" value={summary.scenarios_causing_red} className="text-red-700" />
            <Metric label="AMBER" value={summary.scenarios_causing_amber} className="text-amber-700" />
            <Metric label="GREEN" value={summary.scenarios_green_safe} className="text-emerald-700" />
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {rows.map((scenario) => (
              <ScenarioCard key={scenario.scenario_id} scenario={scenario} />
            ))}
          </div>
        </>
      ) : null}
    </article>
  );
}

function ScenarioCard({ scenario }: { scenario: SimulationScenario }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-mono text-xs font-semibold text-slate-500">{scenario.scenario_id}</p>
          <h3 className="mt-1 text-sm font-semibold text-slate-950">{scenario.name}</h3>
          <p className="mt-1 text-xs capitalize text-slate-500">{label(scenario.type)}</p>
        </div>
        <span className={`rounded border px-2 py-1 text-xs font-semibold ${impactClass(scenario.conservation_impact)}`}>
          {scenario.conservation_impact || "n/a"}
        </span>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
        <span className="rounded bg-slate-50 p-2 text-slate-600">
          Cost <strong className="block text-slate-950">{formatCurrency(scenario.estimated_quarterly_cost)}</strong>
        </span>
        <span className="rounded bg-slate-50 p-2 text-slate-600">
          Recovery <strong className="block text-slate-950">{scenario.recovery_time_days} days</strong>
        </span>
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  className = "text-slate-950",
}: {
  label: string;
  value: string | number;
  className?: string;
}) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-2 text-lg font-semibold ${className}`}>{value}</p>
    </div>
  );
}
