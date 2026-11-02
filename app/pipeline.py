"""The whole flow in one function: photo in -> grounded explanation out.

    extract (AI)  ->  catalog.match (code + data)  ->  explain (AI)  ->  number check (code)  ->  safety footer (code)

Nothing is written to disk: the file bytes live only in memory for this request.
"""
import logging
from datetime import date

from . import catalog, checks, config, explain, extract, safety, scamcheck

log = logging.getLogger("dalil")


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
    fields = trust_screenshot(fields)
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
    result["explanation"], result["number_check"] = explain_checked(fields, service, days_left, lang)
    return result


def trust_screenshot(fields: dict) -> dict:
    """A screenshot of an official app or website is fine; one of any other website is not.

    The AI says whether it saw a web address; plain code decides whether that address is an
    official government site (the same allow-list as "Is this message real?"). So a fake
    "pay your fine" page that looks official is never explained as a real fine."""
    address = fields.get("web_address")
    if address and fields.get("doc_type") != "other" and scamcheck.check_link(address)["status"] != "official":
        log.warning("screenshot from a non-official website (%s): not explained", address)
        fields = dict(fields, doc_type="other")
    return fields


def explain_checked(fields: dict, service: dict | None, days_left: int | None, lang: str,
                    simple: bool = False) -> tuple[dict, str]:
    """Explain, then check every number against the data (issue #20). Returns (explanation, outcome)."""
    language = config.LANGUAGES[lang]
    public = explain._public(service)  # exactly what the AI was shown
    text = explain.explain(fields, service, days_left, language, simple=simple)
    bad = checks.unsupported(text, fields, public, days_left)
    if not bad:
        checks.record("passed")
        return text, "passed"

    warning = (f"WARNING: your previous answer used these numbers that are NOT in DATA: {', '.join(bad)}. "
               "Write the answer again using only numbers that appear in DATA. If a fee, discount or date "
               "is not in DATA, don't mention a number for it: say to check the official link.")
    text = explain.explain(fields, service, days_left, language, warning=warning, simple=simple)
    still = checks.unsupported(text, fields, public, days_left)
    if not still:
        checks.record("retried", bad)
        return text, "retried"

    checks.record("template", still)
    return checks.template(fields, days_left, lang), "template"


def service_summary(service: dict | None) -> dict | None:
    """What the app shows about the matched official service (verified badge, link, law)."""
    if not service:
        return None
    keep = ["id", "service_name", "authority", "official_url", "verified", "last_checked",
            "source", "legal_basis", "fee_aed", "fee_note", "help"]
    return {k: service.get(k) for k in keep}
