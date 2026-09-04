"""Tests for intent extraction against representative messy inputs."""
import pytest

from backend.main import IntentRequest, extract_intent


@pytest.mark.parametrize(
    ("text", "budget"),
    [
        ("looking for a laptop!!! under $1000 @ best price", 1000.0),
        ("laptop under £800", 800.0),
        ("I need a laptop around 2k", 2000.0),
        ("cafe laptop under 900", 900.0),
    ],
)
def test_intent_extraction_handles_messy_budget_queries(text, budget):
    intent = extract_intent(IntentRequest(text=text))

    assert intent.category == "laptops"
    assert intent.budget == budget


def test_intent_extraction_recognizes_customer_signals():
    accepted = extract_intent(IntentRequest(text="Yes, add it to cart"))
    declined = extract_intent(IntentRequest(text="No thanks, I don't want that"))

    assert accepted.accept_signal is True
    assert declined.decline_signal is True
