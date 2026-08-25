import { FormEvent, useState } from "react";
import "./App.css";

type BusinessGoal = "increase_aov" | "increase_conversion";

interface Recommendation {
  action: "UPSELL" | "NO_UPSELL";
  message: string;
  trust?: number;
  reasons?: string[];
  candidate?: {
    product: {
      name: string;
      price: number;
    };
    score: number;
  };
}

function App() {
  const [query, setQuery] = useState("");
  const [goal, setGoal] = useState<BusinessGoal>("increase_aov");
  const [result, setResult] = useState<Recommendation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://127.0.0.1:8000/roundtrip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: query, business_goal: goal }),
      });
      if (!response.ok) throw new Error(`The agent returned ${response.status}.`);
      setResult((await response.json()) as Recommendation);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to reach the backend.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="panel">
        <p className="eyebrow">Trust-aware recommendations</p>
        <h1>Find the right product without the pressure.</h1>
        <p className="intro">
          The agent considers relevance, product compatibility, and the customer&apos;s trust before recommending an upsell.
        </p>
        <form onSubmit={submit}>
          <label htmlFor="goal">Business goal</label>
          <select id="goal" value={goal} onChange={(event) => setGoal(event.target.value as BusinessGoal)}>
            <option value="increase_aov">Increase average order value</option>
            <option value="increase_conversion">Increase conversion</option>
          </select>
          <label htmlFor="query">What are you looking for?</label>
          <div className="composer">
            <input
              id="query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="e.g. I need a laptop under $1000"
            />
            <button disabled={loading}>{loading ? "Thinking..." : "Ask agent"}</button>
          </div>
        </form>
      </section>

      {error && <p className="error">{error}</p>}
      {result && (
        <section className="result" aria-live="polite">
          <span className={result.action === "UPSELL" ? "badge recommend" : "badge neutral"}>{result.action.replace("_", " ")}</span>
          <h2>{result.message}</h2>
          {result.candidate && <p>Recommendation score: {result.candidate.score.toFixed(1)} / 100</p>}
          {result.trust !== undefined && <p>Interaction trust: {result.trust} / 100</p>}
          {result.reasons?.length ? <p>Decision notes: {result.reasons.join(", ")}</p> : null}
        </section>
      )}
    </main>
  );
}

export default App;
