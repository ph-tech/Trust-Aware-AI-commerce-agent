"""Test roundtrip integration: end-to-end flow from user text to response."""
import pytest
import tempfile
import shutil
import os
import sys
from pathlib import Path

# Create temp DB for tests
@pytest.fixture
def temp_db():
    """Create and seed a temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_catalog.db")
    
    # Set env var so backend uses this DB
    old_db_path = os.environ.get("DB_PATH")
    os.environ["DB_PATH"] = db_path
    
    # Import and run ensure_db with temp path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from backend.init_db import ensure_db, DB_PATH as original_path
    
    # Temporarily override DB_PATH
    import backend.init_db
    original = backend.init_db.DB_PATH
    backend.init_db.DB_PATH = Path(db_path)
    ensure_db()
    backend.init_db.DB_PATH = original
    
    yield db_path
    
    # Cleanup
    if old_db_path:
        os.environ["DB_PATH"] = old_db_path
    else:
        os.environ.pop("DB_PATH", None)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_roundtrip_valid_request(temp_db):
    """Test that a valid roundtrip request returns expected structure."""
    from backend.main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    response = client.post(
        "/roundtrip",
        json={"text": "looking for a laptop under 1000", "business_goal": "increase_aov"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data or "message" in data


def test_roundtrip_with_conversion_goal(temp_db):
    """Test roundtrip with maximize_conversion goal."""
    from backend.main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    response = client.post(
        "/roundtrip",
        json={"text": "show me budget laptops", "business_goal": "increase_conversion"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data or "message" in data


def test_roundtrip_empty_text(temp_db):
    """Test that empty text is handled gracefully."""
    from backend.main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    response = client.post(
        "/roundtrip",
        json={"text": "", "business_goal": "increase_aov"}
    )
    
    # Should either return 200 or 400
    assert response.status_code in [200, 400]


def test_roundtrip_missing_business_goal(temp_db):
    """Test that missing business_goal defaults appropriately."""
    from backend.main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    response = client.post(
        "/roundtrip",
        json={"text": "looking for a laptop"}
    )
    
    # Should use default goal or return 422
    assert response.status_code in [200, 422]
