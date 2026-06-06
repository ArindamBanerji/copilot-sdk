import { useEffect, useState } from "react";
import { BASE, normalize } from "../api";

interface CrossGraphInsightCardProps {
  alertId?: string | null;
}

interface ProcessSignal {
  activity?: string;
  currentDuration?: number;
  normalDuration?: number;
  slowdownFactor?: number;
  source?: string;
}

interface ErpImpact {
  affectedPos?: number;
  affectedPlants?: number;
  backlogValue?: number;
  dailyCost?: number;
  source?: string;
}

interface RootCause {
  changeType?: string;
  field?: string;
  newCombinations?: number;
  fanoutMultiplier?: number;
  upstreamSupplier?: string;
  source?: string;
}

interface CombinedImpact {
  monthlyCost?: number;
  annualizedCost?: number;
  confidence?: number;
}

interface CrossGraphInsightResponse {
  alertId?: string;
  processSignal?: ProcessSignal;
  erpImpact?: ErpImpact;
  rootCause?: RootCause;
  combinedImpact?: CombinedImpact;
  sourcesUsed?: string[];
}

type LoadState = "idle" | "loading" | "ready" | "hidden" | "error";

const DEFAULT_INSIGHT: CrossGraphInsightResponse = {
  alertId: "demo",
  processSignal: {
    activity: "Process mining signal",
    source: "celonis",
  },
  erpImpact: {
    source: "sap",
  },
  rootCause: {
    field: "Enterprise graph context",
    changeType: "correlated evidence",
    source: "graph",
  },
  combinedImpact: {},
  sourcesUsed: ["celonis", "sap", "graph"],
};

export function CrossGraphInsightCard({ alertId }: CrossGraphInsightCardProps) {
  const [state, setState] = useState<LoadState>("idle");
  const [data, setData] = useState<CrossGraphInsightResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setState("loading");
    setData(null);
    setError(null);

    const request = alertId ? loadInsight(alertId) : loadDefaultInsight();
    request
      .then((payload) => {
        if (cancelled) {
          return;
        }
        if (!payload) {
          setState("hidden");
          setData(null);
          return;
        }
        setData(payload);
        setState("ready");
      })
      .catch((caught) => {
        if (!cancelled) {
          if (alertId) {
            setError(caught instanceof Error ? caught.message : "Could not load cross-graph insight.");
            setData(null);
            setState("error");
          } else {
            setData(DEFAULT_INSIGHT);
            setState("ready");
          }
        }
      });

    return () => {
      cancelled = true;
    };
  }, [alertId]);

  if (state === "idle" || state === "hidden") {
    return null;
  }

  if (state === "loading") {
    return (
      <section className="copilot-card p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
          Cross-Graph Insight
        </p>
        <p className="mt-2 text-sm dataops-muted">Correlating process, ERP, and graph signals...</p>
      </section>
    );
  }

  if (state === "error") {
    return (
      <section className="copilot-card p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
          Cross-Graph Insight
        </p>
        <p className="mt-2 text-sm" style={{ color: "var(--copilot-danger)" }}>
          {error || "Could not load cross-graph insight."}
        </p>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  return <InsightCard data={data} alertId={alertId ?? data.alertId ?? null} defaultMode={!alertId && data === DEFAULT_INSIGHT} />;
}

async function loadInsight(alertId: string): Promise<CrossGraphInsightResponse | null> {
  const response = await fetch(`${BASE}/api/context/cross-graph-insight/${encodeURIComponent(alertId)}`);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return normalize<CrossGraphInsightResponse>(await response.json());
}

async function loadDefaultInsight(): Promise<CrossGraphInsightResponse> {
  const groupsResponse = await fetch(`${BASE}/api/context/alert-groups`);
  if (!groupsResponse.ok) {
    return DEFAULT_INSIGHT;
  }
  const groups = normalize<{
    groups?: Array<{ alerts?: Array<{ alertId?: string; alert_id?: string }> }>;
    ungrouped?: Array<{ alertId?: string; alert_id?: string }>;
  }>(await groupsResponse.json());
  const groupedAlert = groups.groups?.flatMap((group) => group.alerts || []).find((alert) => alert.alertId || alert.alert_id);
  const fallbackAlert = groups.ungrouped?.find((alert) => alert.alertId || alert.alert_id);
  const defaultAlertId = groupedAlert?.alertId || groupedAlert?.alert_id || fallbackAlert?.alertId || fallbackAlert?.alert_id;
  if (!defaultAlertId) {
    return DEFAULT_INSIGHT;
  }
  return (await loadInsight(defaultAlertId)) ?? DEFAULT_INSIGHT;
}

function InsightCard({
  data,
  alertId,
  defaultMode = false,
}: {
  data: CrossGraphInsightResponse;
  alertId?: string | null;
  defaultMode?: boolean;
}) {
  const sources = data.sourcesUsed || [];
  const processSignal = data.processSignal || {};
  const erpImpact = data.erpImpact || {};
  const rootCause = data.rootCause || {};
  const combinedImpact = data.combinedImpact || {};

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
            Cross-Graph Insight
          </p>
          <h2 className="mt-1 text-xl font-semibold" style={{ color: "var(--copilot-text)" }}>
            SAP, Celonis, and graph evidence aligned
          </h2>
          <p className="mt-1 text-sm dataops-muted">
            {defaultMode
              ? "Default enterprise context view for process, ERP, and graph evidence."
              : sources.length
                ? `${sources.length} sources linked to alert ${data.alertId || alertId}`
                : "Enterprise context available for this alert."}
          </p>
        </div>
        {sources.length ? (
          <span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: "var(--copilot-primary-light)", color: "var(--copilot-primary)" }}>
            {sources.length} sources
          </span>
        ) : null}
      </div>

      <div className="mt-5 grid gap-3">
        <SourceRow
          source="Celonis"
          color="blue"
          title={processSignal.activity || "Process activity"}
          details={[
            ["Current duration", formatDuration(processSignal.currentDuration)],
            ["Normal duration", formatDuration(processSignal.normalDuration)],
            ["Slowdown", formatMultiplier(processSignal.slowdownFactor)],
          ]}
        />
        <SourceRow
          source="SAP"
          color="green"
          title={formatNumber(erpImpact.affectedPos, "POs affected")}
          details={[
            ["Affected plants", formatNumber(erpImpact.affectedPlants)],
            ["Backlog value", formatCurrency(erpImpact.backlogValue)],
            ["Daily cost", formatCurrency(erpImpact.dailyCost)],
          ]}
        />
        <SourceRow
          source="Graph"
          color="purple"
          title={rootCause.field || "Root cause field"}
          details={[
            ["Change type", humanize(rootCause.changeType)],
            ["New combinations", formatNumber(rootCause.newCombinations)],
            ["Fanout", formatMultiplier(rootCause.fanoutMultiplier)],
            ["Supplier", rootCause.upstreamSupplier || null],
          ]}
        />
      </div>

      <div className="mt-5 rounded-md border p-4" style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface-muted)" }}>
        <div className="text-xs font-semibold uppercase tracking-[0.16em] dataops-muted">Combined impact</div>
        <div className="mt-3 grid gap-3 sm:grid-cols-3">
          <ImpactMetric label="Monthly cost" value={formatCurrency(combinedImpact.monthlyCost)} />
          <ImpactMetric label="Annualized cost" value={formatCurrency(combinedImpact.annualizedCost)} />
          <ImpactMetric label="Confidence" value={formatPercent(combinedImpact.confidence)} />
        </div>
      </div>
    </section>
  );
}

function SourceRow({
  source,
  color,
  title,
  details,
}: {
  source: string;
  color: "blue" | "green" | "purple";
  title: string | null;
  details: Array<[string, string | null]>;
}) {
  const palette = sourcePalette(color);
  return (
    <article className="rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: palette.background, color: palette.color }}>
            {source}
          </span>
          <h3 className="mt-3 text-base font-semibold" style={{ color: "var(--copilot-text)" }}>
            {title || "Signal unavailable"}
          </h3>
        </div>
      </div>
      <dl className="mt-3 grid gap-2 sm:grid-cols-2">
        {details
          .filter(([, value]) => Boolean(value))
          .map(([label, value]) => (
            <div key={label} className="rounded-md border px-3 py-2" style={{ borderColor: "var(--copilot-border)" }}>
              <dt className="text-xs font-semibold uppercase dataops-muted">{label}</dt>
              <dd className="mt-1 text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
                {value}
              </dd>
            </div>
          ))}
      </dl>
    </article>
  );
}

function ImpactMetric({ label, value }: { label: string; value: string | null }) {
  return (
    <div>
      <div className="text-xs font-semibold uppercase dataops-muted">{label}</div>
      <div className="mt-1 text-lg font-semibold" style={{ color: "var(--copilot-text)" }}>
        {value || "n/a"}
      </div>
    </div>
  );
}

function sourcePalette(color: "blue" | "green" | "purple") {
  if (color === "blue") {
    return { background: "rgba(59, 130, 246, 0.16)", color: "#93c5fd" };
  }
  if (color === "green") {
    return { background: "rgba(16, 185, 129, 0.16)", color: "#6ee7b7" };
  }
  return { background: "rgba(168, 85, 247, 0.16)", color: "#d8b4fe" };
}

function formatCurrency(value?: number) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return null;
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDuration(value?: number) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return null;
  }
  return `${new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value)} sec`;
}

function formatNumber(value?: number, suffix?: string) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return null;
  }
  const formatted = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
  return suffix ? `${formatted} ${suffix}` : formatted;
}

function formatMultiplier(value?: number) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return null;
  }
  return `${new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(value)}x`;
}

function formatPercent(value?: number) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return null;
  }
  return `${Math.round(value * 100)}%`;
}

function humanize(value?: string) {
  if (!value) {
    return null;
  }
  return value.replace(/_/g, " ");
}
