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


# ---- the real downloaded open datasets (data/open/)

def test_real_price_list_finds_official_fee_codes_in_arabic():
    path = str(config.DATA_DIR / "open" / "dubai_government_service_prices.csv")
    codes = {r["service_fees_code"] for r in lsp.search(path, "Land Department", ["رسم تسجيل عقد ايجار"])}
    assert "DLD-0020607" in codes
    for s in catalog.load():
        for code in s.get("official_fee_codes", []):
            if code.startswith(("DLD-", "GDRF-")):
                assert any(r["service_fees_code"] == code for r in lsp.load(path)), code


def test_open_data_stats_do_not_double_count_speeding():
    from tools import open_data_stats as ods
    stats = ods.traffic_fines()
    assert stats[2016]["uae_fines"] == 12_098_575
    assert 0.70 < stats[2016]["uae_speeding_share"] < 0.72
    assert ods.price_list()["by_type"]["Fine"] == 2377
    assert ods.vehicles_2023() == 672_163


# ---- mock test documents (samples/)

def test_every_expected_sample_file_exists():
    import csv as _csv
    rows = list(_csv.DictReader(open(config.ROOT / "samples" / "expected.csv", encoding="utf-8")))
    assert len(rows) >= 20
    for r in rows:
        assert (config.ROOT / "samples" / r["file"]).exists(), r["file"]
        if r["service_id"] not in ("", "none"):
            assert any(s["id"] == r["service_id"] for s in catalog.load()), r["service_id"]


def test_sample_scoring_rules():
    from tools.run_samples import check
    res = {"fields": {"amount_aed": 1000.0, "deadline_date": None, "emirate": "Abu Dhabi"},
           "service_id": None, "fallback": None}
    assert check("amount_aed", "1000", res) is True
    assert check("deadline_date", "none", res) is True        # nothing printed, nothing guessed
    assert check("service_id", "none", res) is True           # e.g. Sharjah: no wrong page
    assert check("emirate", "abu dhabi", res) is True
    assert check("fallback", "yes", res) is False
    assert check("amount_aed", "", res) is None               # empty = not scored
