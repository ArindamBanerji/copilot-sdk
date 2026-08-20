import type { TrustResponse } from "../types";
import DataProductsCard from "./DataProductsCard";
import { IntelligenceMapPanel } from "./IntelligenceMapPanel";
import TrustCard from "./TrustCard";

export default function DIWiringPanel({ trust }: { trust: TrustResponse | null }) {
  return (
    <section className="grid gap-4" data-testid="di-wiring-panel">
      <div className="copilot-card p-4">
        <p className="dataops-kicker">E5b · Data Intelligence wiring</p>
        <h2 className="dataops-title">Trust → Products → Intelligence Map</h2>
        <p className="mt-1 text-sm dataops-muted">A trust score determines which products are safe, then acquisition advice shows where the next connection compounds value.</p>
        <nav className="mt-3 flex flex-wrap gap-2 text-xs" aria-label="Data Intelligence sequence">
          <a className="rounded-full border px-3 py-1 text-purple-200" href="#di-trust">1 · Trust</a>
          <a className="rounded-full border px-3 py-1 text-purple-200" href="#di-products">2 · Products</a>
          <a className="rounded-full border px-3 py-1 text-purple-200" href="#di-map">3 · Intelligence Map</a>
        </nav>
      </div>
      <div id="di-trust" data-testid="di-wiring-trust"><TrustCard trust={trust} /></div>
      <div id="di-products" data-testid="di-wiring-products"><DataProductsCard /></div>
      <div id="di-map" data-testid="di-wiring-map"><IntelligenceMapPanel /></div>
    </section>
  );
}
