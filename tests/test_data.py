"""Checks on the verified catalog and the open-data lookup tool."""
import csv
import re

from app import catalog, config
from tools import lookup_service_prices as lsp

SOURCES = (config.DATA_DIR / "sources.md").read_text(encoding="utf-8")


def test_verified_records_have_official_source_and_date():
    for s in catalog.load():
        if s["verified"]:
            assert s["source_url"] and s["last_checked"], s["id"]
            assert re.search(r"\.(gov\.ae|abudhabi)/|//u\.ae/|dubailand\.gov\.ae|rta\.ae", s["source_url"]), s["id"]


def test_every_record_is_in_sources_md():
    for s in catalog.load():
        assert s["id"] in SOURCES, s["id"]


def test_related_datasets_are_documented():
    for s in catalog.load():
        for d in s.get("related_datasets", []):
            assert f"| {d} |" in SOURCES, (s["id"], d)


def test_lookup_tool_filters_by_entity_and_keywords(tmp_path):
    path = tmp_path / "prices.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=lsp.COLUMNS)
        w.writeheader()
        w.writerow({"service_fees_code": "1", "government_entity_en": "Dubai Land Department",
                    "service_name_en": "Ejari Registration", "fee_name_en": "Registration fee",
                    "amount_en": "100", "pricing_type_en": "Fee", "fee_status_en": "Active"})
        w.writerow({"service_fees_code": "2", "government_entity_en": "Roads And Transport Authority",
                    "service_name_en": "Pay fines", "fee_name_en": "Knowledge fee",
                    "amount_en": "10", "pricing_type_en": "Fee", "fee_status_en": "Active"})
    hits = lsp.search(str(path), "land department", ["ejari"])
    assert [h["service_fees_code"] for h in hits] == ["1"]
    assert lsp.search(str(path), "roads", ["ejari"]) == []


def test_lookup_tool_reads_real_file_spelling(tmp_path):
    """The downloaded CSV spells columns without inner underscores (feename_en, ...)."""
    path = tmp_path / "real.csv"
    header = ["amount_ar", "amount_en", "collectioncycle_ar", "collectioncycle_en", "entitytype_ar",
              "entitytype_en", "feename_ar", "feename_en", "feestatus_en", "governmententity_en",
              "pricingtype_en", "servicefeescode", "servicename_en"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerow({"amount_en": "100", "feename_en": "Registration fee", "feestatus_en": "Active",
                    "governmententity_en": "Dubai Land Department", "pricingtype_en": "Fee",
                    "servicefeescode": "DLD-1", "servicename_en": "Ejari Registration"})
    hits = lsp.search(str(path), "Land Department", ["ejari"])
    assert hits[0]["service_fees_code"] == "DLD-1" and hits[0]["amount_en"] == "100"
    assert lsp.entities(str(path)) == {"Dubai Land Department": 1}
