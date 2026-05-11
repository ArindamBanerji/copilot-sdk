import { useEffect, useState } from "react";
import { getSchemaImpact } from "../api";
import type { SchemaChange, SchemaImpactResponse } from "../types";

const SYSTEMS = ["warehouse_etl", "billing_api", "payment_gateway", "crm_sync"];

export default function SchemaImpactPanel() {
  const [system, setSystem] = useState("warehouse_etl");
  const [data, setData] = useState<SchemaImpactResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getSchemaImpact(system)
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Could not load schema impact.");
          setData(null);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [system]);

  const changes = data?.schemaChanges || [];

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            OE-3
          </p>
          <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
            Schema Impact: {humanize(system)}
          </h2>
          <p className="mt-1 text-sm dataops-muted">
            {loading
              ? "Tracing downstream schema impact..."
              : `${data?.totalChanges ?? 0} changes · ${data?.totalImpacts ?? 0} downstream impacts · ${data?.totalAlertsPreventable ?? 0} alerts preventable`}
          </p>
        </div>
        <label className="grid gap-1 text-xs font-semibold dataops-muted">
          System
          <select
            className="rounded-md border px-2 py-2 text-sm"
            style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)", color: "var(--copilot-text)" }}
            value={system}
            onChange={(event) => setSystem(event.target.value)}
          >
            {SYSTEMS.map((option) => (
              <option key={option} value={option}>
                {humanize(option)}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error ? <p className="mt-4 text-sm" style={{ color: "var(--copilot-danger)" }}>{error}</p> : null}
      {!loading && !error && changes.length === 0 ? <p className="mt-4 text-sm dataops-muted">No schema changes detected for this system.</p> : null}

      {!error && changes.length > 0 ? (
        <div className="mt-5 grid gap-3">
          {changes.map((change) => (
            <SchemaChangeCard key={`${change.sourceTable || "source"}-${change.column || "column"}`} change={change} />
          ))}
        </div>
      ) : null}
    </section>
  );
}

function SchemaChangeCard({ change }: { change: SchemaChange }) {
  const impactedSystems = change.impactedSystems || [];
  return (
    <article className="rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold" style={{ color: "var(--copilot-text)" }}>
            {change.sourceTable || "Source"}.{change.column || "column"}
          </h3>
          <p className="mt-1 text-sm dataops-muted">
            {humanize(change.changeType || "schema change")} · {change.detected || "date unavailable"}
          </p>
        </div>
        <span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: "var(--copilot-primary-light)", color: "var(--copilot-primary)" }}>
          {change.alertsPrevented ?? 0} alerts prevented
        </span>
      </div>

      <div className="mt-3 grid gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs font-semibold uppercase dataops-muted">Downstream impact</div>
          <div className="mt-2 flex flex-wrap gap-2">
            {impactedSystems.length ? (
              impactedSystems.map((system) => (
                <span key={system} className="rounded-full px-2 py-1 text-xs" style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-text)" }}>
                  {humanize(system)}
                </span>
              ))
            ) : (
              <span className="text-sm dataops-muted">{change.downstreamImpact ?? 0} impacted systems</span>
            )}
          </div>
        </div>
        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs font-semibold uppercase dataops-muted">Proposed fix</div>
          <p className="mt-2 text-sm dataops-muted">{change.proposedFix || "No proposed fix available."}</p>
        </div>
      </div>
    </article>
  );
}

function humanize(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
