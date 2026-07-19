import { useEffect, useMemo, useState } from "react";
import {
  executeTransfer,
  fetchTransferOpportunities,
  fetchTransferStatus,
  type TransferExecuteResponse,
  type TransferMappingSummary,
  type TransferOpportunitiesResponse,
  type TransferStatusResponse,
} from "../api";
import TransferComparisonCard from "./TransferComparisonCard";

function label(value?: string): string {
  return String(value || "unknown").replace(/_/g, " ");
}

export default function TransferPanel() {
  const [cachedStatus, setCachedStatus] = useState<TransferStatusResponse | null>(null);
  const [opportunities, setOpportunities] = useState<TransferOpportunitiesResponse | null>(null);
  const [selected, setSelected] = useState<TransferMappingSummary | null>(null);
  const [dryRun, setDryRun] = useState(true);
  const [result, setResult] = useState<TransferExecuteResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([fetchTransferOpportunities(), fetchTransferStatus()])
      .then(([nextOpportunities, nextStatus]) => {
        if (cancelled) return;
        setOpportunities(nextOpportunities);
        setCachedStatus(nextStatus);
        const transfers = nextOpportunities.availableTransfers || [];
        setSelected(transfers.find((item) => item.target === "trading") || transfers[0] || null);
      })
      .catch((loadError) => {
        console.debug("TransferPanel fetch failed", loadError);
        if (!cancelled) setError(loadError instanceof Error ? loadError.message : "Transfer data unavailable");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const transfers = useMemo(() => opportunities?.availableTransfers || [], [opportunities]);

  async function runTransfer() {
    if (!selected?.source || !selected?.target) return;
    if (selected.target !== "trading") {
      setError("This panel can apply transfers only to trading.");
      return;
    }
    setExecuting(true);
    setError(null);
    try {
      setResult(await executeTransfer(selected.source, selected.target, dryRun));
    } catch (executeError) {
      console.debug("TransferPanel execute failed", executeError);
      setError(executeError instanceof Error ? executeError.message : "Transfer failed");
    } finally {
      setExecuting(false);
    }
  }

  if (loading) {
    return <section className="copilot-card p-4 text-sm trading-muted">Loading transfer opportunities...</section>;
  }

  return (
    <section className="copilot-card p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">Cross-Copilot Transfer</h2>
          <p className="mt-1 text-sm trading-muted">Warm-start candidate patterns from compatible copilots.</p>
        </div>
        <div className="rounded-full border px-3 py-1 text-xs" style={{ borderColor: "var(--copilot-border)" }}>
          {cachedStatus?.warmStarted ? `Warm-started from ${label(cachedStatus.sourceCopilot)}` : "No active transfer"}
        </div>
      </div>

      {error ? <p className="mt-3 text-sm text-red-300">{error}</p> : null}

      {transfers.length === 0 ? (
        <p className="mt-4 text-sm trading-muted">No transfer mappings are available.</p>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="trading-muted">
              <tr>
                <th className="py-2 pr-3">Source</th>
                <th className="py-2 pr-3">Target</th>
                <th className="py-2 pr-3">Categories</th>
                <th className="py-2 pr-3">Select</th>
              </tr>
            </thead>
            <tbody>
              {transfers.map((item) => {
                const active = selected?.source === item.source && selected?.target === item.target;
                const appliesHere = item.target === "trading";
                return (
                  <tr
                    key={`${item.source}-${item.target}`}
                    className="border-t"
                    style={{ borderColor: "var(--copilot-border)", opacity: appliesHere ? 1 : 0.5 }}
                  >
                    <td className="py-2 pr-3">{label(item.source)}</td>
                    <td className="py-2 pr-3">{label(item.target)}</td>
                    <td className="py-2 pr-3">{item.categories ?? 0}</td>
                    <td className="py-2 pr-3">
                      <button
                        type="button"
                        className="copilot-button px-3 py-1 text-xs"
                        disabled={!appliesHere}
                        onClick={() => setSelected(item)}
                      >
                        {appliesHere ? (active ? "Selected" : "Use") : "N/A"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={dryRun} onChange={(event) => setDryRun(event.target.checked)} />
          Dry run
        </label>
        <button
          type="button"
          className="copilot-button px-4 py-2 text-sm"
          disabled={!selected || selected.target !== "trading" || executing}
          onClick={runTransfer}
        >
          {executing ? "Running..." : "Execute Transfer"}
        </button>
      </div>

      {result ? (
        <div className="mt-4 rounded-md border p-3 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="font-semibold">Transfer result</div>
          <div className="mt-2 grid gap-2 sm:grid-cols-3">
            <Fact label="Mode" value={result.dryRun ? "Dry run" : "Apply"} />
            <Fact label="Mapped" value={String(result.categoriesMapped ?? 0)} />
            <Fact label="Conservation reset" value={result.conservationReset ? "Yes" : "No"} />
          </div>
          {result.reason ? <p className="mt-2 trading-muted">{result.reason}</p> : null}
        </div>
      ) : null}

      <TransferComparisonCard />
    </section>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs trading-muted">{label}</div>
      <div className="font-semibold">{value}</div>
    </div>
  );
}
