import { useEffect, useMemo, useState } from "react";
import { getS2PEvolutionVariants, getS2PPromotionCheck } from "../api";
import type {
  S2PEvolutionSummary,
  S2PEvolutionVariantsResponse,
  S2PPromotionCheckResponse,
  S2PPromotionResult,
  S2PVariantSummary
} from "../types";

interface EvolutionState {
  summary: S2PEvolutionSummary | null;
  promotion: S2PPromotionResult | null;
}

function titleCase(value: string): string {
  return value
    .replace(/[_:]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function percent(value?: number): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "n/a";
  return `${Math.round(value * 100)}%`;
}

function rate(variant: S2PVariantSummary): number | undefined {
  return variant.success_rate ?? variant.successRate;
}

function variantCount(summary: S2PEvolutionSummary | null): number {
  return summary?.variant_count ?? summary?.variantCount ?? summary?.variants.length ?? 0;
}

function activeCount(summary: S2PEvolutionSummary | null): number {
  return summary?.active_count ?? summary?.activeCount ?? summary?.variants.filter((variant) => variant.status === "active").length ?? 0;
}

function sdkSummary(response: S2PEvolutionVariantsResponse | null): S2PEvolutionSummary | null {
  return response?.sdk_summary ?? response?.sdkSummary ?? null;
}

function promotedId(promotion: S2PPromotionCheckResponse | null): S2PPromotionResult | null {
  return promotion?.promotion ?? null;
}

function promotionText(promotion: S2PPromotionResult | null): string {
  if (!promotion) return "";
  const promoted = promotion.promoted_id ?? promotion.promotedId ?? "candidate";
  const previous = promotion.previous_id ?? promotion.previousId ?? "active";
  const improvement = promotion.improvement;
  const suffix = typeof improvement === "number" ? ` by ${Math.round(improvement * 100)}pp` : "";
  return `${promoted} replaced ${previous}${suffix}`;
}

export function EvolutionPanel() {
  const [data, setData] = useState<EvolutionState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    Promise.all([getS2PEvolutionVariants(), getS2PPromotionCheck()])
      .then(([variantsResponse, promotionResponse]) => {
        if (cancelled) return;
        setData({
          summary: sdkSummary(variantsResponse),
          promotion: promotedId(promotionResponse)
        });
      })
      .catch((caught) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "Unable to load evolution data");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const variants = data?.summary?.variants ?? [];
  const activeVariants = useMemo(() => variants.filter((variant) => variant.status === "active"), [variants]);

  return (
    <section className="space-y-4" aria-label="S2P preset evolution">
      <article className="copilot-card p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Self-tuning presets</p>
            <h2 className="mt-1 text-xl font-semibold text-slate-950">Variant Evolution</h2>
          </div>
          {loading ? <span className="text-sm text-slate-500">Loading variants...</span> : null}
        </div>

        {error ? (
          <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-700">Unable to load variant evolution.</p>
        ) : null}

        {!loading && !error && variants.length === 0 ? (
          <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-500">No S2P variants are registered yet.</p>
        ) : null}

        {variants.length ? (
          <>
            <div className="mt-4 flex flex-wrap gap-2">
              {activeVariants.map((variant) => (
                <span key={variant.id} className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
                  Active {titleCase(variant.family)}: {variant.id}
                </span>
              ))}
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                {activeCount(data?.summary ?? null)} active / {variantCount(data?.summary ?? null)} total
              </span>
            </div>

            <div className="mt-4 overflow-x-auto">
              <table className="min-w-full border-separate border-spacing-0 text-left text-sm">
                <thead>
                  <tr className="text-xs uppercase tracking-wide text-slate-500">
                    <th className="border-b border-slate-200 px-3 py-2 font-semibold">Variant</th>
                    <th className="border-b border-slate-200 px-3 py-2 font-semibold">Family</th>
                    <th className="border-b border-slate-200 px-3 py-2 font-semibold">Status</th>
                    <th className="border-b border-slate-200 px-3 py-2 font-semibold">Win Rate</th>
                    <th className="border-b border-slate-200 px-3 py-2 font-semibold">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {variants.map((variant) => (
                    <tr key={variant.id} className="text-slate-700">
                      <td className="border-b border-slate-100 px-3 py-3 font-mono text-xs font-semibold text-slate-950">{variant.id}</td>
                      <td className="border-b border-slate-100 px-3 py-3">{titleCase(variant.family)}</td>
                      <td className="border-b border-slate-100 px-3 py-3">
                        <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">
                          {titleCase(variant.status)}
                        </span>
                      </td>
                      <td className="border-b border-slate-100 px-3 py-3">{percent(rate(variant))}</td>
                      <td className="border-b border-slate-100 px-3 py-3">{variant.total ?? 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : null}
      </article>

      <article className="copilot-card p-5">
        <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Promotion Gate</p>
        <div className="mt-3 grid gap-3 sm:grid-cols-3">
          <Metric label="Exploration" value="1.414" />
          <Metric label="Threshold" value="5pp" />
          <Metric label="Min Samples" value="10" />
        </div>
        {data?.promotion ? (
          <p className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-900">
            {promotionText(data.promotion)}
          </p>
        ) : (
          <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-500">No promotion is pending.</p>
        )}
      </article>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-sm font-semibold text-slate-950">{value}</p>
    </div>
  );
}
