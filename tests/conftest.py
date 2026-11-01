"""Shared test setup: every test uses its own empty database, so running the tests never adds
fake accounts or usage counts to the real data/dalil.db."""
import pytest

from app import config


@pytest.fixture(autouse=True)
def separate_database(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "test.db"))
