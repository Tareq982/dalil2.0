"""Find a service (no document) and the two challenge targets on /stats."""
import pytest

from app import ai, config, finder
from app.main import app


def fake_ai(monkeypatch, *answers):
    """Make the AI return the given JSON answers in order; record the prompts it got."""
    monkeypatch.setattr(config, "MOCK_AI", False)
    it, prompts = iter(answers), []
    monkeypatch.setattr(ai, "ask_json", lambda system, text, file=None, max_tokens=2000: (prompts.append(text), next(it))[1])
    return prompts


GOOD = {"service_id": "federal-residency-notice", "question": None, "options": [],
        "what_it_is": "You need to renew your residence permit with ICP.",
        "cost": "AED 100 for the application, plus AED 100 for each year.",
        "deadline": "You can renew before it expires.", "next_steps": ["Open the ICP website", "Log in with UAE Pass"],
        "suggested_questions": ["What documents do I need?"]}


def test_finds_a_catalog_service_with_its_official_link(monkeypatch):
    prompts = fake_ai(monkeypatch, GOOD)
    r = finder.find("my visa expires next month, I live in Sharjah", "en")
    assert r["service_id"] == "federal-residency-notice" and r["link"].startswith("https://icp.gov.ae")
    assert r["number_check"] == "passed" and r["explanation"]["next_steps"]
    assert "federal-residency-notice" in prompts[0] and "NEED>>>" in prompts[0]  # the catalog and the need are both given


def test_asks_one_question_when_it_cannot_tell(monkeypatch):
    fake_ai(monkeypatch, {"service_id": None, "question": "Which emirate issued your visa?", "options": ["Dubai", "Sharjah"]})
    r = finder.find("I need to renew my visa", "en")
    assert r["question"] == "Which emirate issued your visa?" and r["options"] == ["Dubai", "Sharjah"]
    assert "explanation" not in r


def test_after_the_answer_it_chooses(monkeypatch):
    prompts = fake_ai(monkeypatch, dict(GOOD, service_id="dubai-residency-notice"))
    r = finder.find("I need to renew my visa", "en", answer="Dubai")
    assert r["service_id"] == "dubai-residency-notice" and "Their answer to your question: Dubai" in prompts[0]


def test_an_invented_service_id_is_ignored(monkeypatch):
    fake_ai(monkeypatch, dict(GOOD, service_id="sharjah-free-visa-service"))
    r = finder.find("free visa?", "en")
    assert r["service_id"] is None and r["link"] == finder.PORTAL and r["explanation"]["cost"] == ""


def test_invented_numbers_get_one_retry_then_the_official_page(monkeypatch):
    bad = dict(GOOD, cost="Only AED 49 this month.")
    fake_ai(monkeypatch, bad, bad)
    r = finder.find("renew my visa in Ajman", "ar")
    assert r["number_check"] == "template" and r["explanation"]["cost"] == finder.SEE_OFFICIAL["ar"]


def test_empty_request_is_refused():
    with pytest.raises(ValueError):
        finder.find("   ", "en")
    assert app.test_client().post("/find", json={"text": ""}).status_code == 400


def test_find_endpoint_in_mock_mode_and_counted(monkeypatch):
    monkeypatch.setattr(config, "MOCK_AI", True)
    c = app.test_client()
    r = c.post("/find", json={"text": "I am renting a flat in Dubai, Ejari tenancy contract", "lang": "en"}).get_json()
    assert r["service_id"] == "dubai-tenancy-contract" and r["explanation"]["what_it_is"].startswith("[MOCK]")
    assert c.get("/api/stats").get_json()["find_results"] == {"matched": 1}


def test_targets_discovery_time_and_adoption():
    c = app.test_client()
    # two answers: one explained document, one service found
    from app import stats
    stats.record("scan", "traffic_fine", "en", "explained", "passed")
    stats.record("find", "tenancy_contract", "en", "matched")
    for secs in (30, 50):
        assert c.post("/event", json={"kind": "open_official", "source": "scan", "seconds": secs, "lang": "en"}).status_code == 200
    c.post("/event", json={"kind": "open_official", "source": "scan", "seconds": 99999})  # out of range: no time kept
    c.post("/event", json={"kind": "paid", "doc_type": "traffic_fine"})
    t = c.get("/api/stats").get_json()["targets"]
    assert t["median_seconds_to_official"] == 40.0 and t["timed"] == 2
    assert t["answers"] == 2 and t["opened_official"] == 3 and t["marked_paid"] == 1


# ---------------------------------------------------------------- learning loop + human help

def test_a_need_with_no_service_is_counted_by_topic_only(monkeypatch):
    from app import config
    from app.main import app
    import sqlite3
    monkeypatch.setattr(config, "MOCK_AI", True)
    client = app.test_client()
    r = client.post("/find", json={"text": "I need a birth certificate for my new baby, my name is Sara", "lang": "en"}).get_json()
    assert r["service_id"] is None and r["topic"] == "family"
    owners = client.get("/api/stats").get_json()["owners"]
    assert owners["unmet_needs_by_topic"] == {"family": 1}
    rows = sqlite3.connect(config.DB_PATH).execute("SELECT * FROM events").fetchall()
    assert not any("Sara" in str(v) or "baby" in str(v) for row in rows for v in row)  # never the text


def test_an_unknown_topic_from_the_ai_becomes_other(monkeypatch):
    from app import config, finder
    monkeypatch.setattr(config, "MOCK_AI", False)
    monkeypatch.setattr(finder, "_ask", lambda *a, **k: {"service_id": None, "topic": "<script>", "what_it_is": "Not checked yet."})
    assert finder.find("something odd", "en")["topic"] == "other"


def test_found_services_carry_the_official_call_centre(monkeypatch):
    from app import config, finder
    monkeypatch.setattr(config, "MOCK_AI", True)
    r = finder.find("my residence visa in Dubai expires", "en")
    assert r["service_id"] == "dubai-residency-notice"
    assert r["service"]["help"]["phone"] == "800 5111" and "topic" not in r


def test_every_checked_service_has_a_person_to_call():
    from app import catalog
    for s in catalog.load():
        h = s["help"]
        assert h["phone"] and h["name"] and h["page"].startswith("https://") and h["source"] and h["last_checked"]


def test_thumbs_down_is_counted_per_service_for_its_owner():
    from app.main import app
    client = app.test_client()
    client.post("/event", json={"kind": "feedback", "helpful": False, "service_id": "dubai-tenancy-contract"})
    client.post("/event", json={"kind": "feedback", "helpful": True, "service_id": "dubai-tenancy-contract"})
    client.post("/event", json={"kind": "feedback", "helpful": False, "service_id": "not-a-service"})
    o = client.get("/api/stats").get_json()["owners"]
    assert o["not_clear_by_service"] == {"dubai-tenancy-contract": 1} and o["clear_by_service"] == {"dubai-tenancy-contract": 1}
