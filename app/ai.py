"""One function to talk to the AI, whichever provider is set in .env (AI_PROVIDER).

    ai.ask(system, text, file=(bytes, media_type)) -> reply text

Supported: "gemini" (Google, has a free tier) and "claude" (Anthropic).
Plain HTTP with `requests`, so no extra SDKs to install.
"""
import base64
import json
import logging
import re

import requests

from . import config

IMAGE_TYPES = ("image/jpeg", "image/png", "image/webp", "image/gif")
PDF = "application/pdf"


log = logging.getLogger("dalil.ai")


class AIError(Exception):
    pass


class CutOff(AIError):
    """The reply hit the length limit before it was finished."""


def ask(system: str, text: str, file: tuple[bytes, str] | None = None, max_tokens: int = 1200) -> str:
    if file and file[1] not in IMAGE_TYPES + (PDF,):
        raise AIError(f"Unsupported file type: {file[1]}. Send a JPG, PNG, WEBP or PDF.")
    if config.AI_PROVIDER == "gemini":
        return _gemini(system, text, file, max_tokens)
    return _claude(system, text, file, max_tokens)


def ask_json(system: str, text: str, file: tuple[bytes, str] | None = None, max_tokens: int = 2000) -> dict:
    """Ask for a JSON object. If the reply is cut off or isn't JSON, try once more:
    with a bigger length limit, and a reminder to reply with JSON only."""
    try:
        return parse_json(ask(system, text, file, max_tokens))
    except CutOff:
        log.warning("AI reply was cut off at %s tokens, retrying with more room", max_tokens)
        return parse_json(ask(system, text, file, max_tokens * 2))
    except AIError as e:
        if "did not return JSON" not in str(e) and "Could not parse" not in str(e):
            raise
        log.warning("AI reply was not JSON (%s), retrying once", e)
        reminder = text + "\n\nReply with ONLY the JSON object: start with { and end with }. No other text."
        return parse_json(ask(system, reminder, file, max_tokens))


def parse_json(text: str) -> dict:
    """Pull the first JSON object out of a reply (tolerates ```json fences)."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise AIError(f"The model did not return JSON. It said: {text[:200]!r}")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as e:
        raise AIError(f"Could not parse model JSON: {e}") from e


def _b64(data: bytes) -> str:
    return base64.standard_b64encode(data).decode("ascii")


# ---------------------------------------------------------------- Gemini

def _gemini(system, text, file, max_tokens) -> str:
    parts = []
    if file:
        parts.append({"inlineData": {"mimeType": file[1], "data": _b64(file[0])}})
    parts.append({"text": text})
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{config.AI_MODEL}:generateContent",
        headers={"x-goog-api-key": config.AI_API_KEY, "content-type": "application/json"},
        json={
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": parts}],
            # Both our prompts ask for JSON; this makes Gemini return clean JSON.
            # Generous token limit: some Gemini models spend tokens "thinking" first.
            "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": max(max_tokens * 2, 4096)},
        },
        timeout=90,
    )
    if resp.status_code != 200:
        raise AIError(f"Gemini API error {resp.status_code}: {resp.text[:300]}")
    try:
        cand = resp.json()["candidates"][0]
        reply = "".join(p.get("text", "") for p in cand["content"]["parts"] if not p.get("thought")).strip()
    except (KeyError, IndexError) as e:
        raise AIError(f"Unexpected Gemini response: {resp.text[:300]}") from e
    if cand.get("finishReason") == "MAX_TOKENS":
        raise CutOff(f"The AI's answer was cut off at {max_tokens} tokens.")
    return reply


# ---------------------------------------------------------------- Claude

def _claude(system, text, file, max_tokens) -> str:
    content = []
    if file:
        kind = "document" if file[1] == PDF else "image"
        content.append({"type": kind, "source": {"type": "base64", "media_type": file[1], "data": _b64(file[0])}})
    content.append({"type": "text", "text": text})
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": config.AI_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": config.AI_MODEL,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": content}],
        },
        timeout=90,
    )
    if resp.status_code != 200:
        raise AIError(f"Claude API error {resp.status_code}: {resp.text[:300]}")
    body = resp.json()
    reply = "".join(p.get("text", "") for p in body.get("content", []) if p.get("type") == "text").strip()
    if body.get("stop_reason") == "max_tokens":
        raise CutOff(f"The AI's answer was cut off at {max_tokens} tokens.")
    if body.get("stop_reason") == "refusal":
        raise AIError("The AI declined to read this document. Try a clearer photo of an official document.")
    return reply
