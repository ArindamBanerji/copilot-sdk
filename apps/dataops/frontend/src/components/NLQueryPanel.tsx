import { useState, type FormEvent } from "react";
import { queryDataOps } from "../api";
import type { QueryResponse, SourceAttribution } from "../types";

const EXAMPLE_QUESTIONS = [
  "How many decisions?",
  "What is accuracy?",
  "Which source is most reliable?",
];

type QueryState = "idle" | "loading" | "success" | "error" | "insufficient";

export default function NLQueryPanel() {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [state, setState] = useState<QueryState>("idle");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      return;
    }

    setState("loading");
    setResponse(null);
    try {
      const result = await queryDataOps(trimmedQuestion);
      setResponse(result);
      setState(result.confidenceLabel?.toLowerCase() === "insufficient" ? "insufficient" : "success");
    } catch {
      setState("error");
    }
  }

  const confidenceLabel = response?.confidenceLabel || "insufficient";
  const confidenceTone = confidenceToneFor(confidenceLabel);
  const sourceAttribution = response?.sourceAttribution || [];

  return (
    <section className="copilot-card p-5" data-testid="nl-query-panel">
      <div className="mb-4">
        <p className="dataops-kicker">Natural language query</p>
        <h2 className="dataops-title">Ask Your Data</h2>
        <p className="mt-1 text-sm dataops-muted">
          Ask a question and see the answer, evidence, and sources behind it.
        </p>
      </div>

      <form className="grid gap-3" onSubmit={submit}>
        <div className="flex flex-col gap-2 sm:flex-row">
          <label className="sr-only" htmlFor="dataops-query-input">Ask about your data</label>
          <input
            id="dataops-query-input"
            aria-label="Ask about your data"
            className="min-w-0 flex-1 rounded-md border px-3 py-2 text-sm"
            placeholder="Ask about your data..."
            style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)", color: "var(--copilot-text)" }}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
          <button
            className="rounded-md px-4 py-2 text-sm font-semibold"
            style={{ background: "var(--copilot-primary)", color: "white" }}
            type="submit"
            disabled={state === "loading" || !question.trim()}
          >
            {state === "loading" ? "Analyzing..." : "Ask"}
          </button>
        </div>

        <div className="flex flex-wrap gap-2" aria-label="Example questions">
          {EXAMPLE_QUESTIONS.map((example) => (
            <button
              key={example}
              className="rounded-full border px-3 py-1 text-xs dataops-muted"
              style={{ borderColor: "var(--copilot-border)" }}
              type="button"
              onClick={() => setQuestion(example)}
            >
              {example}
            </button>
          ))}
        </div>
      </form>

      {state === "loading" ? (
        <p className="mt-4 text-sm dataops-muted" role="status">Analyzing your question...</p>
      ) : null}

      {state === "error" ? (
        <div className="mt-4 rounded-md border px-4 py-3 text-sm" role="alert" style={{ borderColor: "var(--copilot-danger)", color: "var(--copilot-danger)" }}>
          Unable to process query
        </div>
      ) : null}

      {state === "idle" ? (
        <p className="mt-4 text-sm dataops-muted">Ask a question to see quality-aware answers</p>
      ) : null}

      {response && (state === "success" || state === "insufficient") ? (
        <div className="mt-5 grid gap-4" data-testid="nl-query-response">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="mb-1 text-xs font-semibold uppercase dataops-muted">Answer</p>
              <p className="text-xl font-semibold" data-testid="query-answer">{response.answer || "No answer returned."}</p>
            </div>
            <span
              className="rounded-full px-3 py-1 text-xs font-semibold"
              data-testid="query-confidence"
              style={{ background: confidenceTone.background, color: confidenceTone.color }}
            >
              {confidenceLabel} · {formatConfidence(response.confidence)}
            </span>
          </div>

          {response.qualityWarning ? (
            <div className="rounded-md border px-4 py-3 text-sm" role="alert" data-testid="query-quality-warning" style={{ borderColor: "#d99a22", background: "#fff7df", color: "#78520b" }}>
              {response.qualityWarning}
            </div>
          ) : null}

          <section>
            <h3 className="mb-2 text-xs font-semibold uppercase dataops-muted">Source attribution</h3>
            <div className="grid gap-3" data-testid="source-attribution">
              {sourceAttribution.length > 0 ? sourceAttribution.map((source, index) => (
                <SourceBar key={`${source.sourceId || source.source || "source"}-${index}`} source={source} />
              )) : <p className="text-sm dataops-muted">No source attribution available.</p>}
            </div>
          </section>

          <details data-testid="computation-path">
            <summary className="cursor-pointer text-sm font-semibold">Computation path</summary>
            <ol className="mt-2 grid gap-2 pl-5 text-sm dataops-muted">
              {(response.computationPath || []).map((step, index) => <li key={`${step}-${index}`}>{step}</li>)}
            </ol>
          </details>

          {response.evidence ? (
            <div>
              <h3 className="mb-1 text-xs font-semibold uppercase dataops-muted">Evidence</h3>
              <p className="text-sm">{response.evidence}</p>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function SourceBar({ source }: { source: SourceAttribution }) {
  const trust = clamp(Number(source.trust ?? 0));
  const sourceName = source.source || source.sourceId || "Unknown source";
  return (
    <div data-testid="source-attribution-row">
      <div className="mb-1 flex items-center justify-between gap-3 text-sm">
        <span className="font-medium">{sourceName}</span>
        <span className="dataops-muted">{Math.round(trust * 100)}% trust</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full" style={{ background: "var(--copilot-border)" }}>
        <div
          data-testid="source-attribution-bar"
          className="h-full rounded-full"
          style={{ width: `${trust * 100}%`, background: trust >= 0.8 ? "var(--copilot-success)" : trust >= 0.5 ? "#d99a22" : "var(--copilot-danger)" }}
        />
      </div>
      {source.contribution ? <p className="mt-1 text-xs dataops-muted">{source.contribution}</p> : null}
    </div>
  );
}

function clamp(value: number): number {
  return Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : 0;
}

function formatConfidence(value?: number): string {
  return value == null ? "" : `${Math.round(clamp(value) * 100)}%`;
}

function confidenceToneFor(label: string): { background: string; color: string } {
  switch (label.toLowerCase()) {
    case "high":
      return { background: "var(--copilot-success-light)", color: "var(--copilot-success)" };
    case "moderate":
      return { background: "#fff7df", color: "#78520b" };
    case "low":
      return { background: "#fde8e8", color: "var(--copilot-danger)" };
    default:
      return { background: "var(--copilot-border)", color: "var(--copilot-text-muted)" };
  }
}
