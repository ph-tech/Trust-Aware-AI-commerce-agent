"""Shared pytest fixtures for isolated catalog databases."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.init_db import ensure_db


@pytest.fixture
def temp_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Seed a database unique to the current test."""
    db_path = tmp_path / "catalog.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    ensure_db()
    return db_path
