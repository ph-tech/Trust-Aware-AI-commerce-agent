import pytest
from backend.scoring import compute_score


def test_score_range():
    s = compute_score(price=129.0, margin_pct=40.0, relevance=80.0, compatibility=70.0, business_goal="increase_aov", max_price_in_catalog=1200.0)
    assert 0.0 <= s <= 100.0


def test_aov_prefers_higher_price():
    # Same product except price: higher price should score higher for AOV
    s_low = compute_score(price=100.0, margin_pct=30.0, relevance=80.0, compatibility=70.0, business_goal="increase_aov", max_price_in_catalog=1200.0)
    s_high = compute_score(price=500.0, margin_pct=30.0, relevance=80.0, compatibility=70.0, business_goal="increase_aov", max_price_in_catalog=1200.0)
    assert s_high > s_low


def test_conversion_prefers_lower_price():
    # For conversion goal, lower price should score higher
    s_low = compute_score(price=100.0, margin_pct=30.0, relevance=80.0, compatibility=70.0, business_goal="increase_conversion", max_price_in_catalog=1200.0)
    s_high = compute_score(price=500.0, margin_pct=30.0, relevance=80.0, compatibility=70.0, business_goal="increase_conversion", max_price_in_catalog=1200.0)
    assert s_low > s_high


def test_goals_differ_for_same_input():
    s_aov = compute_score(price=200.0, margin_pct=20.0, relevance=60.0, compatibility=50.0, business_goal="increase_aov", max_price_in_catalog=1200.0)
    s_conv = compute_score(price=200.0, margin_pct=20.0, relevance=60.0, compatibility=50.0, business_goal="increase_conversion", max_price_in_catalog=1200.0)
    assert s_aov != s_conv


def test_input_clamping():
    # Values outside 0-100 should be clamped
    s = compute_score(price=2000.0, margin_pct=200.0, relevance=-50.0, compatibility=150.0, business_goal="increase_aov", max_price_in_catalog=1200.0)
    assert 0.0 <= s <= 100.0
