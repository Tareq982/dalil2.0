"""Look up official fees in the Dubai Government Service Prices open dataset (Dubai Pulse).

1. Download the dataset CSV from:
   https://www.dubaipulse.gov.ae/data/dof-pricing/dof_government_service_prices-open
   and save it as data/open/dubai_government_service_prices.csv
2. Run, for example:
   python tools/lookup_service_prices.py data/open/dubai_government_service_prices.csv "Land Department" "عقد ايجار"
   python tools/lookup_service_prices.py data/open/dubai_government_service_prices.csv "Residency" "تجديد تصريح اقامة"
   python tools/lookup_service_prices.py data/open/dubai_government_service_prices.csv "Dubai Police"

Most service and fee names in the file are in Arabic (even the "_en" columns), so search
with Arabic keywords. The downloaded export has NO amounts: use it for official fee codes,
the legal basis of each fee and counts, and take amounts from the official service pages.

Arguments: the CSV file, part of the government entity name, then keywords that must
ALL appear in the service or fee name (case does not matter). Copy what you find into
data/services.json and record the row's service fees code in data/sources.md.

To see which entity names exist:
   python tools/lookup_service_prices.py data/open/dubai_government_service_prices.csv --entities
"""
import csv
import sys
from collections import Counter

# The fields we show. The real CSV spells them without inner underscores
# (e.g. "feename_en") while the Dubai Pulse page lists "fee_name_en", so we
# match column names with underscores removed and accept either spelling.
COLUMNS = ["service_fees_code", "government_entity_en", "service_name_en", "fee_name_en",
           "amount_en", "pricing_type_en", "fee_status_en"]
# Optional columns: the downloaded file has Arabic names (most "_en" names are Arabic too)
# and the legal basis of each fee. Used when present.
OPTIONAL = ["service_name_ar", "fee_name_ar", "amount_ar", "legislation_en"]


def _norm(name: str) -> str:
    return name.strip().lower().replace("_", "").replace(" ", "")


def load(path: str) -> list[dict]:
    """Read the CSV and return rows keyed by our COLUMNS names, whatever the file's spelling."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = {_norm(h): h for h in (reader.fieldnames or [])}
        missing = [c for c in COLUMNS if _norm(c) not in header]
        if missing:
            raise SystemExit(f"Missing columns {missing}.\nColumns in this file: {sorted(header.values())}")
        cols = COLUMNS + [c for c in OPTIONAL if _norm(c) in header]
        return [{c: (row.get(header[_norm(c)]) or "").strip() for c in cols} for row in reader]


def search(path: str, entity: str, keywords: list[str]) -> list[dict]:
    entity, keywords = entity.lower(), [k.lower() for k in keywords]
    out = []
    for r in load(path):
        if entity not in r["government_entity_en"].lower():
            continue
        text = " ".join(r.get(k, "") for k in ("service_name_en", "fee_name_en", "service_name_ar", "fee_name_ar")).lower()
        if all(k in text for k in keywords):
            out.append(r)
    return out


def entities(path: str) -> Counter:
    return Counter(r["government_entity_en"] for r in load(path))


def main(argv: list[str]) -> None:
    if len(argv) == 3 and argv[2] == "--entities":
        for name, n in entities(argv[1]).most_common():
            print(f"{n:5}  {name}")
        return
    if len(argv) < 3:
        print(__doc__)
        raise SystemExit(1)
    matches = search(argv[1], argv[2], argv[3:])
    for m in matches:
        amount = m["amount_en"] or m.get("amount_ar") or "(no amount in file)"
        print(f"[{m['service_fees_code']}] {m['government_entity_en']} | {m['fee_name_en']} | "
              f"{amount} | {m['pricing_type_en']} | {m.get('legislation_en', '')[:90]}")
    print(f"\n{len(matches)} matching fee rows")
    if not matches:
        print("Tip: run with --entities to see the exact entity names in this file.")


if __name__ == "__main__":
    main(sys.argv)
