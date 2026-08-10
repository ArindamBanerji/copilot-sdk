import { useEffect, useMemo, useState } from "react";

export interface DataTrustFactor {
  name: string;
  weight: number;
  label?: string;
}

export interface DataTrustBadgeProps {
  apiBase: string;
  copilot: string;
  factorLabels?: Record<string, string>;
  accent?: string;
}

interface FingerprintPayload {
  factors?: unknown;
}

const MAX_FACTORS = 5;

export default function DataTrustBadge({
  apiBase,
  copilot,
  factorLabels = {},
  accent = "var(--copilot-primary)",
}: DataTrustBadgeProps) {
  const [factors, setFactors] = useState<DataTrustFactor[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const base = apiBase.replace(/\/$/, "");

    fetch(`${base}/api/fingerprint`)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Fingerprint request failed: ${response.status}`);
        }
        return (await response.json()) as FingerprintPayload;
      })
      .then((payload) => {
        if (!cancelled) {
          setFactors(normalizeFactors(payload.factors));
        }
      })
      .catch(() => {
        if (!cancelled) {
          setFactors([]);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [apiBase]);

  const visibleFactors = useMemo(() => selectFactors(factors), [factors]);
  const highest = visibleFactors[0]?.weight ?? 0;
  const lowest = visibleFactors[visibleFactors.length - 1]?.weight ?? 0;

  return (
    <section
      className="copilot-card p-4"
      data-testid="data-trust-badge"
      data-trust-state={loading ? "loading" : visibleFactors.length > 0 ? "ready" : "empty"}
      style={{ borderLeft: `4px solid ${accent}` }}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: accent }}>
            Data Trust
          </p>
          <h2 className="mt-1 text-base font-semibold" style={{ color: "var(--copilot-text, #111827)" }}>
            Learned source reliability
          </h2>
        </div>
        <span className="text-xs dataops-muted">{copilot}</span>
      </div>

      {loading ? (
        <p className="mt-3 text-sm dataops-muted" data-testid="data-trust-loading">Loading trust weights...</p>
      ) : visibleFactors.length === 0 ? (
        <p className="mt-3 text-sm dataops-muted" data-testid="data-trust-empty">Trust weights are not available yet.</p>
      ) : (
        <>
          <div className="mt-4 grid gap-3" data-testid="data-trust-factors">
            {visibleFactors.map((factor) => {
              const label = factorLabels[factor.name] || factor.label || humanize(factor.name);
              const level = trustLevel(factor.weight);
              return (
                <div key={factor.name} data-testid="data-trust-factor" data-trust-level={level}>
                  <div className="mb-1 flex items-center justify-between gap-3 text-xs">
                    <span style={{ color: "var(--copilot-text, #111827)" }}>{label}</span>
                    <span className="font-semibold" aria-label={`${label} trust ${factor.weight.toFixed(2)}`}>
                      {factor.weight.toFixed(2)}
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full" style={{ background: "var(--copilot-surface-muted, #e5e7eb)" }}>
                    <div
                      className="h-full rounded-full"
                      data-testid="data-trust-bar"
                      style={{ width: `${Math.round(factor.weight * 100)}%`, background: colorForLevel(level) }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
          <p className="mt-3 text-xs dataops-muted" data-testid="data-trust-contrast">
            Highest {highest.toFixed(2)} · Lowest {lowest.toFixed(2)} · Spread {(highest - lowest).toFixed(2)}
          </p>
        </>
      )}
    </section>
  );
}

function normalizeFactors(raw: unknown): DataTrustFactor[] {
  if (Array.isArray(raw)) {
    return raw.flatMap((item) => {
      if (!isRecord(item) || typeof item.name !== "string") {
        return [];
      }
      const weight = numeric(item.dk_weight ?? item.weight);
      return weight === null ? [] : [{ name: item.name, weight, label: optionalString(item.displayName) }];
    });
  }
  if (isRecord(raw)) {
    return Object.entries(raw).flatMap(([name, value]) => {
      const weight = numeric(value);
      return weight === null ? [] : [{ name, weight }];
    });
  }
  return [];
}

function selectFactors(factors: DataTrustFactor[]): DataTrustFactor[] {
  const sorted = [...factors].sort((left, right) => right.weight - left.weight);
  if (sorted.length <= MAX_FACTORS) {
    return sorted;
  }
  return [...sorted.slice(0, 3), ...sorted.slice(-2)];
}

function trustLevel(weight: number): "high" | "medium" | "low" {
  if (weight > 0.7) return "high";
  if (weight >= 0.3) return "medium";
  return "low";
}

function colorForLevel(level: ReturnType<typeof trustLevel>): string {
  if (level === "high") return "var(--copilot-success, #16a34a)";
  if (level === "medium") return "var(--copilot-warning, #d97706)";
  return "var(--copilot-danger, #dc2626)";
}

function humanize(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function numeric(value: unknown): number | null {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(0, Math.min(1, number)) : null;
}

function optionalString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}
