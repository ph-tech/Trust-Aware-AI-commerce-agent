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
    from backend.init_db import ensure_db
    
    # Temporarily override DB_PATH
    import backend.init_db
    original = backend.init_db.DB_PATH
    backend.init_db.DB_PATH = Path(db_path)
    ensure_db()
    backend.init_db.DB_PATH = original
    
    yield db_path
    
    if old_db_path:
        os.environ["DB_PATH"] = old_db_path
    else:
        os.environ.pop("DB_PATH", None)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_trust_initialization(temp_db):
    """Test that trust state initializes correctly via the backend."""
    from backend import trust
    
    session = trust.get_or_create_session(business_goal="increase_aov")
    assert session["interaction_trust"] == 100
    assert session["business_goal"] == "increase_aov"


def test_trust_score_update(temp_db):
    """Test trust score updates after events."""
    from backend import trust
    
    session = trust.get_or_create_session()
    initial_score = trust.get_session_trust(session["id"])
    
    # Apply a decline event
    new_score = trust.apply_event(session_id=session["id"], event="decline", candidate_product_id=1)
    
    assert new_score < initial_score, "Score should decrease after decline"


def test_trust_session_creation(temp_db):
    """Test session creation with different goals."""
    from backend import trust
    
    session_aov = trust.get_or_create_session(business_goal="increase_aov")
    session_conv = trust.get_or_create_session(business_goal="increase_conversion")
    
    assert session_aov["business_goal"] == "increase_aov"
    assert session_conv["business_goal"] == "increase_conversion"
    assert session_aov["id"] != session_conv["id"]


def test_trust_deterministic_deltas(temp_db):
    """Test that trust deltas are deterministic."""
    from backend import trust
    
    session = trust.get_or_create_session()
    initial = 100
    
    # Decline event should always apply -10
    new_score = trust.apply_event(session_id=session["id"], event="decline", candidate_product_id=1)
    assert new_score == initial - 10


def test_trust_boundaries(temp_db):
    """Test trust score stays within 0-100."""
    from backend import trust
    
    session = trust.get_or_create_session()
    
    # Apply many decline events to push score to 0
    for _ in range(20):
        score = trust.apply_event(session_id=session["id"], event="decline", candidate_product_id=1)
    
    assert score >= 0, "Score should not go below 0"
    assert score <= 100, "Score should not exceed 100"
