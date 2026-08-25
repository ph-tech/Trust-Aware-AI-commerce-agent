"""End-to-end tests for the deterministic recommendation pipeline."""
from backend.main import RoundtripRequest, roundtrip


def test_roundtrip_recommends_a_matching_laptop(temp_db):
    response = roundtrip(
        RoundtripRequest(text="I need a laptop under 1000", business_goal="increase_aov")
    )

    assert response["action"] == "UPSELL"
    assert response["candidate"]["product"]["category"] == "laptops"
    assert response["candidate"]["product"]["price"] <= 1000
    assert response["trust"] == 100


def test_roundtrip_returns_neutral_response_when_no_product_matches(temp_db):
    response = roundtrip(
        RoundtripRequest(text="I need a phone under 10", business_goal="increase_aov")
    )

    assert response["action"] == "NO_UPSELL"
    assert response["reasons"] == ["no_matching_products"]
