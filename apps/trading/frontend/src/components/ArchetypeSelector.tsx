import { useEffect, useMemo, useState } from "react";
import {
  applyArchetype,
  fetchArchetype,
  fetchArchetypes,
  fetchCurrentArchetype,
  type ArchetypeApplyResponse,
  type ArchetypeDetail,
  type ArchetypeSummary,
} from "../api";
import ArchetypeComparisonCard from "./ArchetypeComparisonCard";

function displayName(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default function ArchetypeSelector() {
  const [items, setItems] = useState<ArchetypeSummary[]>([]);
  const [selectedName, setSelectedName] = useState("");
  const [currentName, setCurrentName] = useState("default");
  const [detail, setDetail] = useState<ArchetypeDetail | null>(null);
  const [applied, setApplied] = useState<ArchetypeApplyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([fetchArchetypes("trading"), fetchCurrentArchetype().catch(() => ({ current: "default" }))])
      .then(([payload, current]) => {
        if (cancelled) return;
        setItems(payload);
        setCurrentName(current.current || "default");
        const first = payload[0]?.name || "";
        setSelectedName(first);
      })
      .catch((loadError) => {
        if (!cancelled) setError(loadError instanceof Error ? loadError.message : "Archetypes unavailable");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedName) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    fetchArchetype(selectedName)
      .then((payload) => {
        if (!cancelled) setDetail(payload);
      })
      .catch((loadError) => {
        if (!cancelled) setError(loadError instanceof Error ? loadError.message : "Archetype detail unavailable");
      });
    return () => {
      cancelled = true;
    };
  }, [selectedName]);

  const selected = useMemo(
    () => items.find((item) => item.name === selectedName),
    [items, selectedName],
  );

  async function onApply() {
    if (!selectedName) return;
    const confirmed = window.confirm("Replaces bootstrap centroids. Conservation resets.");
    if (!confirmed) return;
    setApplying(true);
    setError(null);
    try {
      const payload = await applyArchetype(selectedName);
      setApplied(payload);
      setCurrentName(payload.current || payload.archetype || selectedName);
    } catch (applyError) {
      setError(applyError instanceof Error ? applyError.message : "Apply failed");
    } finally {
      setApplying(false);
    }
  }

  if (loading) {
    return <section className="copilot-card p-4 text-sm trading-muted">Loading industry archetypes...</section>;
  }

  return (
    <section className="copilot-card p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">Industry Archetype</h2>
          <p className="mt-1 text-sm trading-muted">
            Current archetype: {currentName === "default" ? "Default (generic)" : displayName(currentName)}
          </p>
        </div>
        <span className="rounded-full border px-3 py-1 text-xs" style={{ borderColor: "var(--copilot-border)" }}>
          Bootstrap selector
        </span>
      </div>

      {error ? <p className="mt-3 text-sm text-red-300">{error}</p> : null}

      <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,280px)_1fr]">
        <div>
          <label className="text-xs trading-muted" htmlFor="archetype-select">Template</label>
          <select
            id="archetype-select"
            className="mt-1 w-full rounded-md border bg-transparent px-3 py-2 text-sm"
            style={{ borderColor: "var(--copilot-border)" }}
            value={selectedName}
            onChange={(event) => {
              setSelectedName(event.target.value);
              setApplied(null);
            }}
          >
            {items.map((item) => (
              <option key={item.name} value={item.name}>
                {displayName(item.name)}
              </option>
            ))}
          </select>
          <button type="button" className="copilot-button mt-3 px-4 py-2 text-sm" disabled={!selectedName || applying} onClick={onApply}>
            {applying ? "Applying..." : "Apply"}
          </button>
        </div>

        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <h3 className="text-sm font-semibold">{displayName(selectedName || selected?.name || "default")}</h3>
          <p className="mt-2 text-sm trading-muted">{detail?.description || selected?.description || "No description available."}</p>
          <div className="mt-3 grid gap-3 sm:grid-cols-3">
            <Fact label="Categories" value={String(detail?.categories?.length ?? selected?.categories?.length ?? 0)} />
            <Fact label="Actions" value={String(detail?.actions?.length ?? selected?.actions?.length ?? 0)} />
            <Fact label="Factors" value={String(detail?.factors?.length ?? selected?.factors?.length ?? 0)} />
          </div>
          <div className="mt-3 rounded-md border border-amber-400/40 bg-amber-400/10 p-3 text-sm text-amber-100">
            Replaces bootstrap centroids. Conservation resets.
          </div>
          {detail?.calibrationNotes?.length ? (
            <ul className="mt-3 list-disc pl-5 text-sm trading-muted">
              {detail.calibrationNotes.map((note) => <li key={note}>{note}</li>)}
            </ul>
          ) : null}
          {applied ? <p className="mt-3 text-sm text-emerald-300">{applied.conservationNote || "Archetype applied."}</p> : null}
        </div>
      </div>

      <ArchetypeComparisonCard currentName={currentName} />
    </section>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs trading-muted">{label}</div>
      <div className="font-semibold">{value}</div>
    </div>
  );
}
