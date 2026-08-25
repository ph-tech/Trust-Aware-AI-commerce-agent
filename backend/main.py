from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from typing import Optional, List, Dict, Any
from backend.scoring import compute_score
from backend import trust as trust_module
import json
import os

app = FastAPI(title="Trust-Aware AI Commerce Agent (backend)")

# Allow CORS from localhost frontend during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_conn():
    conn = sqlite3.connect(os.environ.get("DB_PATH", "data/catalog.db"))
    conn.row_factory = sqlite3.Row
    return conn


class IntentRequest(BaseModel):
    text: str


class IntentResponse(BaseModel):
    category: Optional[str] = None
    budget: Optional[float] = None
    explicit_product: Optional[str] = None
    accept_signal: bool = False
    decline_signal: bool = False


class ScoreRequest(BaseModel):
    product_id: int
    relevance: float
    compatibility: float
    session_id: Optional[int] = None
    business_goal: Optional[str] = "increase_aov"


class RoundtripRequest(BaseModel):
    session_id: Optional[int] = None
    text: str
    business_goal: Optional[str] = "increase_aov"


@app.get("/products")
def list_products(category: Optional[str] = None, max_price: Optional[float] = None, limit: int = 20):
    conn = get_conn()
    c = conn.cursor()
    q = "SELECT id, name, category, price, margin_pct, compatible_with FROM products"
    params: List[Any] = []
    clauses: List[str] = []
    if category:
        clauses.append("category = ?")
        params.append(category)
    if max_price is not None:
        clauses.append("price <= ?")
        params.append(max_price)
    if clauses:
        q += " WHERE " + " AND ".join(clauses)
    q += " ORDER BY price ASC LIMIT ?"
    params.append(limit)
    c.execute(q, params)
    rows = c.fetchall()
    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "name": r["name"],
            "category": r["category"],
            "price": r["price"],
            "margin_pct": r["margin_pct"],
            "compatible_with": json.loads(r["compatible_with"] or "[]"),
        })
    conn.close()
    return results


@app.post("/intent", response_model=IntentResponse)
def extract_intent(req: IntentRequest):
    text = req.text.lower()
    # Very small heuristic-based intent extractor (placeholder for LLM)
    category = None
    for cat in ["laptops", "accessories", "phones", "phone_accessories", "peripherals"]:
        if cat.rstrip('s') in text or cat in text:
            category = cat
            break

    # Budget extraction: find a number pattern like 500, 1200, 60k
    budget = None
    import re

    m = re.search(r"(\d{1,6})(k)?", text)
    if m:
        val = int(m.group(1))
        if m.group(2):
            val = val * 1000
        budget = float(val)

    explicit_product = None
    m2 = re.search(r"show me (?:a |an |the )?([a-z0-9 \-]+)", text)
    if m2:
        explicit_product = m2.group(1).strip()

    accept_signal = any(kw in text for kw in ["yes", "i'll take", "add to cart", "sounds good", "accept"])
    decline_signal = any(kw in text for kw in ["no", "not interested", "don't want", "no thanks", "nah", "dont want"])

    return IntentResponse(
        category=category,
        budget=budget,
        explicit_product=explicit_product,
        accept_signal=accept_signal,
        decline_signal=decline_signal,
    )


@app.post("/score")
def score_product(req: ScoreRequest):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT price, margin_pct FROM products WHERE id = ?", (req.product_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    price = float(row["price"])
    margin = float(row["margin_pct"])

    # Use compute_score to get recommendation score
    score = compute_score(
        price=price,
        margin_pct=margin,
        relevance=req.relevance,
        compatibility=req.compatibility,
        business_goal=req.business_goal or "increase_aov",
        max_price_in_catalog=1200.0,
    )
    return {"score": score}


@app.post("/events")
def apply_event(payload: Dict[str, Any]):
    """Apply an event to a session (accept/decline/exceed_budget/low_relevance/no_more_suggestions).
    Example payload: {"session_id": 1, "event": "decline", "candidate_product_id": 21}
    """
    session_id = payload.get("session_id")
    event = payload.get("event")
    candidate_product_id = payload.get("candidate_product_id")
    reasons = payload.get("reasons", [])
    if session_id is None or event is None:
        raise HTTPException(status_code=400, detail="session_id and event required")

    new_trust = trust_module.apply_event(session_id=session_id, event=event, candidate_product_id=candidate_product_id, reasons=reasons)
    return {"session_id": session_id, "new_trust": new_trust}


@app.post("/roundtrip")
def roundtrip(req: RoundtripRequest):
    # 1) Extract intent
    intent = extract_intent(IntentRequest(text=req.text))

    # 2) Ensure session
    session = trust_module.get_or_create_session(business_goal=req.business_goal)
    session_id = req.session_id or session["id"]

    # 3) Product search: by category or all
    conn = get_conn()
    c = conn.cursor()
    q = "SELECT id, name, category, price, margin_pct, compatible_with FROM products"
    params = []
    clauses = []
    if intent.category:
        clauses.append("category = ?")
        params.append(intent.category)
    if intent.budget:
        clauses.append("price <= ?")
        params.append(intent.budget)
    if clauses:
        q += " WHERE " + " AND ".join(clauses)
    q += " ORDER BY price ASC LIMIT 20"
    c.execute(q, params)
    rows = c.fetchall()

    if not rows:
        conn.close()
        # No products found — return a neutral response
        action = "NO_UPSELL"
        reasons = ["no_matching_products"]
        trust_at_decision = session["interaction_trust"]
        trust_module.write_decision(session_id=session_id, action=action, trust_score_at_decision=trust_at_decision, candidate_product_id=None, reasons=reasons, business_goal=req.business_goal, cart_value_at_decision=session["cart_total"])
        return {"action": action, "reasons": reasons, "message": "I couldn't find matching products right now."}

    # 4) Simple relevance & compatibility heuristics
    candidates = []
    for r in rows:
        compat_list = json.loads(r["compatible_with"] or "[]")
        # Relevance: if explicit product mentioned, boost if name contains the terms
        relevance = 60.0
        if intent.explicit_product and intent.explicit_product in r["name"].lower():
            relevance = 95.0
        elif intent.category and intent.category == r["category"]:
            relevance = 80.0

        # Compatibility: percent of cart items compatible (cart is simple; we use sessions table cart_total only -> no item list),
        # For prototype, if product has compatible_with entries assume medium compatibility
        compatibility = 70.0 if compat_list else 40.0

        score = compute_score(price=float(r["price"]), margin_pct=float(r["margin_pct"]), relevance=relevance, compatibility=compatibility, business_goal=req.business_goal or "increase_aov", max_price_in_catalog=1200.0)
        candidates.append({"product": {"id": r["id"], "name": r["name"], "category": r["category"], "price": r["price"], "margin_pct": r["margin_pct"]}, "relevance": relevance, "compatibility": compatibility, "score": score})

    # pick top candidate by score
    candidates.sort(key=lambda x: x["score"], reverse=True)
    top = candidates[0]

    # 5) Rule evaluation → reasons list
    reasons = []
    # budget check
    if intent.budget and top["product"]["price"] > intent.budget:
        reasons.append("exceeds_stated_budget")
    # low relevance check
    if top["relevance"] < 50.0:
        reasons.append("low_relevance")

    # 6) Get current trust
    current_trust = trust_module.get_session_trust(session_id=session_id)

    # 7) Upsell gate
    action = "NO_UPSELL"
    if current_trust > 70:
        action = "UPSELL"
    elif 40 <= current_trust <= 70:
        if top["relevance"] >= 75.0:
            action = "UPSELL"
    elif 20 <= current_trust < 40:
        # No proactive upsells
        if intent.explicit_product:
            action = "UPSELL"
        else:
            action = "NO_UPSELL"
    else:  # trust < 20
        # shopping assistance only
        if intent.explicit_product:
            action = "UPSELL"
        else:
            action = "NO_UPSELL"

    # 8) Write audit log
    trust_module.write_decision(session_id=session_id, action=action, trust_score_at_decision=current_trust, candidate_product_id=top["product"]["id"], reasons=reasons or ["none"], business_goal=req.business_goal, cart_value_at_decision=trust_module.get_session_cart_total(session_id))

    conn.close()

    response = {
        "session_id": session_id,
        "action": action,
        "candidate": top,
        "reasons": reasons,
        "trust": current_trust,
    }
    if action == "UPSELL":
        response["message"] = f"I recommend {top['product']['name']} for INR {top['product']['price']:.2f}."
    else:
        response["message"] = "I won't proactively suggest items right now."

    return response
