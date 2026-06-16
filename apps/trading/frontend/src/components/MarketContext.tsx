import ProvenanceBadge from "./ProvenanceBadge";
import type { MarketSnapshot, TickerData } from "../types";

function formatPct(value: number | null | undefined): string {
  if (typeof value !== "number") {
    return "-";
  }
  return `${value > 0 ? "+" : ""}${value.toFixed(1)}%`;
}

function Instrument({ label, data }: { label: string; data?: TickerData }) {
  return (
    <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs trading-muted">{label}</div>
      <div className="text-lg font-semibold">{data?.ticker || label}</div>
      <div className="text-sm trading-muted">
        {typeof data?.price === "number" ? `$${data.price.toFixed(2)}` : "-"} · {formatPct(data?.change30dPct)}
      </div>
    </div>
  );
}

export default function MarketContext({ snapshot }: { snapshot?: MarketSnapshot }) {
  const sectorRows = Array.isArray(snapshot?.sectors) ? snapshot.sectors.slice(0, 5) : [];
  const provenance = snapshot?.provenance;
  const provenanceAsOf = provenance ? ((provenance as { asOf?: string | null }).asOf ?? provenance.as_of) : null;
  return (
    <section className="copilot-card p-4">
      <div className="mb-4 flex items-start justify-between">
        <div>
          <h2 className="text-base font-semibold">Market Context</h2>
          <p className="text-sm trading-muted">{snapshot?.source || "Cached context"}</p>
          {provenance?.source ? <ProvenanceBadge source={provenance.source} asOf={provenanceAsOf} /> : null}
        </div>
        {snapshot?.asOf ? <span className="text-xs trading-muted">{snapshot.asOf}</span> : null}
      </div>
      <div className="trading-grid trading-grid-3">
        <Instrument label="SPY" data={snapshot?.spy} />
        <Instrument label="VIX" data={snapshot?.vix} />
        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs trading-muted">Sectors</div>
          {sectorRows.length === 0 ? (
            <div className="text-sm trading-muted">No sector context.</div>
          ) : (
            <div className="mt-2 flex flex-col gap-1">
              {sectorRows.map((sector) => (
                <div key={sector.name} className="flex justify-between text-sm">
                  <span>{sector.name}</span>
                  <span className={Number(sector.changePct) >= 0 ? "trading-positive" : "trading-negative"}>
                    {formatPct(sector.changePct)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
