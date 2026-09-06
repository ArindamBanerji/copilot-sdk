import { useEffect, useState } from "react";
import { fetchGatewayVerifications } from "../api";
import type { GatewayVerification } from "../types";

export default function AgentTrustGatewayPanel() {
  const [entries, setEntries] = useState<GatewayVerification[]>([]);
  useEffect(() => { let cancelled = false; fetchGatewayVerifications().then((response) => { if (!cancelled) setEntries(response ?? []); }); return () => { cancelled = true; }; }, []);
  return <article data-testid="agent-trust-gateway-panel" className="copilot-card p-5"><p className="text-xs font-semibold uppercase tracking-wide text-amber-700">DI-GATEWAY</p><h2 className="mt-1 text-lg font-semibold" style={{ color: "var(--copilot-text)" }}>Agent-trust gateway</h2><p className="mt-1 text-sm dataops-muted">Every automated action should pass a trust and conservation check before authority expands.</p>{entries.length === 0 ? <p className="mt-4 rounded-md border border-dashed border-white/15 p-4 text-sm dataops-muted">No gateway verification records are available.</p> : <div className="mt-4 overflow-x-auto"><table className="w-full text-left text-sm"><thead className="text-xs uppercase tracking-wide dataops-muted"><tr><th className="pb-2">Verification</th><th className="pb-2">Outcome</th><th className="pb-2">Trust</th><th className="pb-2">Gate result</th></tr></thead><tbody>{entries.map((entry, index) => <tr key={gatewayRowKey(entry, index)} data-testid="gateway-verification-row" className="border-t border-white/10"><td className="py-2">{entry.id}</td><td className="py-2">{entry.outcome}</td><td className="py-2">{entry.trustScore === null ? "pending" : entry.trustScore.toFixed(2)}</td><td className="py-2 font-semibold">{entry.gateResult}</td></tr>)}</tbody></table></div>}</article>;
}

function gatewayRowKey(entry: GatewayVerification, index: number): string {
  const trust = entry.trustScore === null ? "pending" : entry.trustScore.toFixed(3);
  return `${entry.id}-${entry.outcome}-${entry.gateResult}-${trust}-${entry.provenance}-${index}`;
}
