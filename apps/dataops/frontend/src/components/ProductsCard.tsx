import { useEffect, useState } from "react";
import { fetchDIProducts } from "../api";
import type { DIProduct } from "../types";

function iksTone(iks: number) {
  if (iks > 50) {
    return "text-emerald-300";
  }
  if (iks >= 20) {
    return "text-amber-300";
  }
  return "text-red-300";
}

function conservationTone(status?: string) {
  const normalized = status?.toUpperCase();
  if (normalized === "GREEN") {
    return "border-emerald-300/40 bg-emerald-500/10 text-emerald-200";
  }
  if (normalized === "AMBER") {
    return "border-amber-300/40 bg-amber-500/10 text-amber-200";
  }
  return "border-red-300/40 bg-red-500/10 text-red-200";
}

function maturityLabel(label?: string) {
  const normalized = label?.toLowerCase();
  if (normalized === "mature") {
    return "mature";
  }
  if (normalized === "developing" || normalized === "emerging" || normalized === "learning") {
    return "learning";
  }
  return "bootstrap";
}

function autonomyLabel(status?: string) {
  return status?.toUpperCase() === "GREEN"
    ? "GREEN · safe for autonomous consumption"
    : "AMBER · require human review";
}

function ProductCard({ product }: { product: DIProduct }) {
  const iks = product.iks ?? 0;
  const maturity = maturityLabel(product.maturityLabel);
  return (
    <article
      data-testid="di-product"
      className="rounded-md border border-purple-300/20 bg-purple-500/[0.04] p-4"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-white">{product.productName || product.productId || "Data product"}</h3>
          <p className="mt-1 text-xs dataops-muted">Maturity: {maturity}</p>
        </div>
        <span className={`text-3xl font-semibold ${iksTone(iks)}`} aria-label={`IKS ${iks}`}>
          {iks}
        </span>
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
        <span className={`rounded-full border px-2 py-1 font-semibold ${conservationTone(product.conservationStatus)}`}>
          {product.conservationStatus || "UNKNOWN"}
        </span>
        <span className={`rounded-full border px-2 py-1 font-semibold ${product.conservationStatus?.toUpperCase() === "GREEN" ? "border-emerald-300/40 text-emerald-200" : "border-amber-300/40 text-amber-200"}`}>
          {autonomyLabel(product.conservationStatus)}
        </span>
        <span className="dataops-muted">{product.sources?.length ?? 0} sources</span>
        <span className="dataops-muted">{product.verifiedDecisions ?? 0} verified</span>
      </div>
    </article>
  );
}

export default function ProductsCard() {
  const [products, setProducts] = useState<DIProduct[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchDIProducts().then((payload) => {
      if (!cancelled) {
        setProducts(payload?.products || []);
        setLoading(false);
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const averageIks = products.length
    ? Math.round(products.reduce((sum, product) => sum + (product.iks ?? 0), 0) / products.length)
    : 0;

  return (
    <section data-testid="products-card" className="copilot-card p-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-purple-200/75">Data Intelligence</p>
          <h2 className="mt-1 text-xl font-semibold text-white">Data Products</h2>
        </div>
        <p className="text-sm dataops-muted">
          {loading ? "Loading products..." : `${products.length} data products. Average IKS: ${averageIks}.`}
        </p>
      </div>
      {!loading && products.length === 0 ? (
        <p className="mt-4 text-sm dataops-muted">No data products available.</p>
      ) : (
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {products.map((product) => (
            <ProductCard key={product.productId || product.productName} product={product} />
          ))}
        </div>
      )}
    </section>
  );
}
