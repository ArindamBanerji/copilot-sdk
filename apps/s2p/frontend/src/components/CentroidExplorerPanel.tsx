import { useEffect, useState } from "react";
import { getDKWeights, getDrift } from "../api";
import { S2P_CATEGORIES } from "../types";
import type { DKWeightsResponse, DriftResponse } from "../types";

function label(value: string): string {
  return value.replace(/_/g, " ");
}

function percent(value?: number): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "n/a";
}

export function CentroidExplorerPanel() {
  const [category, setCategory] = useState<string>(S2P_CATEGORIES[0]);
  const [drift, setDrift] = useState<DriftResponse | null>(null);
  const [dk, setDk] = useState<DKWeightsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    Promise.all([getDrift(category), getDKWeights()])
      .then(([driftResponse, dkResponse]) => {
        if (cancelled) return;
        if (!driftResponse) {
          setError("Centroid explorer is unavailable.");
          setDrift(null);
          setDk(dkResponse);
          return;
        }
        setDrift(driftResponse);
        setDk(dkResponse);
      })
      .catch(() => {
        if (!cancelled) {
          setError("Centroid explorer is unavailable.");
          setDrift(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [category]);

  const factors = drift?.factors ?? dk?.factors ?? [];
  const centroidRows = Object.entries(drift?.centroids ?? {});

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Centroid evidence</p>
          <h2 className="mt-1 text-xl font-semibold text-slate-950">Centroid Explorer</h2>
        </div>
        <label className="text-sm font-medium text-slate-700">
          Category
          <select
            value={category}
            onChange={(event) => setCategory(event.target.value)}
            className="mt-2 block min-w-56 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
          >
            {S2P_CATEGORIES.map((item) => (
              <option key={item} value={item}>
                {label(item)}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loading ? <p className="mt-4 text-sm text-slate-500">Loading centroids...</p> : null}
      {error ? <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}

      {!loading && !error && drift ? (
        <>
          <section className="mt-4 rounded-md border border-slate-200 bg-white p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Factor weights</p>
                <p className="mt-1 text-sm text-slate-600">
                  {dk?.available ? "DK weights are available for this scorer." : "DK weights unavailable from backend."}
                </p>
              </div>
            </div>
            {factors.length > 0 ? (
              <div className="mt-3 grid gap-2 md:grid-cols-2">
                {factors.map((factor, index) => {
                  const value = dk?.available ? dk.weights[index] : undefined;
                  return (
                    <div key={factor} className="rounded-md bg-slate-50 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-xs font-semibold capitalize text-slate-700">{label(factor)}</span>
                        <span className="text-xs text-slate-500">{typeof value === "number" ? percent(value) : "n/a"}</span>
                      </div>
                      <div className="mt-2 h-2 rounded-full bg-slate-200">
                        <div
                          className="h-2 rounded-full bg-teal-600"
                          style={{ width: `${typeof value === "number" ? Math.min(Math.max(value * 100, 0), 100) : 0}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="mt-3 text-sm text-slate-500">No factor metadata is available.</p>
            )}
          </section>

          {centroidRows.length > 0 ? (
            <div className="mt-4 space-y-3">
              {centroidRows.map(([action, values]) => (
                <section key={action} className="rounded-md border border-slate-200 bg-white p-4">
                  <h3 className="text-sm font-semibold capitalize text-slate-900">{label(action)}</h3>
                  <div className="mt-3 grid gap-2">
                    {factors.map((factor, index) => {
                      const value = values[index];
                      return (
                        <div key={`${action}-${factor}`}>
                          <div className="flex items-center justify-between gap-3">
                            <span className="text-xs capitalize text-slate-600">{label(factor)}</span>
                            <span className="text-xs font-semibold text-slate-700">{percent(value)}</span>
                          </div>
                          <div className="mt-1 h-2 rounded-full bg-slate-100">
                            <div
                              className="h-2 rounded-full bg-amber-500"
                              style={{ width: `${typeof value === "number" ? Math.min(Math.max(value * 100, 0), 100) : 0}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </section>
              ))}
            </div>
          ) : (
            <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-500">
              No centroid rows are available for this category.
            </p>
          )}
        </>
      ) : null}
    </article>
  );
}
