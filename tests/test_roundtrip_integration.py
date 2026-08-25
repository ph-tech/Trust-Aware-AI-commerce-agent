"""End-to-end tests for the deterministic recommendation pipeline."""
import sqlite3

from backend import trust
from backend.main import RoundtripRequest, roundtrip


def test_roundtrip_recommends_a_matching_laptop(temp_db):
    response = roundtrip(
        RoundtripRequest(text="I need a laptop under 60000", business_goal="increase_aov")
    )

    assert response["action"] == "UPSELL"
    assert response["candidate"]["product"]["category"] == "laptops"
    assert response["candidate"]["product"]["price"] <= 60000
    assert response["trust"] == 100


def test_roundtrip_returns_neutral_response_when_no_product_matches(temp_db):
    response = roundtrip(
        RoundtripRequest(text="I need a phone under 10", business_goal="increase_aov")
    )

    assert response["action"] == "NO_UPSELL"
    assert response["reasons"] == ["no_matching_products"]


def test_roundtrip_reuses_the_existing_session_for_no_match_responses(temp_db):
    session = trust.create_session()
    trust.apply_event(session["id"], "decline")

    with sqlite3.connect(temp_db) as connection:
        sessions_before = connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]

    response = roundtrip(
        RoundtripRequest(session_id=session["id"], text="I need a phone under 10")
    )

    with sqlite3.connect(temp_db) as connection:
        sessions_after = connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]

    assert response["session_id"] == session["id"]
    assert response["trust"] == 90
    assert sessions_after == sessions_before


def test_low_relevance_rule_updates_trust_before_the_gate_decision(temp_db):
    response = roundtrip(RoundtripRequest(text="Show me something"))

    assert response["reasons"] == ["low_relevance"]
    assert response["trust"] == 85
