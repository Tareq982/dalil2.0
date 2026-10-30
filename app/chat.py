"""Ask Dalil: a chat about the scanned document (issue #19).

Grounded and safe by design:
- The AI gets only the non-sensitive details of the document (never the photo, names,
  reference/plate/ID numbers) plus the matched official service from OUR verified catalog
  (looked up here on the server, not trusted from the browser).
- For anything not in that data (where to pay, instalments, late rules...) it can search the
  web LIVE, but only on official UAE government websites (OFFICIAL_SITES). Every answer
  returns the official pages it used as sources.
- Rules: no legal advice, never ask for card numbers/passwords/OTP/ID, only official payment
  channels, say "I'm not sure" instead of guessing.

Live search needs Claude (AI_PROVIDER=claude). With Gemini or in mock mode the chat still
works, answering from the document and catalog only.
"""
import json
import re
from datetime import date

import requests

from . import catalog, config
from .ai import AIError

# Only these sites can be searched (subdomains included, e.g. www.rta.ae).
OFFICIAL_SITES = [
    "u.ae", "rta.ae", "dubaipolice.gov.ae", "adpolice.gov.ae", "shjpolice.gov.ae", "moi.gov.ae",
    "tamm.abudhabi", "icp.gov.ae", "gdrfad.gov.ae", "dubailand.gov.ae", "mohre.gov.ae",
    "dubai.ae", "wam.ae", "mediaoffice.ae", "mediaoffice.abudhabi", "bayanat.ae", "dubaipulse.gov.ae",
]

# The only document details the chat ever sees (same spirit as the accounts allow-list).
DOC_FIELDS = ["doc_type", "emirate", "issuing_authority", "subject", "amount_aed", "issue_date", "deadline_date"]
SERVICE_FIELDS = ["authority", "service_name", "official_url", "fee_aed", "fee_note", "deadline_rule",
                  "next_steps", "verified", "last_checked", "legal_basis"]

MAX_TURNS = 12
MAX_CHARS = 1000

SYSTEM = """You are Dalil, a calm and friendly guide for UAE residents who cannot easily read Arabic or English.
The person has scanned an official document. Answer their questions about it.

Answer in {language}, unless the person clearly writes in another language: then use theirs.
Use simple words. Keep answers short: 2-5 sentences, or up to 4 short bullet points.

Where facts come from, in this order:
1. DOCUMENT and OFFICIAL SERVICE below (checked data). Prefer these.
2. If the answer is not there (where to pay, instalments, late payment, disputes, required documents,
   opening hours...), use the web_search tool. It only searches official UAE government websites.
3. If you still don't know, say so plainly and point to the official service. Never guess.

Rules:
- Never invent amounts, dates, fees, discounts or rules.
- No legal advice. Don't say whether they should dispute or appeal; you may explain how the official
  process works and where to start it.
- Never ask for card numbers, passwords, OTP codes, Emirates ID or passport numbers. If they share
  one, tell them not to share it and not to send it to anyone.
- Payment only through official apps and websites. Warn that real authorities don't send payment
  links by SMS or WhatsApp with big discounts.
- Only help with this document and related UAE government services. Politely decline anything else.
- Don't write web addresses in your answer: the app shows the official sources as links under it.

Today is {today}.

DOCUMENT:
{document}

OFFICIAL SERVICE (from Dalil's verified catalog, may be null):
{service}"""


def context_for(fields: dict, service_id: str | None) -> tuple[dict, dict | None]:
    doc = {k: fields.get(k) for k in DOC_FIELDS if fields.get(k) not in (None, "")}
    service = next((s for s in catalog.load() if s["id"] == service_id), None) if service_id else None
    return doc, ({k: service.get(k) for k in SERVICE_FIELDS} if service else None)


def clean_messages(messages) -> list[dict]:
    """Plain text turns only, alternating, ending with the user. Long or odd input is trimmed."""
    out = []
    for m in (messages or [])[-MAX_TURNS:]:
        if not isinstance(m, dict) or m.get("role") not in ("user", "assistant"):
            continue
        text = str(m.get("content", "")).strip()[:MAX_CHARS]
        if not text:
            continue
        if out and out[-1]["role"] == m["role"]:
            out[-1]["content"] += "\n" + text
        else:
            out.append({"role": m["role"], "content": text})
    while out and out[0]["role"] != "user":
        out.pop(0)
    if not out or out[-1]["role"] != "user":
        raise AIError("Ask a question first.")
    return out


URL = re.compile(r"\(?\s*(?:https?://\s*\S+|www\.\S+)\s*\)?")


def _official(url: str) -> bool:
    host = re.sub(r"^https?://", "", url or "").split("/")[0].lower()
    return any(host == d or host.endswith("." + d) for d in OFFICIAL_SITES)


def ask(fields: dict, service_id: str | None, messages: list, language: str) -> dict:
    """Returns {answer, sources: [{url, title}], searched: bool, live: bool}."""
    turns = clean_messages(messages)
    doc, service = context_for(fields or {}, service_id)

    if config.MOCK_AI:
        return {"answer": "[MOCK] I can answer questions about this document once an AI key is set. "
                          "For now, use the official link above.",
                "sources": [{"url": (service or {}).get("official_url") or "https://u.ae",
                             "title": (service or {}).get("service_name") or "UAE government portal"}],
                "searched": False, "live": False}

    system = SYSTEM.format(language=language, today=date.today().isoformat(),
                           document=json.dumps(doc, ensure_ascii=False, indent=1),
                           service=json.dumps(service, ensure_ascii=False, indent=1))
    if config.AI_PROVIDER != "claude":
        return _answer_without_search(system, turns, service)
    return _claude_with_search(system, turns, service)


def _post(payload: dict) -> requests.Response:
    return requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": config.AI_API_KEY, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json=payload, timeout=90)


def _claude_with_search(system: str, turns: list, service: dict | None) -> dict:
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 3,
              "allowed_domains": OFFICIAL_SITES,
              "user_location": {"type": "approximate", "country": "AE", "timezone": "Asia/Dubai"}}]
    messages = [dict(t) for t in turns]
    payload = {"model": config.AI_MODEL, "max_tokens": 1500, "system": system, "messages": messages, "tools": tools}
    resp = _post(payload)
    if resp.status_code == 400 and "web search" in resp.text.lower():
        # Web search switched off for this API account: still answer, from the checked data only.
        return _answer_without_search(system, turns, service)
    if resp.status_code != 200:
        raise AIError(f"Claude API error {resp.status_code}: {resp.text[:300]}")
    body = resp.json()
    content = list(body.get("content", []))
    for _ in range(3):  # a long search turn can pause; send it back unchanged to continue
        if body.get("stop_reason") != "pause_turn":
            break
        resp = _post({**payload, "messages": messages + [{"role": "assistant", "content": content}]})
        if resp.status_code != 200:
            raise AIError(f"Claude API error {resp.status_code}: {resp.text[:300]}")
        body = resp.json()
        content += body.get("content", [])
    return _parse(content, service)


def _parse(content: list, service: dict | None) -> dict:
    texts, sources, searched = [], [], False
    for block in content:
        if block.get("type") == "server_tool_use":
            searched = True
        elif block.get("type") == "text":
            texts.append(block.get("text", ""))
            for c in block.get("citations") or []:
                if c.get("url") and _official(c["url"]):
                    sources.append({"url": c["url"], "title": c.get("title") or c["url"]})
    answer = re.sub(r"[ \t]{2,}", " ", URL.sub(" ", "".join(texts))).strip()
    if not answer:
        raise AIError("Dalil couldn't answer that. Try asking in a different way.")
    if service and service.get("official_url"):
        sources.append({"url": service["official_url"], "title": service.get("service_name") or "Official service"})
    seen, unique = set(), []
    for s in sources:
        if s["url"] not in seen:
            seen.add(s["url"])
            unique.append(s)
    return {"answer": answer, "sources": unique[:5], "searched": searched, "live": True}


def _answer_without_search(system: str, turns: list, service: dict | None) -> dict:
    from . import ai
    note = "\n\n(Live search is not available: answer only from DOCUMENT and OFFICIAL SERVICE.)"
    history = "\n".join(f"{t['role'].upper()}: {t['content']}" for t in turns)
    answer = ai.ask(system + note, history + "\nASSISTANT:", max_tokens=1200)
    out = _parse([{"type": "text", "text": answer}], service)
    out["live"] = False
    return out
