import { useEffect, useMemo, useState } from "react";
import { getCentroidDrift, getCentroidExplanation } from "../api";
import type { CentroidExplanation, DriftResponse, ProvenanceDisplayValue } from "../types";
import { FactorRadar } from "./FactorRadar";

function label(value?: string): string {
  return value ? value.replace(/_/g, " ") : "n/a";
}

function numeric(value: number): string {
  return Number.isFinite(value) ? value.toFixed(3) : "n/a";
}

function boolLabel(value?: boolean): string {
  return value ? "yes" : "no";
}

function evidenceLabel(metric: ProvenanceDisplayValue): string {
  return metric.provenance_label || metric.provenance_tier || metric.source || "provenance unavailable";
}

export function CentroidExplorer({ decisionId }: { decisionId?: string }) {
  const [explanation, setExplanation] = useState<CentroidExplanation | null>(null);
  const [drift, setDrift] = useState<DriftResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!decisionId) {
      setExplanation(null);
      setDrift(null);
      setError("");
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError("");
    setDrift(null);

    getCentroidExplanation(decisionId)
      .then((response) => {
        if (cancelled) return;
        if (!response) {
          setExplanation(null);
          setError("Centroid explanation is unavailable for this decision.");
          return;
        }
        setExplanation(response);
        void getCentroidDrift(response.category, response.closest_action).then((driftResponse) => {
          if (!cancelled) setDrift(driftResponse);
        });
      })
      .catch(() => {
        if (!cancelled) {
          setExplanation(null);
          setError("Centroid explanation is unavailable for this decision.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [decisionId]);

  const distances = useMemo(() => {
    return Object.entries(explanation?.centroid_distances ?? {}).sort((left, right) => left[1] - right[1]);
  }, [explanation]);

  const evidence = Object.entries(explanation?.p39_evidence ?? {});

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Centroid explorer</p>
          <h2 className="mt-1 text-xl font-semibold text-slate-950">Decision proximity explanation</h2>
          <p className="mt-2 max-w-3xl text-sm text-slate-600">
            Read-only centroid comparison for the stored scored factor vector. This is explanatory context, not causal
            proof and not a replacement for the scorer recommendation.
          </p>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
          read-only
        </span>
      </div>

      {!decisionId ? (
        <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-500">
          Select or score a decision to view centroid explanation.
        </p>
      ) : null}
      {loading ? <p className="mt-4 text-sm text-slate-500">Loading centroid explanation...</p> : null}
      {error ? <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}

      {!loading && explanation ? (
        <div className="mt-5 space-y-4">
          <section className="rounded-md border border-slate-200 bg-white p-4">
            <div className="grid gap-3 md:grid-cols-4">
              <Metric label="Decision" value={explanation.decision_id} />
              <Metric label="Recommended" value={label(explanation.recommended_action)} />
              <Metric label="Closest centroid" value={label(explanation.closest_action)} />
              <Metric label="DK status" value={label(explanation.dk_status)} />
            </div>
            {!explanation.closest_matches_recommendation ? (
              <p className="mt-3 rounded-md bg-amber-50 p-3 text-sm text-amber-800">
                Centroid proximity is explanatory context and does not replace the scorer recommendation.
              </p>
            ) : null}
            <p className="mt-3 text-sm text-slate-600">{explanation.summary}</p>
            {explanation.dk_status !== "available" ? (
              <p className="mt-2 text-xs text-slate-500">
                Trust weights are learning or unavailable; factor ordering uses a uniform display fallback.
              </p>
            ) : null}
          </section>

          <FactorRadar
            factors={explanation.factor_contributions}
            dkStatus={explanation.dk_status}
            closestAction={explanation.closest_action}
            recommendedAction={explanation.recommended_action}
          />

          <section className="rounded-md border border-slate-200 bg-white p-4">
            <h3 className="text-base font-semibold text-slate-950">Action distance table</h3>
            <div className="mt-3 overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead>
                  <tr className="text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <th className="py-2 pr-4">Action</th>
                    <th className="py-2 pr-4">Total L2 distance</th>
                    <th className="py-2 pr-4">Closest</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {distances.map(([action, distance]) => (
                    <tr key={action} className={action === explanation.closest_action ? "bg-amber-50" : undefined}>
                      <td className="py-2 pr-4 font-medium capitalize text-slate-800">{label(action)}</td>
                      <td className="py-2 pr-4 text-slate-600">{numeric(distance)}</td>
                      <td className="py-2 pr-4 text-slate-600">{boolLabel(action === explanation.closest_action)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="rounded-md border border-slate-200 bg-white p-4">
            <h3 className="text-base font-semibold text-slate-950">P39 supplier evidence</h3>
            {evidence.length === 0 ? (
              <p className="mt-3 text-sm text-slate-500">No persisted supplier enrichment was returned for this decision.</p>
            ) : (
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                {evidence.map(([name, metric]) => (
                  <div key={name} className="rounded-md bg-slate-50 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <span className="text-sm font-semibold capitalize text-slate-800">{label(name)}</span>
                      <span className="rounded-full bg-white px-2 py-1 text-xs font-semibold text-slate-600">
                        {metric.source ?? "source unavailable"}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-600">{String(metric.value ?? "n/a")}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      {evidenceLabel(metric)} · measured {boolLabel(metric.measured)} · verified {boolLabel(metric.verified)}
                    </p>
                  </div>
                ))}
              </div>
            )}
            <p className="mt-3 text-xs text-slate-500">
              Supplier enrichment is displayed as provenance context only and is not used in centroid distances.
            </p>
          </section>

          <section className="rounded-md border border-slate-200 bg-white p-4">
            <h3 className="text-base font-semibold text-slate-950">Centroid drift</h3>
            {!drift ? (
              <p className="mt-3 text-sm text-slate-500">Checking centroid history...</p>
            ) : drift.supported && drift.points.length > 0 ? (
              <div className="mt-3 overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-sm">
                  <thead>
                    <tr className="text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                      <th className="py-2 pr-4">Timestamp</th>
                      <th className="py-2 pr-4">Verified count</th>
                      <th className="py-2 pr-4">Distance from previous</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {drift.points.map((point, index) => (
                      <tr key={`${point.timestamp ?? "checkpoint"}-${index}`}>
                        <td className="py-2 pr-4 text-slate-700">{point.timestamp ?? "n/a"}</td>
                        <td className="py-2 pr-4 text-slate-600">{point.verified_count ?? "n/a"}</td>
                        <td className="py-2 pr-4 text-slate-600">
                          {typeof point.distance_from_previous === "number"
                            ? numeric(point.distance_from_previous)
                            : "n/a"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="mt-3 rounded-md bg-slate-50 p-3 text-sm text-slate-500">
                Centroid history unavailable: {drift.reason || "unsupported by current backend state"}.
              </p>
            )}
          </section>
        </div>
      ) : null}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 break-words text-sm font-semibold capitalize text-slate-950">{value}</p>
    </div>
  );
}
