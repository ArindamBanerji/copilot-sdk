import { useEffect, useState } from "react";
import { fetchS2PRules } from "../api";
import type { RuleLifecycleResponse } from "../types";

const stateClasses: Record<string, string> = {
  promoted: "border-emerald-200 bg-emerald-50 text-emerald-800",
  shadow: "border-blue-200 bg-blue-50 text-blue-800",
  proposed: "border-amber-200 bg-amber-50 text-amber-800",
  rejected: "border-rose-200 bg-rose-50 text-rose-800",
};

export function RuleLifecyclePanel() {
  const [data, setData] = useState<RuleLifecycleResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchS2PRules().then((response) => {
      if (!cancelled) setData(response);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const rules = data?.rules ?? [];

  return (
    <article className="copilot-card p-5">
      <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Rule lifecycle</p>
      <h2 className="mt-1 text-xl font-semibold text-slate-950">Seeded procurement controls</h2>
      {rules.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">No rule lifecycle data available.</p>
      ) : (
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {rules.map((rule) => (
            <div key={rule.rule_id ?? rule.ruleId} className="rounded-md border border-slate-200 bg-white p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <h3 className="text-sm font-semibold text-slate-950">{rule.name}</h3>
                <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${stateClasses[rule.state] ?? "border-slate-200 bg-slate-50 text-slate-700"}`}>
                  {rule.state}
                </span>
              </div>
              <p className="mt-2 text-xs text-slate-500">{rule.rule_id ?? rule.ruleId}</p>
              <p className="mt-3 text-sm text-slate-600">
                {rule.factor?.replace(/_/g, " ")} · {rule.action?.replace(/_/g, " ")}
              </p>
            </div>
          ))}
        </div>
      )}
      {data?.note ? <p className="mt-4 text-xs font-medium text-slate-500">{data.note}</p> : null}
    </article>
  );
}
