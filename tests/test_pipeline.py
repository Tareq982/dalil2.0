"""Run with:  python -m pytest
These tests need no API key: AI calls are replaced by mock answers."""
import pytest

from app import catalog, config, extract, pipeline, safety
from app.main import app


@pytest.fixture(autouse=True)
def mock_ai(monkeypatch):
    monkeypatch.setattr(config, "MOCK_AI", True)


def fields(**over):
    f = dict(extract.MOCK_FIELDS)
    f.update(over)
    return f


# ---- catalog matching (the open-data step)

def test_dubai_speeding_fine_matches_dubai_record():
    s = catalog.match(fields())
    assert s["id"] == "dubai-traffic-fine"
    assert s["matched_item"]["id"] == "speeding"


def test_abu_dhabi_fine_does_not_get_dubai_link():
    s = catalog.match(fields(emirate="Abu Dhabi", issuing_authority="Abu Dhabi Police",
                             keywords=["abu", "dhabi", "police", "speed"]))
    assert s["id"] == "abu-dhabi-traffic-fine"


def test_sharjah_fine_with_no_record_returns_none():
    assert catalog.match(fields(emirate="Sharjah", issuing_authority="Sharjah Police",
                                keywords=["sharjah", "police"])) is None


def test_residency_outside_dubai_uses_federal_record():
    s = catalog.match(fields(doc_type="visa_residency_notice", emirate="Sharjah",
                             issuing_authority="ICP", keywords=["icp", "residency", "visa"]))
    assert s["id"] == "federal-residency-notice"


def test_every_record_has_required_keys():
    required = {"id", "doc_type", "authority", "service_name", "official_url", "next_steps", "source", "verified"}
    for s in catalog.load():
        assert required <= s.keys(), s.get("id")
        assert s["doc_type"] in extract.DOC_TYPES


# ---- safety rules

def test_low_confidence_gives_fallback_not_a_guess():
    assert safety.level(0.2) == 2


def test_unreadable_document_has_zero_confidence():
    assert safety.overall_confidence(fields(readable=False), None) == 0.0


def test_every_language_has_every_safety_string():
    for code in config.LANGUAGES:
        assert safety.TEXT[code].keys() == safety.TEXT["en"].keys(), code


def test_normalise_fixes_bad_model_output():
    out = extract.normalise({"doc_type": "banana", "confidence": "high", "amount_aed": "abc"})
    assert out["doc_type"] == "other" and out["confidence"] == 0.0 and out["amount_aed"] is None


# ---- whole flow (mock AI)

def test_pipeline_end_to_end_mock():
    r = pipeline.analyze(b"fake", "image/jpeg", "hi")
    assert r["service_id"] == "dubai-traffic-fine"
    assert r["explanation"]["next_steps"]
    assert r["footer"]["disclaimer"] == safety.TEXT["hi"]["disclaimer"]
    assert len(pipeline.to_text(r)) <= 1600


def test_web_analyze_endpoint():
    client = app.test_client()
    from io import BytesIO
    r = client.post("/analyze", data={"file": (BytesIO(b"x"), "a.jpg", "image/jpeg"), "lang": "en"},
                    content_type="multipart/form-data")
    assert r.status_code == 200 and r.json["service_id"] == "dubai-traffic-fine"


def test_whatsapp_language_menu():
    client = app.test_client()
    r = client.post("/whatsapp", data={"From": "whatsapp:+971500000000", "Body": "hi there", "NumMedia": "0"})
    assert b"Choose your language" in r.data
    r = client.post("/whatsapp", data={"From": "whatsapp:+971500000000", "Body": "3", "NumMedia": "0"})
    assert "हिन्दी".encode() in r.data
