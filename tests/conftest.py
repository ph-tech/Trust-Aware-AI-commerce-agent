"""Pytest configuration: add repo root to sys.path so backend modules can be imported."""
import sys
from pathlib import Path

# Add the repo root to sys.path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))
