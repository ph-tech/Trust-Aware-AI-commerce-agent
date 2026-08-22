"""Recommendation scoring engine for Trust-Aware AI Commerce Agent.

This module implements the deterministic, unit-testable scoring heuristic described in the project prompt.

Key points:
- The LLM is not involved here; this is pure code that scores candidate products.
- We accept precomputed component scores (relevance, compatibility) in the 0-100 range.
- Margin is taken from product.margin_pct (0-100).
- Business objective bonus is computed from the product price relative to a provided max_price:
    - For 'increase_aov', higher-priced products score higher on the objective axis.
    - For 'increase_conversion', lower-priced products score higher on the objective axis.
- The final score is a weighted sum of components and returned on a 0-100 scale.

The weights mirror the prompt's prototype heuristics. These weights are intentionally explicit and
not learned from data — include an explanation in code comments and UI.
"""

from typing import Literal

BusinessGoal = Literal["increase_aov", "increase_conversion"]

# Prototype heuristic weights (explicit, not learned)
WEIGHTS = {
    "increase_aov": {
        "relevance": 0.40,
        "compatibility": 0.25,
        "margin": 0.20,
        "objective": 0.15,
    },
    "increase_conversion": {
        "relevance": 0.60,
        "compatibility": 0.25,
        "margin": 0.05,
        "objective": 0.10,
    },
}


def _clamp_0_100(x: float) -> float:
    return max(0.0, min(100.0, x))


def compute_score(
    price: float,
    margin_pct: float,
    relevance: float,
    compatibility: float,
    business_goal: BusinessGoal = "increase_aov",
    max_price_in_catalog: float = 1200.0,
) -> float:
    """Compute a weighted recommendation score (0-100) for a candidate product.

    Parameters
    - price: product price in the same units as max_price_in_catalog
    - margin_pct: product margin percent (0-100)
    - relevance: precomputed relevance score (0-100)
    - compatibility: precomputed compatibility score (0-100)
    - business_goal: either 'increase_aov' or 'increase_conversion'
    - max_price_in_catalog: used to normalize price for the objective bonus

    Returns
    - score: float in range 0-100

    Notes
    - All component inputs (relevance, compatibility, margin_pct) are expected to be in 0-100.
    - The function is deterministic and purely arithmetic so it can be unit-tested and audited.
    """

    # sanitize inputs
    relevance = _clamp_0_100(relevance)
    compatibility = _clamp_0_100(compatibility)
    margin_pct = _clamp_0_100(margin_pct)
    max_price = max(1.0, float(max_price_in_catalog))

    # Normalize price to 0-100 by dividing by max_price
    price_norm = (price / max_price) * 100.0
    price_norm = _clamp_0_100(price_norm)

    # Objective bonus: for AOV prefer higher price; for Conversion prefer lower price
    if business_goal == "increase_aov":
        objective_score = price_norm
    else:  # increase_conversion
        objective_score = 100.0 - price_norm

    # Compose weighted sum
    w = WEIGHTS[business_goal]
    raw_score = (
        relevance * w["relevance"]
        + compatibility * w["compatibility"]
        + margin_pct * w["margin"]
        + objective_score * w["objective"]
    )

    # raw_score is in 0-100 range already because components are 0-100 and weights sum to 1
    score = _clamp_0_100(raw_score)
    return score


if __name__ == "__main__":
    # Example usage
    s = compute_score(price=129.0, margin_pct=40.0, relevance=80.0, compatibility=70.0, business_goal="increase_aov", max_price_in_catalog=1200.0)
    print(f"Example score: {s:.2f}")
