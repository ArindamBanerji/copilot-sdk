import { useEffect, useState } from "react";
import { executeChainTransfer, fetchChainStatus, validateChainTransfer, type ChainStatusResponse } from "../api";
import ProvenanceBadge from "./ProvenanceBadge";

function pct(value?: number) {
  return Number.isFinite(value) ? `${Math.round(Number(value) * 100)}%` : "n/a";
}

export default function ChainTransferCard() {
  const [status, setStatus] = useState<ChainStatusResponse | null>(null);
  const [message, setMessage] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setStatus(await fetchChainStatus());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No chain locations configured");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function preview() {
    const result = await validateChainTransfer();
    setMessage(result.valid ? "Ready to preview transfer." : String((result.reasons as string[] | undefined)?.[0] ?? "Review before transfer."));
  }

  async function dryRun() {
    const result = await executeChainTransfer("chicago", "miami", true);
    setMessage(result.transferred ? "Dry run complete. Miami can start from Chicago patterns." : "Transfer is not ready yet.");
  }

  return (
    <section className="purchase-card">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Chain Learning</p>
          <h2 className="purchase-title">Chicago lessons help Miami on day one</h2>
        </div>
        <ProvenanceBadge source={status?.provenance === "demo" ? "sample" : status?.provenance} />
      </div>
      {loading ? <p className="purchase-muted">Checking chain locations...</p> : null}
      {error ? <p className="purchase-muted">{error}</p> : null}
      {status ? (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <div className="rounded-md border p-3" style={{ borderColor: "var(--purchase-border)" }}>
              <div className="purchase-muted text-sm">Source location</div>
              <strong>{status.source?.location ?? "Chicago"}</strong>
              <p className="purchase-muted text-sm">{status.source?.decisions ?? 500} decisions, {pct(status.source?.accuracy)} accuracy</p>
            </div>
            <div className="rounded-md border p-3" style={{ borderColor: "var(--purchase-border)" }}>
              <div className="purchase-muted text-sm">Target location</div>
              <strong>{status.target?.location ?? "Miami"}</strong>
              <p className="purchase-muted text-sm">new opening, {status.target?.decisions ?? 0} decisions</p>
            </div>
            <div className="rounded-md border p-3" style={{ borderColor: "var(--purchase-border)" }}>
              <div className="purchase-muted text-sm">Estimated day-one accuracy</div>
              <strong>{pct(status.estimatedAccuracy)}</strong>
              <p className="purchase-muted text-sm">Saved about 3 weeks calibration</p>
            </div>
          </div>
          <p className="purchase-muted mt-3">
            Miami starts with Chicago patterns but must verify them locally. Auto-approve becomes safe when learning is GREEN.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button className="purchase-button secondary" type="button" onClick={() => void preview()}>Validate</button>
            <button className="purchase-button" type="button" onClick={() => void dryRun()}>Dry run transfer</button>
          </div>
          {message ? <p className="purchase-muted mt-2">{message}</p> : null}
        </>
      ) : null}
    </section>
  );
}
