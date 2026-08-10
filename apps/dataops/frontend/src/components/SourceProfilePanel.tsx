import { useEffect, useState } from "react";
import { fetchDIProfiles, fetchDISourceConsumers, fetchDISourceTrust } from "../api";
import type {
  DIProfilesResponse,
  DISourceConsumersResponse,
  DISourceSummary,
  DISourceTrustResponse,
} from "../types";

interface SourceDetail {
  trust: DISourceTrustResponse | null;
  consumers: DISourceConsumersResponse | null;
}

function sourceId(source: DISourceSummary): string {
  return source.sourceName || source.source_name || "unknown-source";
}

function trustTone(score: number) {
  if (score >= 0.8) {
    return "bg-emerald-400";
  }
  if (score >= 0.5) {
    return "bg-amber-400";
  }
  return "bg-red-400";
}

function trustLabel(score: number, label?: string) {
  return label || (score >= 0.8 ? "reliable" : score >= 0.5 ? "moderate" : "noisy");
}

function TrustBar({ score }: { score: number }) {
  const bounded = Math.max(0, Math.min(score, 1));
  return (
    <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-700/50" aria-label={`Trust ${Math.round(bounded * 100)}%`}>
      <div className={`h-full ${trustTone(bounded)}`} style={{ width: `${bounded * 100}%` }} />
    </div>
  );
}

function SourceDetails({ detail }: { detail: SourceDetail }) {
  const trust = detail.trust;
  const consumers = detail.consumers?.consumers || [];
  const score = trust?.trustScore ?? 0;
  return (
    <div className="mt-4 grid gap-4 border-t border-white/10 pt-4">
      <div>
        <h4 className="text-xs font-semibold uppercase tracking-[0.16em] text-purple-200/75">Column trust</h4>
        {trust?.columns?.length ? (
          <div className="mt-2 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase dataops-muted">
                <tr><th className="pb-2">Column</th><th className="pb-2">Trust</th><th className="pb-2">Label</th></tr>
              </thead>
              <tbody>
                {trust.columns.map((column) => (
                  <tr key={column.name} className="border-t border-white/5">
                    <td className="py-2">{column.name || "unknown"}</td>
                    <td className="py-2">{Math.round((column.trust ?? 0) * 100)}%</td>
                    <td className="py-2 dataops-muted">{column.label || "unclassified"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <p className="mt-2 text-sm dataops-muted">No column trust data available.</p>}
      </div>
      <div>
        <h4 className="text-xs font-semibold uppercase tracking-[0.16em] text-purple-200/75">Consumers</h4>
        {consumers.length ? (
          <div className="mt-2 grid gap-2">
            {consumers.map((consumer) => (
              <div key={consumer.consumerId} className="rounded-md border border-white/10 px-3 py-2 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-semibold">{consumer.consumerId || "consumer"}</span>
                  <span className="text-purple-200">{Math.round((consumer.satisfactionRate ?? 0) * 100)}%</span>
                </div>
                {consumer.lastIssue ? <p className="mt-1 text-xs dataops-muted">Last issue: {consumer.lastIssue}</p> : null}
              </div>
            ))}
          </div>
        ) : <p className="mt-2 text-sm dataops-muted">No consumers reported.</p>}
      </div>
      <p className={`text-sm font-semibold ${score >= 0.8 ? "text-emerald-300" : "text-amber-300"}`}>
        {score >= 0.8 ? "Recommendation: Safe for autonomous agent consumption" : "Recommendation: Require human review"}
      </p>
    </div>
  );
}

export default function SourceProfilePanel() {
  const [profiles, setProfiles] = useState<DIProfilesResponse | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [details, setDetails] = useState<Record<string, SourceDetail>>({});
  const [loadingDetails, setLoadingDetails] = useState<Record<string, boolean>>({});

  useEffect(() => {
    let cancelled = false;
    fetchDIProfiles().then((payload) => {
      if (!cancelled) {
        setProfiles(payload);
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  async function toggleSource(id: string) {
    if (expanded === id) {
      setExpanded(null);
      return;
    }
    setExpanded(id);
    if (details[id] || loadingDetails[id]) {
      return;
    }
    setLoadingDetails((current) => ({ ...current, [id]: true }));
    const [trust, consumers] = await Promise.all([fetchDISourceTrust(id), fetchDISourceConsumers(id)]);
    setDetails((current) => ({ ...current, [id]: { trust, consumers } }));
    setLoadingDetails((current) => ({ ...current, [id]: false }));
  }

  const sources = profiles?.sources || [];
  return (
    <section data-testid="source-profile-panel" className="copilot-card p-5">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-purple-200/75">Source Profiler</p>
        <h2 className="mt-1 text-xl font-semibold text-white">Data Source Trust</h2>
        <p className="mt-1 text-sm dataops-muted">Expand a source to inspect column trust and consumer quality.</p>
      </div>
      <div className="mt-4 grid gap-3">
        {!sources.length ? <p className="text-sm dataops-muted">No profiled sources available.</p> : null}
        {sources.map((source) => {
          const id = sourceId(source);
          const detail = details[id];
          const score = detail?.trust?.trustScore ?? source.latestProfile?.overallQuality ?? 0;
          return (
            <article key={id} data-testid="source-profile" className="rounded-md border border-purple-300/20 bg-purple-500/[0.03] p-4">
              <button
                type="button"
                className="w-full text-left"
                aria-expanded={expanded === id}
                data-testid={`source-profile-toggle-${id}`}
                onClick={() => void toggleSource(id)}
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <h3 className="font-semibold text-white">{id}</h3>
                    <p className="mt-1 text-xs dataops-muted">{source.entityType || source.entity_type || "source"}</p>
                  </div>
                  <span className="text-sm font-semibold text-purple-200">{Math.round(score * 100)}%</span>
                </div>
                <TrustBar score={score} />
                <div className="mt-2 flex items-center justify-between text-xs dataops-muted">
                  <span>{trustLabel(score, detail?.trust?.trustLabel)}</span>
                  <span>{expanded === id ? "Collapse" : "Inspect details"}</span>
                </div>
              </button>
              {expanded === id ? (
                loadingDetails[id] ? <p className="mt-4 border-t border-white/10 pt-4 text-sm dataops-muted">Loading source details...</p> : detail ? <SourceDetails detail={detail} /> : null
              ) : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}
