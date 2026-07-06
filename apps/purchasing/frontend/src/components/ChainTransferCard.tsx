import { useEffect, useState } from "react";
import { executeChainTransfer, fetchChainStatus, validateChainTransfer, type ChainStatusResponse } from "../api";
import ProvenanceBadge from "./ProvenanceBadge";

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8020";

type DemoTransferResult = {
  before?: Record<string, { iks?: number }>;
  after?: Record<string, { iks?: number }>;
  narrative?: string;
  transferred?: { dk_weights?: number; patterns?: string[] };
};

export default function ChainTransferCard() {
  const [status, setStatus] = useState<ChainStatusResponse | null>(null);
  const [message, setMessage] = useState<string>("");
  const [demoResult, setDemoResult] = useState<DemoTransferResult | null>(null);
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

  async function transferNow() {
    setMessage("");
    setDemoResult(null);
    await fetch(`${BASE}/api/purchasing/demo/chain-seed`, { method: "POST" });
    const response = await fetch(`${BASE}/api/purchasing/chain/transfer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_location: "downtown",
        target_locations: ["airport", "suburb", "new"],
      }),
    });
    if (!response.ok) {
      setMessage("Transfer is not ready yet.");
      return;
    }
    const result = await response.json();
    setDemoResult(result);
    setMessage(result.narrative ?? "Downtown's purchasing discipline transferred.");
  }

  return (
    <section className="purchase-card">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Chain Learning</p>
          <h2 className="purchase-title">Downtown discipline becomes the baseline for all four</h2>
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
              <strong>Downtown</strong>
              <p className="purchase-muted text-sm">200 decisions, 58 IKS, GREEN learning</p>
            </div>
            <div className="rounded-md border p-3" style={{ borderColor: "var(--purchase-border)" }}>
              <div className="purchase-muted text-sm">Target locations</div>
              <strong>Airport, Suburb, New</strong>
              <p className="purchase-muted text-sm">AMBER or RED locations get the baseline</p>
            </div>
            <div className="rounded-md border p-3" style={{ borderColor: "var(--purchase-border)" }}>
              <div className="purchase-muted text-sm">What transfers</div>
              <strong>Trust weights and patterns</strong>
              <p className="purchase-muted text-sm">Downtown's buying habits seed the weaker locations</p>
            </div>
          </div>
          <p className="purchase-muted mt-3">
            Airport, Suburb, and New start from Downtown patterns but must verify them locally. Auto-approve becomes safe when learning is GREEN.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button className="purchase-button secondary" type="button" onClick={() => void preview()}>Validate</button>
            <button className="purchase-button" type="button" onClick={() => void dryRun()}>Dry run transfer</button>
            <button className="purchase-button" type="button" onClick={() => void transferNow()}>Transfer Now</button>
          </div>
          {message ? <p className="purchase-muted mt-2">{message}</p> : null}
          {demoResult ? (
            <div className="mt-3 grid gap-2 md:grid-cols-3">
              {["airport", "suburb", "new"].map((location) => (
                <div key={location} className="rounded-md border p-3" style={{ borderColor: "var(--purchase-border)" }}>
                  <div className="purchase-muted text-sm">{location[0].toUpperCase() + location.slice(1)}</div>
                  <strong>
                    IKS {demoResult.before?.[location]?.iks ?? "-"} -&gt; {demoResult.after?.[location]?.iks ?? "-"}
                  </strong>
                </div>
              ))}
              <p className="purchase-muted text-sm md:col-span-3">
                Moved {demoResult.transferred?.dk_weights ?? 0} trust weights and {demoResult.transferred?.patterns?.length ?? 0} buying patterns.
              </p>
            </div>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
