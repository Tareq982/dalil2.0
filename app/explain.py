"""Step 4: explain the document in the user's language, using ONLY the facts we give it."""
import json
import re

from . import ai, config

SYSTEM = """You help residents of the UAE who cannot easily read Arabic or English understand official documents.
Write in {language}. Use simple words and short sentences, as if explaining to a friend.

Use ONLY the facts in DATA. Never invent fees, dates, rules or links.
- If the fee is unknown, say to check the amount on the document and the official link.
- If the deadline is unknown, say the document does not show one and to check the official link soon.
- Do not give legal advice or say whether to dispute or appeal. You may say the official service explains how.
- Keep names of authorities and services in English (you may add a translation in brackets).
- Never write web addresses (URLs). The app shows the official link as a button; say "the official link" instead.
- Don't repeat personal details from the document (names, plate numbers, ID numbers).

Return ONLY a JSON object, all text in {language}:
{{
  "what_it_is": "1-2 sentences: what this document is and why they received it",
  "cost": "1 sentence: how much they need to pay, or that there is no fee shown",
  "deadline": "1 sentence: by when, and how many days are left if given",
  "next_steps": ["up to 3 short steps, the first one is the most important"],
  "suggested_questions": ["3 short follow-up questions this person is likely to ask next, e.g. about where to pay, instalments, what happens if late, or required documents"]
}}"""


def explain(fields: dict, service: dict | None, days_left: int | None, language: str) -> dict:
    if config.MOCK_AI:
        return mock(fields, service, days_left)

    data = {
        "document": fields,
        "matched_service": _public(service),
        "days_left_until_deadline": days_left,
    }
    text = "DATA:\n" + json.dumps(data, ensure_ascii=False, indent=2)
    # Non-Latin scripts (Malayalam, Bengali, Urdu...) need many more tokens for the same text
    out = ai.ask_json(SYSTEM.format(language=language), text, max_tokens=2500)
    steps = out.get("next_steps") or []
    return {
        "what_it_is": _no_urls(out.get("what_it_is", "")),
        "cost": _no_urls(out.get("cost", "")),
        "deadline": _no_urls(out.get("deadline", "")),
        "next_steps": [_no_urls(s) for s in steps][:3],
        "suggested_questions": [str(q)[:120] for q in (out.get("suggested_questions") or [])][:3],
    }


URL = re.compile(r"\(?\s*(?:https?://\s*\S+|www\.\S+)\s*\)?")


def _no_urls(text) -> str:
    """Remove web addresses from the AI's text: the official link is shown as a button."""
    return re.sub(r"\s{2,}", " ", URL.sub(" ", str(text))).replace(" .", ".").strip()


def _public(service: dict | None) -> dict | None:
    """Only pass the fields the model needs (keeps prompts small and focused)."""
    if not service:
        return None
    keep = ["authority", "service_name", "official_url", "fee_aed", "fee_note",
            "deadline_rule", "next_steps", "matched_item"]
    return {k: service.get(k) for k in keep}


def mock(fields: dict, service: dict | None, days_left: int | None) -> dict:
    amount = fields.get("amount_aed")
    return {
        "what_it_is": f"[MOCK] This is a {fields.get('doc_type', 'document').replace('_', ' ')} "
                      f"from {fields.get('issuing_authority') or 'a government authority'}: {fields.get('subject') or ''}.",
        "cost": f"[MOCK] The amount shown is AED {amount:g}." if amount else "[MOCK] No amount is shown.",
        "deadline": f"[MOCK] {days_left} days left." if days_left is not None else "[MOCK] No deadline is printed. Check the official link soon.",
        "next_steps": (service or {}).get("next_steps", ["Open the official website"])[:3],
        "suggested_questions": ["Where can I pay this?", "Can I pay in instalments?", "What happens if I pay late?"],
    }
