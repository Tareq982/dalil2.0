"""Anonymous usage counts, thumbs up/down, "Explain it simpler" and the /stats page."""
import sqlite3
from io import BytesIO

from app import catalog, config, stats
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


# ---------------------------------------------------------------- timing test (challenge targets)

def run(client, task, condition, seconds, found=True):
    return client.post("/api/trials", json={"task": task, "condition": condition, "seconds": seconds, "found": found})


def test_timing_test_compares_without_and_with_dalil_against_the_targets():
    client = app.test_client()
    for secs, found in [(240, True), (180, True), (300, False), (200, True), (100, False)]:
        assert run(client, "dubai-visa", "without", secs, found).status_code == 200
    for secs in (60, 50, 70, 40, 90):
        assert run(client, "dubai-fine", "with", secs).status_code == 200
    t = client.get("/api/stats").get_json()["trial"]
    # gave up counts as the 5-minute limit: without = 180, 200, 240, 300, 300 -> median 240
    assert t["without"] == {"runs": 5, "found": 3, "median_seconds": 240, "found_rate": 0.6}
    assert t["with"] == {"runs": 5, "found": 5, "median_seconds": 60, "found_rate": 1.0}
    assert t["discovery_time_cut"] == 0.75 and t["adoption_increase"] == 0.667
    assert t["met"] == {"discovery": True, "adoption": True} and t["enough"] is True
    assert t["per_task"]["dubai-visa"] == {"without": 5, "with": 0}


def test_timing_test_targets_not_met_and_not_enough_runs():
    client = app.test_client()
    run(client, "dubai-rent", "without", 100)
    run(client, "sharjah-visa", "with", 70)
    t = client.get("/api/trials").get_json()
    assert t["discovery_time_cut"] == 0.3 and t["met"]["discovery"] is False
    assert t["adoption_increase"] == 0.0 and t["met"]["adoption"] is False
    assert t["enough"] is False and len(t["tasks"]) == 5


def test_timing_test_rejects_bad_runs_and_can_undo():
    client = app.test_client()
    assert run(client, "made-up", "with", 50).status_code == 400
    assert run(client, "dubai-fine", "sometimes", 50).status_code == 400
    assert run(client, "dubai-fine", "with", 9999).status_code == 400
    assert run(client, "dubai-fine", "with", 50, found="yes").status_code == 400
    run(client, "dubai-fine", "with", 50)
    run(client, "dubai-fine", "without", 150)
    t = client.post("/api/trials/undo").get_json()
    assert t["runs"] == 1 and t["last"] == {"task": "dubai-fine", "condition": "with"}
    assert t["discovery_time_cut"] is None


def test_every_timing_task_points_at_a_checked_service():
    ids = {s["id"] for s in catalog.load()}
    assert all(t["service_id"] in ids for t in stats.TRIAL_TASKS)
    assert app.test_client().get("/timing").status_code == 200
