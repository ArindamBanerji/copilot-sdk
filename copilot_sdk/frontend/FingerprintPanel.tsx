export type FingerprintCategory = "signal" | "moderate" | "noise";

export interface FactorItem {
  name: string;
  displayName: string;
  weight: number;
  sigma: number;
  interpretation: string;
  category?: FingerprintCategory;
}

export interface FingerprintPanelProps {
  factors: FactorItem[];
  signalLabel?: string;
  noiseLabel?: string;
  perCategoryPrecision?: Record<string, number>;
  decisionsAnalyzed?: number;
}

interface ClassifiedFactor extends FactorItem {
  resolvedCategory: FingerprintCategory;
}

function clampUnit(value: number): number {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.max(0, Math.min(1, value));
}

function classify(factor: FactorItem): ClassifiedFactor {
  if (factor.category) {
    return { ...factor, resolvedCategory: factor.category };
  }
  if (factor.weight >= 0.6) {
    return { ...factor, resolvedCategory: "signal" };
  }
  if (factor.weight >= 0.3) {
    return { ...factor, resolvedCategory: "moderate" };
  }
  return { ...factor, resolvedCategory: "noise" };
}

function categoryColor(category: FingerprintCategory): string {
  if (category === "signal") {
    return "var(--copilot-fingerprint-clean)";
  }
  if (category === "moderate") {
    return "var(--copilot-fingerprint-moderate)";
  }
  return "var(--copilot-fingerprint-noisy)";
}

function FactorRow({ factor }: { factor: ClassifiedFactor }) {
  const weight = clampUnit(factor.weight);
  const color = categoryColor(factor.resolvedCategory);

  return (
    <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
            {factor.displayName || factor.name}
          </div>
          <div className="text-xs" style={{ color: "var(--copilot-text-muted)" }}>
            sigma {factor.sigma.toFixed(3)} · {factor.interpretation}
          </div>
        </div>
        <div className="text-sm font-semibold" style={{ color }}>
          {(weight * 100).toFixed(0)}%
        </div>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full" style={{ background: "var(--copilot-surface-muted)" }}>
        <div
          className="h-full rounded-full"
          style={{
            width: `${weight * 100}%`,
            background: color,
          }}
        />
      </div>
    </div>
  );
}

function FactorSection({
  title,
  factors,
}: {
  title: string;
  factors: ClassifiedFactor[];
}) {
  if (factors.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col gap-3">
      <h3 className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--copilot-text-subtle)" }}>
        {title}
      </h3>
      {factors.map((factor) => (
        <FactorRow key={factor.name} factor={factor} />
      ))}
    </div>
  );
}

export default function FingerprintPanel({
  factors,
  signalLabel = "Signal",
  noiseLabel = "Noise",
  perCategoryPrecision,
  decisionsAnalyzed,
}: FingerprintPanelProps) {
  const classified = factors.map(classify);
  const signals = classified
    .filter((factor) => factor.resolvedCategory === "signal")
    .sort((a, b) => b.weight - a.weight);
  const moderate = classified
    .filter((factor) => factor.resolvedCategory === "moderate")
    .sort((a, b) => b.weight - a.weight);
  const noise = classified
    .filter((factor) => factor.resolvedCategory === "noise")
    .sort((a, b) => a.weight - b.weight);
  const precisionEntries = Object.entries(perCategoryPrecision || {});

  return (
    <section className="copilot-card p-4">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold" style={{ color: "var(--copilot-text)" }}>
            Fingerprint
          </h2>
          <p className="text-sm" style={{ color: "var(--copilot-text-muted)" }}>
            Factor precision and noise profile
          </p>
        </div>
        {typeof decisionsAnalyzed === "number" ? (
          <div className="text-right text-xs" style={{ color: "var(--copilot-text-muted)" }}>
            <div className="font-semibold" style={{ color: "var(--copilot-text)" }}>
              {decisionsAnalyzed}
            </div>
            analyzed
          </div>
        ) : null}
      </div>

      {classified.length === 0 ? (
        <div className="rounded-md p-4 text-sm" style={{ background: "var(--copilot-surface-muted)", color: "var(--copilot-text-muted)" }}>
          No fingerprint data available.
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-3">
          <FactorSection title={signalLabel} factors={signals} />
          <FactorSection title="Moderate" factors={moderate} />
          <FactorSection title={noiseLabel} factors={noise} />
        </div>
      )}

      {precisionEntries.length > 0 ? (
        <div className="mt-5">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--copilot-text-subtle)" }}>
            Category Precision
          </h3>
          <div className="grid gap-2 md:grid-cols-2">
            {precisionEntries.map(([category, precision]) => (
              <div
                key={category}
                className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
                style={{ borderColor: "var(--copilot-border)" }}
              >
                <span style={{ color: "var(--copilot-text-muted)" }}>{category}</span>
                <span className="font-semibold" style={{ color: "var(--copilot-text)" }}>
                  {(clampUnit(Number(precision)) * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
