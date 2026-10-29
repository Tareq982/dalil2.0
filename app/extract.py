"""Step 2: read the photo and pull out structured fields.

The output shape below is the team's shared contract (see README "Extracted fields").
If you change it, update the README and catalog.py/explain.py in the same pull request.
"""
from . import ai, config

DOC_TYPES = ["traffic_fine", "visa_residency_notice", "tenancy_contract", "other"]

SYSTEM = f"""You read photos of official UAE documents (Arabic and/or English) for a guidance app.
Return ONLY a JSON object, no other text, with exactly these keys:

{{
  "doc_type": one of {DOC_TYPES},
  "emirate": "Dubai" | "Abu Dhabi" | "Sharjah" | "Ajman" | "Umm Al Quwain" | "Ras Al Khaimah" | "Fujairah" | null,
  "issuing_authority": string or null,          // e.g. "Dubai Police", "RTA", "GDRFA", "ICP", "Dubai Land Department"
  "reference_number": string or null,
  "amount_aed": number or null,                 // total amount due, as printed
  "issue_date": "YYYY-MM-DD" or null,
  "deadline_date": "YYYY-MM-DD" or null,        // only if a date is printed on the document
  "subject": string or null,                    // the violation, notice reason, or contract subject, in English
  "key_points": [string],                       // up to 5 short facts in English, copied from the document
  "keywords": [string],                         // up to 8 lowercase English words useful for matching a service
  "document_language": "ar" | "en" | "mixed" | "other",
  "readable": true | false,                     // false if blurry, cut off, or not a document
  "confidence": number between 0 and 1          // how sure you are about doc_type AND the key fields
}}

Rules:
- Copy values exactly as printed. Never invent a value: use null if it is not visible.
- Do not include personal data such as names, Emirates ID, passport or phone numbers.
- If the image is not an official document, set doc_type "other", readable false, confidence 0."""


MOCK_FIELDS = {
    "doc_type": "traffic_fine",
    "emirate": "Dubai",
    "issuing_authority": "Dubai Police",
    "reference_number": "MOCK-000123",
    "amount_aed": 600,
    "issue_date": "2026-10-20",
    "deadline_date": None,
    "subject": "Exceeding the speed limit",
    "key_points": ["Speed camera violation", "Vehicle plate shown on fine"],
    "keywords": ["speed", "radar", "traffic", "fine", "dubai", "police"],
    "document_language": "mixed",
    "readable": True,
    "confidence": 0.9,
}


def extract(data: bytes, media_type: str) -> dict:
    if config.MOCK_AI:
        return dict(MOCK_FIELDS)

    fields = ai.ask_json(SYSTEM, "Read this document and return the JSON.", file=(data, media_type), max_tokens=1500)
    return normalise(fields)


def normalise(fields: dict) -> dict:
    """Make sure every key exists with a sensible type, whatever the model returned."""
    out = {k: fields.get(k) for k in MOCK_FIELDS}
    if out["doc_type"] not in DOC_TYPES:
        out["doc_type"] = "other"
    out["key_points"] = [str(x) for x in (out["key_points"] or [])][:5]
    out["keywords"] = [str(x).lower() for x in (out["keywords"] or [])][:8]
    out["readable"] = bool(out["readable"])
    try:
        out["confidence"] = max(0.0, min(1.0, float(out["confidence"] or 0)))
    except (TypeError, ValueError):
        out["confidence"] = 0.0
    try:
        out["amount_aed"] = float(out["amount_aed"]) if out["amount_aed"] is not None else None
    except (TypeError, ValueError):
        out["amount_aed"] = None
    return out
