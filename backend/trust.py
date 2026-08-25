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


def create_session(business_goal: str = "increase_aov") -> Dict[str, Any]:
    conn = _conn()
    c = conn.cursor()
    created_at = datetime.now(timezone.utc).isoformat()
    c.execute(
        "INSERT INTO sessions (created_at, interaction_trust, business_goal, cart_total) VALUES (?, ?, ?, ?)",
        (created_at, 100, business_goal, 0.0),
    )
    conn.commit()
    session_id = c.lastrowid
    conn.close()
    return get_session(session_id)


def get_session(session_id: int) -> Dict[str, Any]:
    conn = _conn()
    c = conn.cursor()
    c.execute(
        "SELECT id, created_at, interaction_trust, business_goal, cart_total, budget_stated "
        "FROM sessions WHERE id = ?",
        (session_id,),
    )
    row = c.fetchone()
    conn.close()
    if not row:
        raise ValueError("session not found")
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
    c.execute("SELECT interaction_trust FROM sessions WHERE id = ?", (session_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise ValueError("session not found")
    current = int(row["interaction_trust"])
    if event not in DELTAS:
        conn.close()
        raise ValueError(f"unsupported trust event: {event}")
    delta = DELTAS[event]
    new_trust = _apply_delta(current, delta)
    c.execute("UPDATE sessions SET interaction_trust = ? WHERE id = ?", (new_trust, session_id))
    c.execute(
        """
        INSERT INTO trust_events (
            session_id, timestamp, event, trust_before, trust_after,
            candidate_product_id, reasons
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            datetime.now(timezone.utc).isoformat(),
            event,
            current,
            new_trust,
            candidate_product_id,
            json.dumps(reasons or [f"event:{event}"]),
        ),
    )
    conn.commit()
    conn.close()
    return new_trust
