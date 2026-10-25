"""Step 3: match the extracted fields to a verified service record.

This is deliberately plain code, not AI: the fee, deadline rule and link the user
sees come from data/services.json, which the Data role builds from open data and
official service pages (with each source recorded).
"""
import json
from functools import lru_cache

from . import config


@lru_cache(maxsize=1)
def load() -> list[dict]:
    with open(config.DATA_DIR / "services.json", encoding="utf-8") as f:
        return json.load(f)["services"]


def _words(*values) -> set[str]:
    text = " ".join(str(v) for v in values if v).lower()
    return {w.strip(".,()/-") for w in text.split() if len(w) > 2}


def match(fields: dict) -> dict | None:
    """Return the best service record for these fields, or None if nothing fits."""
    emirate = fields.get("emirate")
    candidates = [
        s for s in load()
        if s["doc_type"] == fields.get("doc_type")
        # never send a Sharjah fine to a Dubai page: same emirate, or a federal (None) record
        and (not emirate or s.get("emirate") in (None, emirate))
    ]
    if not candidates:
        return None

    doc_words = _words(
        fields.get("issuing_authority"),
        fields.get("emirate"),
        fields.get("subject"),
        *fields.get("keywords", []),
    )

    def score(service: dict) -> int:
        s = len(doc_words & {k.lower() for k in service.get("match_keywords", [])})
        if fields.get("emirate") and service.get("emirate") == fields.get("emirate"):
            s += 3
        if service.get("emirate") is None:  # federal / any-emirate fallback
            s += 1
        return s

    best = max(candidates, key=score)
    record = dict(best)
    record["matched_item"] = match_item(best, doc_words)
    return record


def match_item(service: dict, doc_words: set[str]) -> dict | None:
    """Optional: find the specific violation/notice inside the service (e.g. which fine)."""
    items = service.get("items", [])
    scored = [(len(doc_words & {k.lower() for k in i.get("match_keywords", [])}), i) for i in items]
    scored = [x for x in scored if x[0] > 0]
    return max(scored, key=lambda x: x[0])[1] if scored else None
