"""Personalization: profile privacy filter, official eligibility rules, For you, profile sync."""
from datetime import date

from app import config, finder, personal
from app.main import app

TODAY = date(2026, 11, 2)


def test_profile_keeps_only_allowed_answers():
    p = personal.clean({"emirate": "Dubai", "residence": "sponsored", "residence_expiry": "2026-12-01", "drives": True,
                        "home": "rent", "name": "Arjun", "emirates_id": "784-1990-1234567-1", "emirate_typo": "x"})
    assert p == {"emirate": "Dubai", "residence": "sponsored", "residence_expiry": "2026-12-01", "drives": True, "home": "rent"}
    assert personal.clean({"emirate": "Narnia", "residence": "king", "residence_expiry": "2026-13-45", "drives": "yes"}) == {}


def test_grace_period_comes_from_the_official_data_for_each_residence_type():
    fed = personal.residency_service({"emirate": "Sharjah", "residence": "golden"})
    assert fed["id"] == "federal-residency-notice"
    days = {r: (personal.eligibility({"residence": r}, fed) or {}).get("grace_days") for r in personal.RESIDENCE}
    assert days == {"golden": 180, "graduate": 180, "skilled": 90, "owner": 90, "sponsored": 60, "other": 30,
                    "citizen": None, "not_sure": None}
    dubai = personal.residency_service({"emirate": "Dubai", "residence": "sponsored"})
    assert dubai["id"] == "dubai-residency-notice" and personal.eligibility({"residence": "sponsored"}, dubai)["grace_days"] == 60
    # no checked rule for this category in Dubai: no number is given
    assert personal.eligibility({"residence": "golden"}, dubai) is None


def test_for_you_matches_the_profile():
    cards = personal.for_you({"emirate": "Dubai", "residence": "sponsored", "residence_expiry": "2027-06-01",
                              "drives": True, "home": "rent"}, TODAY)
    assert [c["reason"] for c in cards] == ["residency", "driving", "renting"]
    assert cards[0]["service"]["id"] == "dubai-residency-notice" and cards[0]["eligibility"]["grace_days"] == 60
    assert cards[1]["service"]["id"] == "dubai-traffic-fine" and cards[2]["service"]["id"] == "dubai-tenancy-contract"


def test_expiring_residence_comes_first():
    cards = personal.for_you({"emirate": "Abu Dhabi", "residence": "skilled", "residence_expiry": "2026-11-20",
                              "drives": True}, TODAY)
    assert cards[0]["reason"] == "residency" and cards[0]["days_left"] == 18 and cards[0]["urgent"]
    assert cards[0]["eligibility"]["grace_days"] == 90 and cards[1]["service"]["id"] == "abu-dhabi-traffic-fine"


def test_no_unchecked_services_are_suggested():
    # a citizen renting in Sharjah who drives: Dalil has no checked Sharjah services, so it suggests nothing
    assert personal.for_you({"emirate": "Sharjah", "residence": "citizen", "drives": True, "home": "rent"}, TODAY) == []


def test_for_you_endpoint():
    r = app.test_client().post("/for-you", json={"profile": {"emirate": "Dubai", "home": "rent"}})
    assert [c["reason"] for c in r.get_json()] == ["renting"]


def test_profile_syncs_to_the_account_and_is_filtered():
    c = app.test_client()
    assert c.post("/api/profile", json={"emirate": "Dubai"}).status_code == 401
    c.post("/api/signup", json={"email": "p@example.com", "password": "longpassword"})
    saved = c.post("/api/profile", json={"emirate": "Dubai", "residence": "owner", "passport": "N123"}).get_json()
    assert saved == {"emirate": "Dubai", "residence": "owner"}
    assert c.get("/api/profile").get_json() == saved
    c.delete("/api/account")
    c.post("/api/signup", json={"email": "p@example.com", "password": "longpassword"})
    assert c.get("/api/profile").get_json() == {}   # deleted with the account


def test_find_uses_the_profile(monkeypatch):
    from app import ai
    monkeypatch.setattr(config, "MOCK_AI", False)
    prompts = []
    monkeypatch.setattr(ai, "ask_json", lambda system, text, file=None, max_tokens=2000: (prompts.append(text), {
        "service_id": "federal-residency-notice", "what_it_is": "Renew with ICP.", "cost": "See the fee when you apply.",
        "deadline": "Renew before it expires.", "next_steps": ["Open the ICP website"]})[1])
    r = finder.find("my visa expires soon", "en", profile={"emirate": "Ajman", "residence": "skilled", "name": "x"})
    assert '"emirate": "Ajman"' in prompts[0] and "name" not in prompts[0].split("THEMSELVES")[1]
    assert r["personal"]["grace_days"] == 90
