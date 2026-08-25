import { FormEvent, type CSSProperties, useState } from "react";
import "./App.css";

type BusinessGoal = "increase_aov" | "increase_conversion";

interface ChatMessage {
  id: number;
  role: "customer" | "agent";
  content: string;
}

interface Recommendation {
  session_id?: number;
  action: "UPSELL" | "NO_UPSELL";
  message: string;
  trust?: number;
  reasons?: string[];
  candidate?: {
    product: {
      id: number;
      name: string;
      price: number;
      category: string;
    };
    score: number;
  };
}

const quickPrompts = [
  "I need a laptop under 60000",
  "Show me a phone under 40000",
  "Find a useful laptop accessory",
];

const formatRupees = (amount: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);

const productVisualClass = (category: string) =>
  category.includes("phone") ? "phone" : category === "laptops" ? "laptop" : "accessory";

function App() {
  const [query, setQuery] = useState("");
  const [goal, setGoal] = useState<BusinessGoal>("increase_aov");
  const [result, setResult] = useState<Recommendation | null>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 0,
      role: "agent",
      content: "Tell me what you are shopping for and your budget. I will only recommend what is useful.",
    },
  ]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!query.trim()) return;

    const customerMessage = query.trim();
    setMessages((current) => [...current, { id: Date.now(), role: "customer", content: customerMessage }]);
    setQuery("");
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://127.0.0.1:8000/roundtrip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: customerMessage,
          business_goal: goal,
          session_id: sessionId ?? undefined,
        }),
      });
      if (!response.ok) throw new Error(`The agent returned ${response.status}.`);
      const recommendation = (await response.json()) as Recommendation;
      setResult(recommendation);
      setSessionId(recommendation.session_id ?? null);
      setMessages((current) => [
        ...current,
        { id: Date.now() + 1, role: "agent", content: recommendation.message },
      ]);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to reach the backend.");
    } finally {
      setLoading(false);
    }
  }

  async function recordFeedback(event: "accept" | "decline") {
    if (!result?.session_id) return;

    try {
      const response = await fetch("http://127.0.0.1:8000/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: result.session_id,
          event,
          candidate_product_id: result.candidate?.product.id,
        }),
      });
      if (!response.ok) throw new Error("Unable to record feedback.");
      const feedback = (await response.json()) as { new_trust: number };
      setResult((current) => (current ? { ...current, trust: feedback.new_trust } : current));
      setMessages((current) => [
        ...current,
        {
          id: Date.now(),
          role: "agent",
          content: event === "accept" ? "Great choice. I have noted that recommendation." : "Understood. I will keep future suggestions more conservative.",
        },
      ]);
    } catch (feedbackError) {
      setError(feedbackError instanceof Error ? feedbackError.message : "Unable to record feedback.");
    }
  }

  const trust = result?.trust ?? 100;

  return (
    <main className="page">
      <header className="topbar">
        <a className="brand" href="/">
          <span className="brand-mark">T</span>
          <span>truely<span>cart</span></span>
        </a>
        <nav aria-label="Primary navigation"><a href="#shop">Shop</a><a href="#deals">Deals</a><a href="#how-it-works">How it works</a></nav>
        <div className="online"><i /> Personalised picks</div>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">Technology, made simple</p>
          <h1>Shop electronics<br />with confidence.</h1>
          <p className="intro">Tell us what you need and your budget. We will narrow down the catalog to useful, relevant options.</p>
          <div className="hero-perks"><span>Prices in INR</span><span>Transparent recommendations</span></div>
        </div>
        <div className="hero-photo" role="img" aria-label="Laptop on a desk">
          <div className="photo-caption"><span>Built around your needs</span><strong>Clear choices. No noise.</strong></div>
          <div className="trust-card">
            <div className="trust-ring" style={{ "--trust": `${trust}%` } as CSSProperties}>
              <span>{trust}</span><small>/100</small>
            </div>
            <div><strong>Trust signal</strong><p>Always customer-first</p></div>
          </div>
        </div>
      </section>

      <section className="category-row" id="shop">
        <button type="button" onClick={() => setQuery("I need a laptop under 60000")}><span>01</span><b>Laptops</b><small>Work, study and everyday use</small></button>
        <button type="button" onClick={() => setQuery("Show me a phone under 40000")}><span>02</span><b>Phones</b><small>Find a phone that fits your day</small></button>
        <button type="button" onClick={() => setQuery("Find a useful laptop accessory")}><span>03</span><b>Accessories</b><small>Useful upgrades for your setup</small></button>
      </section>

      <section className="workspace" id="how-it-works">
        <div className="chat-panel">
          <div className="panel-head">
            <div><p className="micro-label">Product finder</p><h2>What are you looking for?</h2></div>
            <span className="secure">Recommendation history</span>
          </div>
          <div className="messages" aria-live="polite">
            {messages.map((message) => (
              <article className={`message ${message.role}`} key={message.id}>
                <span className="avatar">{message.role === "agent" ? "T" : "You"}</span>
                <p>{message.content}</p>
              </article>
            ))}
            {loading && <article className="message agent"><span className="avatar">T</span><p className="typing">Checking available products...</p></article>}
          </div>
          <div className="quick-prompts">
            {quickPrompts.map((prompt) => <button type="button" key={prompt} onClick={() => setQuery(prompt)}>{prompt}</button>)}
          </div>
          <form className="composer" onSubmit={submit}>
            <input id="query" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Try “laptop for college under ₹60,000”" aria-label="Shopping query" />
            <button className="send" disabled={loading || !query.trim()} aria-label="Ask shopping assistant">{loading ? "..." : "Find match"}</button>
          </form>
        </div>

        <aside className="decision-panel">
          <div className="panel-head"><div><p className="micro-label">Recommendation</p><h2>Best match</h2></div><span className={`status ${result?.action === "UPSELL" ? "good" : ""}`}>{result?.action?.replace("_", " ") ?? "READY"}</span></div>
          <label className="goal-label" htmlFor="goal">Your shopping goal</label>
          <select id="goal" value={goal} onChange={(event) => setGoal(event.target.value as BusinessGoal)}>
            <option value="increase_aov">Higher order value</option>
            <option value="increase_conversion">Better conversion</option>
          </select>
          {result?.candidate ? (
            <div className="product-card">
              <div className={`product-visual ${productVisualClass(result.candidate.product.category)}`}><i /><b /><em /></div>
              <div className="product-details"><p className="micro-label">{result.candidate.product.category.replace("_", " ")}</p>
              <h3>{result.candidate.product.name}</h3>
              <strong>{formatRupees(result.candidate.product.price)}</strong></div>
              <div className="score-row"><span>Fit score</span><b>{result.candidate.score.toFixed(0)}<small>/100</small></b></div>
              <div className="score-track"><i style={{ width: `${result.candidate.score}%` }} /></div>
              <div className="decision-reasons">
                <span>Relevance checked</span><span>Trust respected</span>
              </div>
              <div className="feedback">
                <button type="button" onClick={() => recordFeedback("decline")}>Not for me</button>
                <button type="button" className="primary-action" onClick={() => recordFeedback("accept")}>This works</button>
              </div>
            </div>
          ) : <div className="empty-state"><span className="empty-orb">T</span><h3>Start with what you need</h3><p>Share a product type and a budget to get a focused recommendation.</p></div>}
          {result?.reasons?.length ? <p className="notes">Decision notes: {result.reasons.join(", ")}</p> : null}
        </aside>
      </section>
      {error && <p className="error">{error}</p>}
    </main>
  );
}

export default App;
