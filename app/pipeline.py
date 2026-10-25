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
        "confidence": conf,
        "footer": footer,
        "mock": config.MOCK_AI,
    }

    if safety.level(conf) == 2:  # too unsure: don't guess
        result["fallback"] = safety.text(lang)["fallback"]
        return result

    days_left = days_until(fields.get("deadline_date"))
    result["days_left"] = days_left
    result["explanation"] = explain.explain(fields, service, days_left, config.LANGUAGES[lang])
    return result


def to_text(result: dict) -> str:
    """Format a result as a WhatsApp message (Twilio limit is 1600 characters)."""
    f = result["footer"]
    lines = []
    if result.get("fallback"):
        lines.append(result["fallback"])
    else:
        e = result["explanation"]
        lines += [f"📄 {e['what_it_is']}", "", f"💰 {e['cost']}", f"⏰ {e['deadline']}", ""]
        lines += [f"{i}. {step}" for i, step in enumerate(e["next_steps"], 1)]
    lines += ["", f"🔗 {f['link_label']}: {f['link']}", f"✅ {f['confidence_label']} · {f['source_label']}"]
    if f.get("unverified"):
        lines.append(f"⚠️ {f['unverified']}")
    lines.append(f"ℹ️ {f['disclaimer']}")
    text = "\n".join(lines)
    return text if len(text) <= 1600 else text[:1590] + "…"
