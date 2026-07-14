import { FormEvent, useState } from "react";

type QueryResponse = {
  answer?: string;
  evidence?: string[];
  intent?: string;
  query_template?: string;
};

export default function NLQueryPanel() {
  const [question, setQuestion] = useState("What is the most reliable source?");
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const result = await fetch("http://127.0.0.1:8030/api/dataops/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!result.ok) {
        throw new Error("Query failed");
      }
      setResponse((await result.json()) as QueryResponse);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "DataOps query unavailable");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="copilot-card p-5">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="dataops-kicker">Natural language query</p>
          <h2 className="dataops-title">Ask Your Data</h2>
        </div>
        {response?.intent ? (
          <span className="rounded-full px-3 py-1 text-xs font-semibold" style={{ background: "var(--copilot-primary-light)", color: "var(--copilot-primary)" }}>
            {response.intent}
          </span>
        ) : null}
      </div>

      <form className="grid gap-3 md:grid-cols-[1fr_auto]" onSubmit={submit}>
        <input
          aria-label="DataOps question"
          className="rounded-md border px-3 py-2 text-sm"
          placeholder="What is the most reliable source?"
          style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)", color: "var(--copilot-text)" }}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
        />
        <button className="rounded-md px-4 py-2 text-sm font-semibold" style={{ background: "var(--copilot-primary)", color: "white" }} type="submit" disabled={loading || !question.trim()}>
          {loading ? "Asking..." : "Ask"}
        </button>
      </form>

      {error ? <p className="mt-3 text-sm" style={{ color: "var(--copilot-danger)" }}>{error}</p> : null}

      {response ? (
        <div className="mt-4 grid gap-3 text-sm">
          <p>{response.answer || "No answer returned."}</p>
          {response.query_template ? <p className="dataops-muted">Template: {response.query_template}</p> : null}
          <div>
            <p className="mb-2 text-xs font-semibold uppercase dataops-muted">Evidence</p>
            <ul className="grid gap-2">
              {(response.evidence || []).map((item) => (
                <li key={item} className="rounded-md border px-3 py-2" style={{ borderColor: "var(--copilot-border)" }}>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </section>
  );
}
