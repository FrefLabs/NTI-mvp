import pytest
from fastapi.testclient import TestClient

from app import database
from app.main import app


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Point the SQLite cache at a fresh temp file for every test."""
    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "test.db")


@pytest.fixture
def client():
    return TestClient(app)
