"""Tiny wrapper around the Claude Messages API (plain HTTP, no SDK needed)."""
import base64
import json
import re

import requests

from . import config

API_URL = "https://api.anthropic.com/v1/messages"


class AIError(Exception):
    pass


def file_block(data: bytes, media_type: str) -> dict:
    """Turn uploaded bytes into a content block Claude can read (photo or PDF)."""
    b64 = base64.standard_b64encode(data).decode("ascii")
    if media_type == "application/pdf":
        return {"type": "document", "source": {"type": "base64", "media_type": media_type, "data": b64}}
    if media_type not in ("image/jpeg", "image/png", "image/gif", "image/webp"):
        raise AIError(f"Unsupported file type: {media_type}. Send a JPG, PNG, WEBP or PDF.")
    return {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}}


def ask(system: str, content: list, max_tokens: int = 1200) -> str:
    """Send one message to Claude and return the text of the reply."""
    resp = requests.post(
        API_URL,
        headers={
            "x-api-key": config.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": config.CLAUDE_MODEL,
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


def parse_json(text: str) -> dict:
    """Pull the first JSON object out of a reply (tolerates ```json fences)."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise AIError("The model did not return JSON.")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as e:
        raise AIError(f"Could not parse model JSON: {e}") from e
