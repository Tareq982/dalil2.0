"""One function to talk to the AI, whichever provider is set in .env (AI_PROVIDER).

    ai.ask(system, text, file=(bytes, media_type)) -> reply text

Supported: "gemini" (Google, has a free tier) and "claude" (Anthropic).
Plain HTTP with `requests`, so no extra SDKs to install.
"""
import base64
import json
import re

import requests

from . import config

IMAGE_TYPES = ("image/jpeg", "image/png", "image/webp", "image/gif")
PDF = "application/pdf"


class AIError(Exception):
    pass


def ask(system: str, text: str, file: tuple[bytes, str] | None = None, max_tokens: int = 1200) -> str:
    if file and file[1] not in IMAGE_TYPES + (PDF,):
        raise AIError(f"Unsupported file type: {file[1]}. Send a JPG, PNG, WEBP or PDF.")
    if config.AI_PROVIDER == "gemini":
        return _gemini(system, text, file, max_tokens)
    return _claude(system, text, file, max_tokens)


def parse_json(text: str) -> dict:
    """Pull the first JSON object out of a reply (tolerates ```json fences)."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise AIError("The model did not return JSON.")
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
            "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": max(max_tokens, 4096)},
        },
        timeout=60,
    )
    if resp.status_code != 200:
        raise AIError(f"Gemini API error {resp.status_code}: {resp.text[:300]}")
    try:
        cand = resp.json()["candidates"][0]
        return "".join(p.get("text", "") for p in cand["content"]["parts"] if not p.get("thought")).strip()
    except (KeyError, IndexError) as e:
        raise AIError(f"Unexpected Gemini response: {resp.text[:300]}") from e


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
        timeout=60,
    )
    if resp.status_code != 200:
        raise AIError(f"Claude API error {resp.status_code}: {resp.text[:300]}")
    parts = resp.json().get("content", [])
    return "".join(p.get("text", "") for p in parts if p.get("type") == "text").strip()
