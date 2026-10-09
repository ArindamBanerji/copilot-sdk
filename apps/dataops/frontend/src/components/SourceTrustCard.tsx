import { Fragment, useEffect, useState } from "react";
import { fetchSourceTrust, type SourceTrustRow } from "../api";

const statusColors = { GREEN: "#35b779", AMBER: "#e5a93d", RED: "#d95d6a" };
const trendArrows = { improving: "↑", stable: "→", declining: "↓" };

function displayName(value: string): string {
  return value.replace(/([a-z])([A-Z])/g, "$1 $2").replace(/_/g, " ");
}

export default function SourceTrustCard() {
  const [rows, setRows] = useState<SourceTrustRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchSourceTrust().then((data) => {
      if (!cancelled) setRows(data);
    }).catch(() => {
      if (!cancelled) setError("Source trust is unavailable. Please try again.");
    }).finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, [refresh]);

  const verified = rows[0]?.totalVerified ?? 0;
  return (
    <section className="copilot-card p-5" data-testid="source-trust-card">
      <div className="flex items-center justify-between gap-3">
        <h2 className="dataops-section-title" style={{ color: "#9b7cff" }}>Source Trust</h2>
        <button type="button" className="copilot-button-secondary px-3 py-1 text-xs"
          disabled={loading} onClick={() => setRefresh((value) => value + 1)}>Refresh</button>
      </div>
      <p className="mt-2 text-xs dataops-muted">
        Relative factor trust, not a reliability probability. Unmapped pipelines remain neutral at 50%.
      </p>
      {loading ? <p role="status" className="mt-4 text-sm dataops-muted">Loading source trust…</p>
        : error ? <p role="alert" className="mt-4 text-sm" style={{ color: "var(--copilot-danger)" }}>{error}</p>
        : rows.length === 0 ? <p className="mt-4 text-sm dataops-muted">No source trust data available.</p>
        : <>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs dataops-muted"><tr>
                <th className="pb-3">Source</th><th className="pb-3">Trust</th>
                <th className="pb-3 pl-4">Status</th><th className="pb-3 pl-4">Trend</th>
              </tr></thead>
              <tbody>{rows.map((row) => {
                const open = expanded === row.source;
                const factors = Object.entries(row.dkContribution);
                return <Fragment key={row.source}>
                  <tr className="cursor-pointer border-t" style={{ borderColor: "var(--copilot-border)" }}
                    onClick={() => setExpanded(open ? null : row.source)}>
                    <td className="py-3 pr-4">
                      <button type="button" className="text-left capitalize" aria-expanded={open}
                        aria-controls={`source-trust-${row.source}`}
                        onClick={(event) => { event.stopPropagation(); setExpanded(open ? null : row.source); }}>
                        <span aria-hidden="true" className="mr-2">{open ? "▾" : "▸"}</span>{displayName(row.source)}
                      </button>
                      {factors.length === 0 && <span className="ml-2 text-xs dataops-muted">Neutral</span>}
                    </td>
                    <td className="min-w-32 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-24 overflow-hidden rounded-full" style={{ background: "var(--copilot-border)" }}
                          role="meter" aria-label={`${displayName(row.source)} relative trust`}
                          aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(row.trust * 100)}>
                          <div className="h-full rounded-full" style={{ width: `${row.trust * 100}%`, background: "#9b7cff" }} />
                        </div>
                        <span className="text-xs tabular-nums">{Math.round(row.trust * 100)}%</span>
                      </div>
                    </td>
                    <td className="py-3 pl-4"><span className="rounded-full border px-2 py-1 text-xs"
                      style={{ color: statusColors[row.status], borderColor: statusColors[row.status] }}>{row.status}</span></td>
                    <td className="py-3 pl-4 whitespace-nowrap" title="Trend in factor fingerprint history">
                      <span aria-hidden="true">{trendArrows[row.trend]}</span> <span className="text-xs capitalize">{row.trend}</span>
                    </td>
                  </tr>
                  {open && <tr id={`source-trust-${row.source}`}><td colSpan={4} className="pb-4 pl-6">
                    {factors.length ? <dl className="grid gap-1 text-xs">
                      {factors.map(([factor, value]) => <div key={factor} className="flex gap-4">
                        <dt className="capitalize dataops-muted">{displayName(factor)}</dt>
                        <dd>{(value * 100).toFixed(1)}% relative DK contribution</dd>
                      </div>)}
                    </dl> : <p className="text-xs dataops-muted">No mapped learned weights available. 50% is a neutral default.</p>}
                    <p className="mt-2 text-xs dataops-muted">{row.verified.toLocaleString()} verified decisions involving this source.</p>
                  </td></tr>}
                </Fragment>;
              })}</tbody>
            </table>
          </div>
          <footer className="mt-4 border-t pt-3 text-xs dataops-muted" style={{ borderColor: "var(--copilot-border)" }}>
            Trust scores from {verified.toLocaleString()} verified decisions · {rows[0].provenance}
            <p className="mt-1">Trends compare factor fingerprints; stable also applies when prior evidence is unavailable.</p>
          </footer>
        </>}
    </section>
  );
}
