import { useEffect, useMemo, useState } from "react";
import { EvolutionPanel, type EvolutionVariant } from "../../../../../copilot_sdk/frontend";
import {
  fetchS2PEvolutionRules,
  fetchS2PEvolutionVariants,
  fetchS2PPromotedRules,
  fetchS2PShadowResults
} from "../api";
import type {
  S2PEvolutionRule,
  S2PEvolutionVariant,
  S2PPromotedResponse,
  S2PShadowResult,
  S2PShadowResultsResponse
} from "../types";

function ensureArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? value as T[] : [];
}

interface EvolutionData {
  rules: S2PEvolutionRule[];
  variants: S2PEvolutionVariant[];
  shadowResults: S2PShadowResultsResponse | null;
  promoted: S2PPromotedResponse | null;
}

function text(value: unknown, fallback = ""): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function numberValue(...values: unknown[]): number | undefined {
  for (const value of values) {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return undefined;
}

function variantId(variant: S2PEvolutionVariant): string {
  return text(variant.variant_id, text(variant.variantId, text(variant.id, "variant")));
}

function templateName(variant: S2PEvolutionVariant): string {
  return text(variant.template_name, text(variant.templateName, "Evolution variant"));
}

function titleCase(value: string): string {
  return value
    .replace(/[_:]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function promotedVariantId(promoted: S2PPromotedResponse | null): string {
  const item = promoted?.promoted;
  if (!item || typeof item !== "object") return "";
  return text(item.variant_id, text(item.variantId));
}

function flattenShadowResults(response: S2PShadowResultsResponse | null): Array<S2PShadowResult & { variantId: string }> {
  const raw = response?.results;
  if (!raw) return [];
  if (Array.isArray(raw)) {
    const fallbackId = text(response?.variant_id, text(response?.variantId));
    return raw.map((result) => ({ ...result, variantId: fallbackId }));
  }
  return Object.entries(raw).flatMap(([id, rows]) => rows.map((result) => ({ ...result, variantId: id })));
}

function toEvolutionVariant(
  variant: S2PEvolutionVariant,
  promotedId: string,
  shadowRows: Array<S2PShadowResult & { variantId: string }>,
): EvolutionVariant {
  const id = variantId(variant);
  const wins = shadowRows.filter((result) => result.variantId === id && (result.win || result.better)).length;
  const total = shadowRows.filter((result) => result.variantId === id).length;
  const winRate = numberValue(variant.win_rate, variant.winRate, total > 0 ? wins / total : undefined);
  const sampleSize = numberValue(variant.sample_size, variant.sampleSize, total);
  const status = id === promotedId ? "promoted" : total > 0 ? "shadow" : "created";
  const category = text(variant.category, Array.isArray(variant.categories) ? variant.categories.join(", ") : "");
  const parameter = text(variant.parameter);

  return {
    id,
    name: titleCase(`${templateName(variant)}${category ? ` ${category}` : ""}`),
    status,
    description: [parameter ? `Parameter: ${titleCase(parameter)}` : "", category ? `Category: ${titleCase(category)}` : ""]
      .filter(Boolean)
      .join(" | "),
    shadowCount: sampleSize,
    shadowWinRate: winRate,
    sourceCopilot: text(variant.source, "S2P")
  };
}

function hasData(data: EvolutionData | null): boolean {
  return Boolean(
    data &&
      (data.rules.length > 0 ||
        data.variants.length > 0 ||
        flattenShadowResults(data.shadowResults).length > 0 ||
        Object.keys(data.promoted?.promoted ?? {}).length > 0),
  );
}

function formatPercent(value: unknown): string {
  const parsed = numberValue(value);
  return typeof parsed === "number" ? `${Math.round(parsed * 100)}%` : "n/a";
}

export function S2PEvolutionPanel() {
  const [data, setData] = useState<EvolutionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([
      fetchS2PEvolutionRules(),
      fetchS2PEvolutionVariants(),
      fetchS2PShadowResults(),
      fetchS2PPromotedRules()
    ])
      .then(([rules, variants, shadowResults, promoted]) => {
        if (cancelled) return;
        setData({
          rules: ensureArray<S2PEvolutionRule>(rules?.rules),
          variants: variants?.variants ?? [],
          shadowResults,
          promoted
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

  const shadowRows = useMemo(() => flattenShadowResults(data?.shadowResults ?? null), [data?.shadowResults]);
  const promoted = data?.promoted?.promoted ?? null;
  const promotedId = promotedVariantId(data?.promoted ?? null);
  const variants = useMemo(
    () => (data?.variants ?? []).map((variant) => toEvolutionVariant(variant, promotedId, shadowRows)),
    [data?.variants, promotedId, shadowRows],
  );
  const latestEvents = shadowRows.slice(0, 5);

  return (
    <section className="space-y-4" aria-label="S2P evolution">
      <article className="copilot-card p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">AgentEvolver</p>
            <h2 className="mt-1 text-xl font-semibold text-slate-950">S2P evolution</h2>
          </div>
          {loading ? <span className="text-sm text-slate-500">Loading evolution data...</span> : null}
        </div>

        {error ? (
          <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-700">Unable to load evolution data.</p>
        ) : null}

        {!loading && !error && !hasData(data) ? (
          <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-500">No evolution data yet.</p>
        ) : null}

        {ensureArray<S2PEvolutionRule>(data?.rules).length ? (
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {ensureArray<S2PEvolutionRule>(data?.rules).map((rule) => (
              <div key={rule.rule_id ?? rule.ruleId ?? rule.name} className="rounded-md border border-slate-200 bg-white p-4">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-sm font-semibold text-slate-950">{titleCase(text(rule.label, rule.name))}</h3>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                    {rule.variant_count ?? rule.variantCount ?? 0} variants
                  </span>
                </div>
                <p className="mt-2 text-sm text-slate-600">
                  {titleCase(text(rule.success_metric_name, text(rule.successMetricName, "success metric")))}
                </p>
                <p className="mt-2 text-xs text-slate-500">
                  {ensureArray<string>(rule.applicable_categories ?? rule.applicableCategories).map(titleCase).join(", ") || "All S2P categories"}
                </p>
              </div>
            ))}
          </div>
        ) : null}
      </article>

      {variants.length ? <EvolutionPanel variants={variants} title="Evolution variants" /> : null}

      <article className="copilot-card p-5">
        <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Promoted rules</p>
        {promoted && Object.keys(promoted).length > 0 ? (
          <div className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
            <h3 className="font-semibold">{titleCase(text(promoted.template_name, "Promoted rule"))}</h3>
            <p className="mt-1">
              {text(promoted.variant_id, "variant")} {text(promoted.category) ? `| ${titleCase(text(promoted.category))}` : ""}
            </p>
            {typeof promoted.evidence === "object" && promoted.evidence ? (
              <p className="mt-2 text-xs">
                Win rate {formatPercent((promoted.evidence as Record<string, unknown>).win_rate)} | Conservation{" "}
                {text((promoted.evidence as Record<string, unknown>).conservation_status, "n/a")}
              </p>
            ) : null}
          </div>
        ) : (
          <p className="mt-3 rounded-md bg-slate-50 p-3 text-sm text-slate-500">No promoted rules yet.</p>
        )}
      </article>

      <article className="copilot-card p-5">
        <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Evolution history</p>
        {latestEvents.length ? (
          <ol className="mt-3 space-y-3">
            {latestEvents.map((event, index) => (
              <li key={`${event.variantId}-${index}`} className="rounded-md border border-slate-200 bg-white p-4 text-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-semibold text-slate-950">{titleCase(event.variantId)}</span>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                    {event.win || event.better ? "win" : event.regression ? "regression" : "shadow"}
                  </span>
                </div>
                <p className="mt-2 text-slate-600">
                  Accuracy {formatPercent(event.accuracy)} vs baseline {formatPercent(event.baseline_accuracy ?? event.baselineAccuracy)}
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  {text(event.metric_name, text(event.metricName, "shadow result"))} | sample {numberValue(event.sample_size, event.sampleSize) ?? 0}
                </p>
              </li>
            ))}
          </ol>
        ) : (
          <p className="mt-3 rounded-md bg-slate-50 p-3 text-sm text-slate-500">No evolution history yet.</p>
        )}
      </article>
    </section>
  );
}
