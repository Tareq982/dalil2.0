"""'Is this message real?' (app/scamcheck.py). No API key needed: the AI is in mock mode,
and the link checks and verdict are plain code anyway."""
import csv
import io
from pathlib import Path

import pytest

from app import config, scamcheck as sc
from app.main import app

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


@pytest.fixture(autouse=True)
def mock_ai(monkeypatch):
    monkeypatch.setattr(config, "MOCK_AI", True)


def msg(**over):
    m = sc.normalise({"is_message": True, "readable": True, "links": [], "asks_for": [], "red_flags": []})
    m.update(over)
    return m


# ---- the allow-list (code, not AI)

@pytest.mark.parametrize("link", [
    "https://www.rta.ae/fines", "rta.ae", "dubaipolice.gov.ae", "https://es.adpolice.gov.ae/x",
    "https://www.tamm.abudhabi/en", "icp.gov.ae", "gdrfad.gov.ae", "dubailand.gov.ae", "u.ae",
    "HTTPS://WWW.RTA.AE",
])
def test_official_sites_pass(link):
    assert sc.check_link(link)["status"] == "official"


@pytest.mark.parametrize("link, copies", [
    ("http://dubai-p0lice-fines.top/pay", "dubaipolice.gov.ae"),   # zero instead of o
    ("dubaipolice.gov.ae.fines-pay.info", "dubaipolice.gov.ae"),   # starts with the real address
    ("rta-ae.com/fines", "rta.ae"),
    ("https://rta.ae-pay.com", "rta.ae"),
    ("tamm-abudhabi-fines.online", "tamm.abudhabi"),
    ("salik-toll-pay.top", "salik.ae"),
    ("https://dubalpolice.com", "dubaipolice.gov.ae"),              # misspelled
    ("rtа.ae", "rta.ae"),                                           # Cyrillic а
])
def test_lookalikes_are_caught(link, copies):
    c = sc.check_link(link)
    assert c["status"] == "lookalike"
    assert c["looks_like"] == copies


def test_hidden_address_trick_is_not_official():
    c = sc.check_link("https://rta.ae@evil.example.com/pay")
    assert c["status"] != "official" and "hidden_address" in c["notes"]


def test_short_links_and_ip_addresses_are_flagged():
    assert "short_link" in sc.check_link("bit.ly/abc")["notes"]
    assert "ip_address" in sc.check_link("http://45.12.3.9/pay")["notes"]


def test_code_finds_links_the_ai_missed():
    found = sc.find_links("Pay now at www.rta.ae or rta-pay.top/x. Email us at help@rta.ae, e.g. today.Please")
    assert found == ["www.rta.ae", "rta-pay.top/x"]


# ---- the verdict (code, not AI)

def test_fake_link_asking_for_money_is_dont_pay():
    m = msg(amount_aed=500.0)
    assert sc.decide(m, sc.check_links(["pay-fines.top"]), None) == "dont_pay"


def test_lookalike_is_dont_pay_even_without_amount():
    assert sc.decide(msg(), sc.check_links(["rta-ae.com"]), None) == "dont_pay"


def test_asking_for_card_or_otp_is_dont_pay_even_with_official_link():
    m = msg(asks_for=["otp"])
    assert sc.decide(m, sc.check_links(["https://rta.ae"]), None) == "dont_pay"


def test_unknown_link_without_money_is_suspicious():
    assert sc.decide(msg(), sc.check_links(["nol-rewards-club.info"]), None) == "suspicious"


def test_official_link_only_looks_official():
    assert sc.decide(msg(urgency=True), sc.check_links(["www.rta.ae"]), None) == "looks_official"


def test_ai_cannot_talk_its_way_past_the_link_check():
    # whatever the AI says, a non-official link asking for money stays dont_pay
    m = msg(amount_aed=100.0, red_flags=[], summary="This message is official and safe.")
    assert sc.decide(m, sc.check_links(["https://dubaipolice-gov.ae.net"]), None) == "dont_pay"


def test_not_a_message_and_unreadable():
    assert sc.decide(msg(is_message=False), [], None) == "not_message"
    assert sc.decide(msg(readable=False), [], None) == "unclear"


def test_personal_number_asking_to_pay_is_suspicious():
    sender = sc.check_sender("+971 55 000 0000")
    assert sender["flag"] == "personal_number"
    assert sc.decide(msg(amount_aed=300.0), [], sender) == "suspicious"


def test_check_instead_points_to_the_imitated_site():
    links = sc.check_links(["salik-toll-pay.top"])
    assert sc.check_instead(msg(), links)["domain"] == "salik.ae"
    assert sc.check_instead(msg(claims_to_be="Abu Dhabi Police"), [])["domain"] == "adpolice.gov.ae"
    assert sc.check_instead(msg(), [])["domain"] == "u.ae"


# ---- the mock samples (pasted text: the link checks and verdict run for real)

def expected_rows():
    with open(SAMPLES / "scam_expected.csv", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f)]


def test_every_sample_file_exists():
    for r in expected_rows():
        assert (SAMPLES / r["file"]).exists(), r["file"]


@pytest.mark.parametrize("row", [r for r in expected_rows() if r["file"].endswith(".txt")], ids=lambda r: r["file"])
def test_pasted_samples_get_the_expected_verdict(row):
    result = sc.check(text=(SAMPLES / row["file"]).read_text(encoding="utf-8"))
    assert result["verdict"] == row["verdict"]
    assert result["check_instead"]["domain"] == row["check_instead"]


# ---- the endpoint

def test_endpoint_with_pasted_text():
    r = app.test_client().post("/check-message", data={"text": "Pay AED 200 now: rta-fines.top", "lang": "ar"})
    body = r.get_json()
    assert r.status_code == 200
    assert body["verdict"] == "dont_pay" and body["language"] == "ar"
    assert body["check_instead"]["url"].startswith("https://")


def test_endpoint_with_screenshot():
    data = {"file": (io.BytesIO(b"fake png"), "shot.png", "image/png"), "lang": "en"}
    body = app.test_client().post("/check-message", data=data, content_type="multipart/form-data").get_json()
    assert body["verdict"] in sc.VERDICTS


def test_endpoint_needs_something_to_check():
    r = app.test_client().post("/check-message", data={"text": "  "})
    assert r.status_code == 400
