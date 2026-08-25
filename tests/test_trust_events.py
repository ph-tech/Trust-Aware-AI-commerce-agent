"""Tests for trust changes and audit persistence."""
import sqlite3

from backend import trust


def test_decline_reduces_trust_and_records_an_audit_event(temp_db):
    session = trust.get_or_create_session()

    assert trust.apply_event(session["id"], "decline", candidate_product_id=1) == 90

    with sqlite3.connect(temp_db) as connection:
        event = connection.execute(
            "SELECT action, trust_score_at_decision FROM decisions WHERE session_id = ?",
            (session["id"],),
        ).fetchone()
    assert event == ("NO_UPSELL", 100)


def test_trust_is_clamped_at_zero(temp_db):
    session = trust.get_or_create_session()

    for _ in range(20):
        trust.apply_event(session["id"], "no_more_suggestions")

    assert trust.get_session_trust(session["id"]) == 0
