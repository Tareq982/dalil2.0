"""Anonymous usage counts, thumbs up/down, "Explain it simpler" and the /stats page."""
import sqlite3
from io import BytesIO

from app import config, stats
from app.main import app

FIELDS = {"doc_type": "traffic_fine", "emirate": "Dubai", "issuing_authority": "Dubai Police",
          "amount_aed": 600, "deadline_date": "2030-01-01", "subject": "Speeding",
          "reference_number": "DXB-123", "plate": "Q 40512", "name": "Arjun"}


def use_mock(monkeypatch):
    monkeypatch.setattr(config, "MOCK_AI", True)


def test_a_scan_is_counted_without_personal_details(monkeypatch):
    use_mock(monkeypatch)
    client = app.test_client()
    r = client.post("/analyze", data={"file": (BytesIO(b"x"), "a.jpg", "image/jpeg"), "lang": "ar"},
                    content_type="multipart/form-data")
    assert r.status_code == 200
    s = client.get("/api/stats").get_json()
    assert s["totals"]["scan"] == 1 and s["scans_by_language"] == {"ar": 1}
    assert s["number_check"] == {"passed": 1}
    rows = sqlite3.connect(config.DB_PATH).execute("SELECT * FROM events").fetchall()
    assert len(rows) == 1 and len(rows[0]) == 6  # time, kind, doc type, language, result, number check: nothing else


def test_thumbs_up_and_down():
    client = app.test_client()
    for helpful in (True, True, False):
        assert client.post("/event", json={"kind": "feedback", "helpful": helpful, "doc_type": "traffic_fine",
                                           "lang": "hi"}).status_code == 200
    assert client.post("/event", json={"kind": "share", "lang": "en"}).status_code == 200
    s = client.get("/api/stats").get_json()
    assert s["helpful"] == {"yes": 2, "no": 1} and s["totals"]["share"] == 1


def test_unknown_or_odd_values_are_not_stored():
    client = app.test_client()
    assert client.post("/event", json={"kind": "drop table"}).status_code == 400
    stats.record("feedback", doc_type="<script>", lang="xx", outcome="yes")
    row = sqlite3.connect(config.DB_PATH).execute("SELECT doc_type, lang FROM events").fetchone()
    assert row == (None, None)


def test_simpler_uses_only_safe_fields_and_is_number_checked(monkeypatch):
    seen = {}

    def fake(fields, service, days_left, lang, simple=False):
        seen.update(fields=fields, service=service, simple=simple, lang=lang)
        return {"what_it_is": "A fine.", "cost": "AED 600.", "deadline": "Soon.", "next_steps": ["Pay online."]}, "passed"

    monkeypatch.setattr("app.pipeline.explain_checked", fake)
    r = app.test_client().post("/simplify", json={"fields": FIELDS, "service_id": "dubai-traffic-fine", "lang": "ur"})
    body = r.get_json()
    assert r.status_code == 200 and body["number_check"] == "passed" and body["language"] == "ur"
    assert seen["simple"] is True and seen["service"]["id"] == "dubai-traffic-fine"
    assert "reference_number" not in seen["fields"] and "plate" not in seen["fields"] and "name" not in seen["fields"]


def test_simpler_in_mock_mode(monkeypatch):
    use_mock(monkeypatch)
    body = app.test_client().post("/simplify", json={"fields": FIELDS, "lang": "en"}).get_json()
    assert body["explanation"]["cost"].startswith("[MOCK simpler]") and body["number_check"] == "passed"


def test_stats_page_is_served():
    assert app.test_client().get("/stats").status_code == 200
