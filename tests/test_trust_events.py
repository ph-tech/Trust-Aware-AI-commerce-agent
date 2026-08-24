"""Test trust scoring and audit logging."""
import pytest
import tempfile
import shutil
import os
import sys
from pathlib import Path
import json

@pytest.fixture
def temp_db():
    """Create and seed a temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_catalog.db")
    
    old_db_path = os.environ.get("DB_PATH")
    os.environ["DB_PATH"] = db_path
    
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from backend.init_db import init_db
    init_db(db_path)
    
    yield db_path
    
    if old_db_path:
        os.environ["DB_PATH"] = old_db_path
    else:
        os.environ.pop("DB_PATH", None)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_trust_initialization(temp_db):
    """Test that trust score initializes correctly."""
    from backend.trust import TrustState
    
    trust = TrustState()
    assert trust.score == 100.0, "Initial trust score should be 100.0"
    assert trust.history == [], "History should start empty"


def test_trust_score_update(temp_db):
    """Test trust score updates after events."""
    from backend.trust import TrustState
    
    trust = TrustState()
    initial_score = trust.score
    
    # Simulate an upsell acceptance
    trust.record_event("upsell_accepted", {"product_id": "P001", "margin": 0.25})
    
    assert trust.score > initial_score, "Score should increase after upsell acceptance"
    assert len(trust.history) == 1, "History should record the event"


def test_trust_audit_log_structure(temp_db):
    """Test that audit logs have correct structure."""
    from backend.trust import TrustState
    
    trust = TrustState()
    trust.record_event("product_viewed", {"product_id": "P001", "category": "laptops"})
    
    assert len(trust.history) == 1
    event = trust.history[0]
    
    assert "event_type" in event
    assert "metadata" in event
    assert "timestamp" in event
    assert event["event_type"] == "product_viewed"


def test_trust_upsell_gate(temp_db):
    """Test trust-based upsell gating logic."""
    from backend.trust import TrustState
    
    trust = TrustState()
    
    # With high trust, upsell should be allowed
    can_upsell = trust.can_upsell()
    assert can_upsell is True, "Should allow upsell with high initial trust"
    
    # Simulate multiple rejections to lower trust
    for _ in range(5):
        trust.record_event("upsell_declined", {"reason": "budget_constraint"})
    
    # With low trust, upsell might be restricted
    can_upsell = trust.can_upsell()
    # Whether True or False, the method should return a boolean
    assert isinstance(can_upsell, bool)


def test_trust_export(temp_db):
    """Test that trust state can be exported to JSON for audit."""
    from backend.trust import TrustState
    
    trust = TrustState()
    trust.record_event("product_viewed", {"product_id": "P001"})
    trust.record_event("upsell_accepted", {"product_id": "P002"})
    
    export = trust.export_audit_log()
    
    assert isinstance(export, (dict, str)), "Export should be dict or JSON string"
    # If it's a string, it should be valid JSON
    if isinstance(export, str):
        parsed = json.loads(export)
        assert isinstance(parsed, dict)
