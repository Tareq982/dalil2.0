"""Look up official fees in the Dubai Government Service Prices open dataset (Dubai Pulse).

1. Download the dataset CSV from:
   https://www.dubaipulse.gov.ae/data/dof-pricing/dof_government_service_prices-open
2. Run, for example:
   python tools/lookup_service_prices.py prices.csv "Land Department" ejari tenancy
   python tools/lookup_service_prices.py prices.csv "Roads And Transport" fine
   python tools/lookup_service_prices.py prices.csv "Dubai Police" "knowledge"

Arguments: the CSV file, part of the government entity name, then keywords that must
ALL appear in the service or fee name (case does not matter). Copy what you find into
data/services.json and record the row's service_fees_code in data/sources.md.
"""
import csv
import sys

COLUMNS = ["service_fees_code", "government_entity_en", "service_name_en", "fee_name_en",
           "amount_en", "pricing_type_en", "fee_status_en"]


def search(path: str, entity: str, keywords: list[str]) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if rows and "government_entity_en" not in rows[0]:
        raise SystemExit(f"Unexpected columns: {list(rows[0])[:8]}... Is this the Service Prices CSV?")
    entity, keywords = entity.lower(), [k.lower() for k in keywords]
    out = []
    for r in rows:
        if entity not in (r.get("government_entity_en") or "").lower():
            continue
        text = f"{r.get('service_name_en', '')} {r.get('fee_name_en', '')}".lower()
        if all(k in text for k in keywords):
            out.append({c: (r.get(c) or "").strip() for c in COLUMNS})
    return out


def main(argv: list[str]) -> None:
    if len(argv) < 3:
        print(__doc__)
        raise SystemExit(1)
    matches = search(argv[1], argv[2], argv[3:])
    for m in matches:
        print(f"[{m['service_fees_code']}] {m['government_entity_en']} | {m['service_name_en']} | "
              f"{m['fee_name_en']} | {m['amount_en']} | {m['pricing_type_en']} | {m['fee_status_en']}")
    print(f"\n{len(matches)} matching fee rows")


if __name__ == "__main__":
    main(sys.argv)
