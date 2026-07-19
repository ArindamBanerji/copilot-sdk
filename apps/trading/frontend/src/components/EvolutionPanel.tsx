import { useEffect, useMemo, useState } from "react";
import { fetchActiveVariant, fetchEvolutionActive, fetchEvolutionLog, type ParameterEvolutionActive, type TradingEvolutionLogEntry } from "../api";
import ProvenanceBadge from "./ProvenanceBadge";

function variantId(entry?: TradingEvolutionLogEntry | null): string {
  return entry?.variantId ?? entry?.variant_id ?? "none";
}

function createdAt(entry: TradingEvolutionLogEntry): string {
  return entry.createdAt ?? entry.created_at ?? "";
}

function avgImprovement(entry: TradingEvolutionLogEntry): number {
  return Number(entry.avgImprovementPp ?? entry.avg_improvement_pp ?? 0);
}

function resultImprovement(result: NonNullable<TradingEvolutionLogEntry["results"]>[number]): number {
  return Number(result.improvementPp ?? result.improvement_pp ?? 0);
}

function resultBatch(result: NonNullable<TradingEvolutionLogEntry["results"]>[number]): number {
  return Number(result.batchNumber ?? result.batch_number ?? 0);
}

function resultSafe(result: NonNullable<TradingEvolutionLogEntry["results"]>[number]): boolean {
  return Boolean(result.conservationSafe ?? result.conservation_safe);
}

export default function EvolutionPanel() {
  const [log, setLog] = useState<TradingEvolutionLogEntry[]>([]);
  const [activeState, setActiveState] = useState<ParameterEvolutionActive | null>(null);
  const [activeVariant, setActiveVariant] = useState<TradingEvolutionLogEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchEvolutionLog(), fetchEvolutionActive(), fetchActiveVariant()])
      .then(([nextLog, nextActive, nextVariant]) => {
        if (cancelled) return;
        setLog(nextLog.filter((entry) => !entry.kind || entry.kind === "variant"));
        setActiveState(nextActive);
        setActiveVariant(nextVariant);
      })
      .catch((loadError) => {
        console.debug("evolution state unavailable", loadError);
        if (!cancelled) setError("Evolution state unavailable.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const active = activeState?.variant ?? activeVariant ?? log.find((entry) => String(entry.status || "").toLowerCase() === "promoted") ?? null;
  const latest = active ?? log[0] ?? null;
  const latestResults = latest?.results ?? [];
  const conservationGreen = latestResults.length === 0 || latestResults.every(resultSafe);
  const status = active ? "Promoted" : latest ? `Evaluating (${latest.batches ?? 0}/3 batches)` : "Pending";
  const adjustments = useMemo(() => Object.entries(latest?.adjustments ?? {}), [latest]);

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold">Agent Evolution</h2>
            <span className={`h-2.5 w-2.5 rounded-full ${conservationGreen ? "bg-emerald-500" : "bg-amber-500"}`} />
          </div>
          <p className="mt-1 text-sm trading-muted">Trading factor-weight variants are shadow tested before promotion.</p>
        </div>
        <ProvenanceBadge source="real_measured" />
      </div>

      {loading ? (
        <p className="mt-4 text-sm trading-muted">Loading evolution state...</p>
      ) : error ? (
        <p className="mt-4 text-sm text-red-500">{error}</p>
      ) : (
        <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_1fr]">
          <article className="rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide trading-muted">Active Variant</p>
                <h3 className="mt-1 text-base font-semibold">{variantId(latest)}</h3>
                <p className="mt-1 text-sm trading-muted">{latest?.description ?? "No variants generated yet."}</p>
              </div>
              <span className="rounded border px-2 py-1 text-xs font-semibold" style={{ borderColor: "var(--copilot-border)" }}>
                {status}
              </span>
            </div>

            <div className="mt-4">
              <p className="text-xs font-semibold uppercase tracking-wide trading-muted">Factor adjustments</p>
              {adjustments.length === 0 ? (
                <p className="mt-2 text-sm trading-muted">No factor adjustments.</p>
              ) : (
                <div className="mt-2 overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="text-left text-xs trading-muted">
                      <tr>
                        <th className="py-2 pr-3">Factor</th>
                        <th className="py-2 pr-3">Baseline</th>
                        <th className="py-2 pr-3">Adjusted</th>
                        <th className="py-2">Multiplier</th>
                      </tr>
                    </thead>
                    <tbody>
                      {adjustments.map(([factor, multiplier]) => (
                        <tr key={factor} className="border-t" style={{ borderColor: "var(--copilot-border)" }}>
                          <td className="py-2 pr-3">{factor.replace(/_/g, " ")}</td>
                          <td className="py-2 pr-3">1.00</td>
                          <td className="py-2 pr-3">{Number(multiplier).toFixed(2)}</td>
                          <td className="py-2">{Number(multiplier).toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="mt-4">
              <p className="text-xs font-semibold uppercase tracking-wide trading-muted">Shadow results</p>
              {latestResults.length === 0 ? (
                <p className="mt-2 text-sm trading-muted">No shadow batches yet.</p>
              ) : (
                <div className="mt-2 overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="text-left text-xs trading-muted">
                      <tr>
                        <th className="py-2 pr-3">Batch</th>
                        <th className="py-2 pr-3">Improvement pp</th>
                        <th className="py-2">Conservation</th>
                      </tr>
                    </thead>
                    <tbody>
                      {latestResults.map((result) => (
                        <tr key={resultBatch(result)} className="border-t" style={{ borderColor: "var(--copilot-border)" }}>
                          <td className="py-2 pr-3">{resultBatch(result)}</td>
                          <td className="py-2 pr-3">{resultImprovement(result).toFixed(1)}</td>
                          <td className="py-2">{resultSafe(result) ? "GREEN" : "PAUSED"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </article>

          <article className="rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide trading-muted">Conservation Guard</p>
                <h3 className="mt-1 text-base font-semibold">{conservationGreen ? "GREEN" : "AMBER"}</h3>
              </div>
              {!conservationGreen ? (
                <span className="rounded bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800">Evolution paused</span>
              ) : null}
            </div>

            <div className="mt-5">
              <p className="text-xs font-semibold uppercase tracking-wide trading-muted">Evolution Log</p>
              {log.length === 0 ? (
                <p className="mt-3 text-sm trading-muted">No variants have been tested.</p>
              ) : (
                <div className="mt-2 overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="text-left text-xs trading-muted">
                      <tr>
                        <th className="py-2 pr-3">Variant</th>
                        <th className="py-2 pr-3">Created</th>
                        <th className="py-2 pr-3">Batches</th>
                        <th className="py-2 pr-3">Avg improvement</th>
                        <th className="py-2">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {log.map((entry) => (
                        <tr key={variantId(entry)} className="border-t" style={{ borderColor: "var(--copilot-border)" }}>
                          <td className="py-2 pr-3 font-mono text-xs">{variantId(entry)}</td>
                          <td className="py-2 pr-3">{createdAt(entry).slice(0, 10) || "n/a"}</td>
                          <td className="py-2 pr-3">{entry.batches ?? 0}</td>
                          <td className="py-2 pr-3">{avgImprovement(entry).toFixed(1)} pp</td>
                          <td className="py-2">{entry.status ?? "pending"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </article>
        </div>
      )}
    </section>
  );
}
