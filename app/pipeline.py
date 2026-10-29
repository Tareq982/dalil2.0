"""The whole flow in one function: photo in -> grounded explanation out.

    extract (AI)  ->  catalog.match (code + data)  ->  explain (AI)  ->  safety footer (code)

Nothing is written to disk: the file bytes live only in memory for this request.
"""
from datetime import date

from . import catalog, config, explain, extract, safety


def days_until(deadline: str | None) -> int | None:
    if not deadline:
        return None
    try:
        return (date.fromisoformat(deadline) - date.today()).days
    except ValueError:
        return None


def analyze(data: bytes, media_type: str, lang: str = "en") -> dict:
    lang = lang if lang in config.LANGUAGES else "en"

    fields = extract.extract(data, media_type)
    service = catalog.match(fields)
    conf = safety.overall_confidence(fields, service)
    footer = safety.footer(lang, conf, service)

    result = {
        "language": lang,
        "fields": fields,
        "service_id": (service or {}).get("id"),
        "service": service_summary(service),
        "confidence": conf,
        "footer": footer,
        "mock": config.MOCK_AI,
    }

    if fields.get("doc_type") == "other" and fields.get("readable"):
        # Readable, but not a document Dalil supports (receipt, scam text message...)
        result["fallback"] = safety.text(lang)["not_supported"]
        result["not_supported"] = True
        return result

    if safety.level(conf) == 2:  # too unsure: don't guess
        result["fallback"] = safety.text(lang)["fallback"]
        return result

    days_left = days_until(fields.get("deadline_date"))
    result["days_left"] = days_left
    result["explanation"] = explain.explain(fields, service, days_left, config.LANGUAGES[lang])
    return result


def service_summary(service: dict | None) -> dict | None:
    """What the app shows about the matched official service (verified badge, link, law)."""
    if not service:
        return None
    keep = ["id", "service_name", "authority", "official_url", "verified", "last_checked",
            "source", "legal_basis", "fee_aed", "fee_note"]
    return {k: service.get(k) for k in keep}
