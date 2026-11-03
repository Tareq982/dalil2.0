"""The "Show this to staff" card (web/js/staff.js): the person's need in Arabic and English,
built by code from the checked catalog and what Dalil read on the paper."""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
I18N = (ROOT / "web" / "js" / "i18n.js").read_text(encoding="utf-8")
SERVICES = json.loads((ROOT / "data" / "services.json").read_text(encoding="utf-8"))["services"]


def test_card_labels_exist_in_all_seven_languages():
    for key in ["staff_title", "staff_text", "staff_copy", "staff_copied", "staff_play"]:
        assert len(re.findall(rf'["\s]{key}"?:', I18N)) == 7, key


def test_every_service_has_its_name_and_authority_in_arabic():
    # The Arabic half of the card names the service from the catalog, never from the AI
    for s in SERVICES:
        ar = s.get("names", {}).get("ar", {})
        assert ar.get("service_name") and ar.get("authority"), s["id"]


def run_card(service_id, fields, lang):
    """Build both notes with the real staff.js in Node."""
    service = next((s for s in SERVICES if s["id"] == service_id), None) if service_id else None
    script = (
        f'import {{ staffText }} from {json.dumps((ROOT / "web" / "js" / "staff.js").as_uri())};'
        f"console.log(JSON.stringify(staffText({json.dumps(service)}, {json.dumps(fields)}, {json.dumps(lang)})));"
    )
    out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


needs_node = pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")


@needs_node
def test_scanned_fine_in_urdu_gives_arabic_and_english_with_the_papers_numbers():
    fine = {"doc_type": "traffic_fine", "reference_number": "DXB-123456", "amount_aed": 600, "deadline_date": "2026-11-30"}
    service = SERVICES[0]
    card = run_card(service["id"], fine, "ur")
    assert service["names"]["ar"]["service_name"] in card["ar"]
    assert service["service_name"] in card["en"]
    for note in card.values():
        assert "DXB-123456" in note and "600" in note and "2026" in note
    assert "الأردية" in card["ar"] and "My language is Urdu" in card["en"]


@needs_node
def test_found_service_without_a_paper_still_names_the_service():
    service = SERVICES[-1]
    card = run_card(service["id"], {}, "ml")
    assert service["names"]["ar"]["service_name"] in card["ar"]
    assert "Malayalam" in card["en"] and "Reference" not in card["en"]


@needs_node
def test_no_language_line_for_arabic_or_english_readers_and_nothing_when_empty():
    service = SERVICES[0]
    assert "My language" not in run_card(service["id"], {}, "ar")["en"]
    assert "My language" not in run_card(service["id"], {}, "en")["en"]
    assert run_card(None, {}, "ur") == {"ar": "", "en": ""}
