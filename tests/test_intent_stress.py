"""Stress test: messy/edge case inputs and concurrent requests."""
import pytest
import tempfile
import shutil
import os
import sys
from pathlib import Path
import concurrent.futures


@pytest.fixture(scope="function")
def temp_db(monkeypatch):
    """Create and seed a temporary database for testing."""
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_catalog.db")
    
    # Set environment variable
    monkeypatch.setenv("DB_PATH", db_path)
    
    # Initialize database
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from backend.init_db import ensure_db
    import backend.init_db as init_db_mod
    
    # Temporarily override DB_PATH in the module
    old_path = init_db_mod.DB_PATH
    init_db_mod.DB_PATH = Path(db_path)
    ensure_db()
    init_db_mod.DB_PATH = old_path
    
    yield db_path
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_intent_with_special_characters(temp_db):
    """Test intent extraction handles special characters and unicode."""
    from backend.main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    messy_inputs = [
        "looking for a laptop!!! under $1000 @ best price",
        "café laptop café",
        "laptop 💻 under 1000",
        "laptop; laptop, laptop. laptop?",
    ]
    
    for text in messy_inputs:
        response = client.post(
            "/roundtrip",
            json={"text": text, "business_goal": "increase_aov"}
        )
        assert response.status_code == 200, f"Failed for: {text}"


def test_intent_with_very_long_input(temp_db):
    """Test handling of very long input text."""
    from backend.main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    long_text = "laptop " * 500  # 3000+ characters
    response = client.post(
        "/roundtrip",
        json={"text": long_text, "business_goal": "increase_aov"}
    )
    
    # Should handle gracefully (200, 400, or 413)
    assert response.status_code in [200, 400, 413]


def test_intent_with_numbers_and_currencies(temp_db):
    """Test intent extraction with various currency formats."""
    from backend.main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    currency_inputs = [
        "laptop under 1000 USD",
        "laptop under $1000",
        "laptop under £800",
        "laptop under €900",
        "laptop under 1000 dollars",
    ]
    
    for text in currency_inputs:
        response = client.post(
            "/roundtrip",
            json={"text": text, "business_goal": "increase_aov"}
        )
        assert response.status_code == 200, f"Failed for: {text}"


def test_concurrent_requests(temp_db):
    """Test that backend handles concurrent requests without errors."""
    from backend.main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    def make_request(i):
        return client.post(
            "/roundtrip",
            json={"text": f"laptop {i}", "business_goal": "increase_aov"}
        )
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request, i) for i in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    assert len(results) == 10
    assert all(r.status_code == 200 for r in results), "All requests should succeed"


def test_scoring_edge_cases(temp_db):
    """Test scoring logic with edge case products and criteria."""
    from backend.main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Test with very specific criteria
    edge_cases = [
        "cheapest product available",
        "most expensive product",
        "any laptop",
        "laptop laptop laptop",  # Repetition
    ]
    
    for text in edge_cases:
        response = client.post(
            "/roundtrip",
            json={"text": text, "business_goal": "increase_conversion"}
        )
        assert response.status_code == 200, f"Failed for: {text}"
