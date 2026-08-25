# Minimal deterministic trust engine and audit logger for local use.
# Implements the Interaction Trust deltas from the spec and writes decisions to the SQLite DB.
import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import os


def _conn():
    conn = sqlite3.connect(os.environ.get("DB_PATH", "data/catalog.db"))
    conn.row_factory = sqlite3.Row
    return conn


def get_or_create_session(business_goal: str = "increase_aov") -> Dict[str, Any]:
    conn = _conn()
    c = conn.cursor()
    # Create a fresh session (simple single-session prototype). We always create a new session.
    created_at = datetime.now(timezone.utc).isoformat()
    c.execute(
        "INSERT INTO sessions (created_at, interaction_trust, business_goal, cart_total) VALUES (?, ?, ?, ?)",
        (created_at, 100, business_goal, 0.0),
    )
    conn.commit()
    session_id = c.lastrowid
    c.execute("SELECT id, created_at, interaction_trust, business_goal, cart_total, budget_stated FROM sessions WHERE id = ?", (session_id,))
    row = c.fetchone()
    conn.close()
    return dict(row)


def get_session_trust(session_id: int) -> int:
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT interaction_trust FROM sessions WHERE id = ?", (session_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise ValueError("session not found")
    return int(row["interaction_trust"])


def get_session_cart_total(session_id: int) -> float:
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT cart_total FROM sessions WHERE id = ?", (session_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise ValueError("session not found")
    return float(row["cart_total"] or 0.0)


# Deterministic deltas per spec
DELTAS = {
    "accept": 5,
    "decline": -10,
    "exceeds_stated_budget": -20,
    "low_relevance": -15,
    "no_more_suggestions": -30,
}


def _apply_delta(current: int, delta: int) -> int:
    new = current + delta
    # Keep trust in 0-100
    return max(0, min(100, new))


def write_decision(
    session_id: int,
    action: str,
    trust_score_at_decision: int,
    candidate_product_id: Optional[int],
    reasons: list,
    business_goal: Optional[str],
    cart_value_at_decision: float,
) -> None:
    conn = _conn()
    c = conn.cursor()
    timestamp = datetime.now(timezone.utc).isoformat()
    c.execute(
        "INSERT INTO decisions (session_id, timestamp, action, trust_score_at_decision, candidate_product_id, reasons, business_goal, cart_value_at_decision) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (session_id, timestamp, action, int(trust_score_at_decision), candidate_product_id, json.dumps(reasons), business_goal, cart_value_at_decision),
    )
    conn.commit()
    conn.close()


def apply_event(session_id: int, event: str, candidate_product_id: Optional[int] = None, reasons: Optional[list] = None) -> int:
    """
    Apply a session event and update interaction_trust deterministically.
    Supported events (strings): 'accept', 'decline', 'exceeds_stated_budget', 'low_relevance', 'no_more_suggestions'
    Returns the new trust score.
    """
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT interaction_trust, cart_total, business_goal FROM sessions WHERE id = ?", (session_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise ValueError("session not found")
    current = int(row["interaction_trust"])
    delta = DELTAS.get(event, 0)
    new_trust = _apply_delta(current, delta)
    c.execute("UPDATE sessions SET interaction_trust = ? WHERE id = ?", (new_trust, session_id))
    conn.commit()
    conn.close()

    # Write a decision/audit-log entry for visibility
    write_decision(
        session_id=session_id,
        action="UPSELL" if event == "accept" else "NO_UPSELL",
        trust_score_at_decision=current,  # trust at moment of decision
        candidate_product_id=candidate_product_id,
        reasons=reasons or [f"event:{event}"],
        business_goal=row["business_goal"],
        cart_value_at_decision=row["cart_total"],
    )
    return new_trust
