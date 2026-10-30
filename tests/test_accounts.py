"""Accounts and synced documents: sign up, sync across 'devices', privacy filter, delete."""
import pytest

from app import config
from app.main import app


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "test.db"))


def device():
    return app.test_client()  # each test client has its own cookies, like a separate phone


def test_sync_across_devices_and_privacy_filter(fresh_db):
    phone = device()
    assert phone.post("/api/signup", json={"email": "Test@Example.com", "password": "longenough"}).status_code == 200
    doc = {"id": "d1", "kind": "traffic_fine", "authority": "Dubai Police", "amount_aed": 600,
           "date": "2026-11-03", "summary": "A speeding fine.", "official_url": "https://www.rta.ae/",
           # sensitive fields a client might send: must be dropped by the server
           "name": "Arjun Menon", "reference_number": "DXB-123", "plate": "Q 40512", "photo": "data:image/png;base64,AAA"}
    saved = phone.post("/api/documents", json=doc).json
    assert saved[0]["amount_aed"] == 600.0
    for secret in ("name", "reference_number", "plate", "photo"):
        assert secret not in saved[0]

    laptop = device()
    assert laptop.get("/api/documents").status_code == 401           # not signed in yet
    assert laptop.post("/api/login", json={"email": "test@example.com", "password": "wrong-pass"}).status_code == 401
    assert laptop.post("/api/login", json={"email": "test@example.com", "password": "longenough"}).status_code == 200
    docs = laptop.get("/api/documents").json
    assert [d["id"] for d in docs] == ["d1"] and "reference_number" not in docs[0]

    assert laptop.delete("/api/documents/d1").status_code == 200
    assert phone.get("/api/documents").json == []


def test_password_is_hashed_and_account_can_be_deleted(fresh_db):
    import sqlite3
    c = device()
    c.post("/api/signup", json={"email": "a@b.co", "password": "secret-123"})
    c.post("/api/documents", json=[{"id": "x", "kind": "tenancy_contract"}, {"id": "y", "kind": "traffic_fine"}])
    row = sqlite3.connect(config.DB_PATH).execute("SELECT password_hash FROM users").fetchone()
    assert "secret-123" not in row[0] and row[0].startswith(("scrypt", "pbkdf2"))
    assert c.delete("/api/account").status_code == 200
    con = sqlite3.connect(config.DB_PATH)
    assert con.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
    assert con.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 0
    assert c.get("/api/me").json == {"email": None}


def test_signup_validation(fresh_db):
    c = device()
    assert c.post("/api/signup", json={"email": "not-an-email", "password": "longenough"}).status_code == 400
    assert c.post("/api/signup", json={"email": "a@b.co", "password": "short"}).status_code == 400
    c.post("/api/signup", json={"email": "a@b.co", "password": "longenough"})
    assert device().post("/api/signup", json={"email": "a@b.co", "password": "longenough"}).status_code == 409


def test_bad_values_are_dropped():
    from app.accounts import clean
    out = clean({"id": "z", "date": "next week", "official_url": "javascript:alert(1)", "status": "hacked",
                 "amount_aed": "abc", "summary": "x" * 5000})
    assert out == {"id": "z", "summary": "x" * 600}


def test_deleting_account_signs_out_other_devices(fresh_db):
    phone, laptop = device(), device()
    phone.post("/api/signup", json={"email": "z@y.co", "password": "longenough"})
    laptop.post("/api/login", json={"email": "z@y.co", "password": "longenough"})
    phone.delete("/api/account")
    assert laptop.get("/api/me").json == {"email": None}
    assert laptop.get("/api/documents").status_code == 401
