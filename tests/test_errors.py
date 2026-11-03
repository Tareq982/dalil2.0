"""Errors carry a code, and every code has a message in the app's languages (web/js/i18n.js)."""
import re
from io import BytesIO
from pathlib import Path

from app import config
from app.main import app

I18N = (Path(__file__).resolve().parent.parent / "web" / "js" / "i18n.js").read_text(encoding="utf-8")
CODES = ["no_file", "unsupported_file", "empty_message", "empty_need", "ai_error",
         "bad_login", "invalid_email", "short_password", "account_exists", "sign_in_first"]


def test_every_error_code_has_a_message_in_all_seven_languages():
    for code in CODES + ["generic", "details"]:
        assert len(re.findall(rf'["\s]err_{code}"?:', I18N)) == 7, code


def test_unsupported_and_missing_files_get_codes(monkeypatch):
    monkeypatch.setattr(config, "MOCK_AI", True)
    client = app.test_client()
    r = client.post("/analyze", data={"file": (BytesIO(b"x"), "a.heic", "image/heic")}, content_type="multipart/form-data")
    assert r.status_code == 400 and r.get_json()["code"] == "unsupported_file"
    r = client.post("/analyze", data={}, content_type="multipart/form-data")
    assert r.get_json()["code"] == "no_file"
    r = client.post("/check-message", data={"file": (BytesIO(b"x"), "a.heic", "image/heic")}, content_type="multipart/form-data")
    assert r.get_json()["code"] == "unsupported_file"
    assert client.post("/check-message", data={"text": " "}).get_json()["code"] == "empty_message"
    assert client.post("/find", json={"text": ""}).get_json()["code"] == "empty_need"


def test_account_errors_get_codes():
    client = app.test_client()
    assert client.post("/api/signup", json={"email": "nope", "password": "longenough"}).get_json()["code"] == "invalid_email"
    assert client.post("/api/signup", json={"email": "a@b.ae", "password": "short"}).get_json()["code"] == "short_password"
    assert client.post("/api/signup", json={"email": "a@b.ae", "password": "longenough"}).status_code == 200
    assert client.post("/api/signup", json={"email": "a@b.ae", "password": "longenough"}).get_json()["code"] == "account_exists"
    assert client.post("/api/login", json={"email": "a@b.ae", "password": "wrongpass"}).get_json()["code"] == "bad_login"


def test_eligibility_says_when_the_rule_was_checked():
    from app import personal
    cards = personal.for_you({"emirate": "Sharjah", "residence": "skilled"})
    assert cards[0]["eligibility"]["grace_days"] == 90 and cards[0]["eligibility"]["checked"] == "2026-10-28"
