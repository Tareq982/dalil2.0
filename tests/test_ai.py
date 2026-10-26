"""Checks the request we send to each AI provider and how we read its reply.
No real API calls: requests.post is replaced by a fake."""
import pytest

from app import ai, config


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload, self.status_code, self.text = payload, status, str(payload)

    def json(self):
        return self._payload


@pytest.fixture
def capture(monkeypatch):
    calls = {}

    def install(reply):
        def fake_post(url, headers=None, json=None, timeout=None):
            calls.update(url=url, headers=headers, body=json)
            return reply
        monkeypatch.setattr(ai.requests, "post", fake_post)
        return calls
    return install


def use(monkeypatch, provider, model):
    monkeypatch.setattr(config, "AI_PROVIDER", provider)
    monkeypatch.setattr(config, "AI_MODEL", model)
    monkeypatch.setattr(config, "AI_API_KEY", "test-key")


def test_gemini_request_and_reply(monkeypatch, capture):
    use(monkeypatch, "gemini", "gemini-3.5-flash-lite")
    calls = capture(FakeResponse({"candidates": [{"content": {"parts": [{"text": '{"ok": true}'}]}}]}))
    out = ai.ask("SYS", "hello", file=(b"img", "image/jpeg"))
    assert out == '{"ok": true}'
    assert calls["url"].endswith("/models/gemini-3.5-flash-lite:generateContent")
    assert calls["headers"]["x-goog-api-key"] == "test-key"
    parts = calls["body"]["contents"][0]["parts"]
    assert parts[0]["inlineData"]["mimeType"] == "image/jpeg" and parts[1]["text"] == "hello"
    assert calls["body"]["systemInstruction"]["parts"][0]["text"] == "SYS"


def test_gemini_skips_thought_parts(monkeypatch, capture):
    use(monkeypatch, "gemini", "m")
    capture(FakeResponse({"candidates": [{"content": {"parts": [
        {"text": "thinking...", "thought": True}, {"text": '{"a": 1}'}]}}]}))
    assert ai.parse_json(ai.ask("S", "t")) == {"a": 1}


def test_gemini_error_is_reported(monkeypatch, capture):
    use(monkeypatch, "gemini", "m")
    capture(FakeResponse({"error": {"message": "API key not valid"}}, status=400))
    with pytest.raises(ai.AIError, match="Gemini API error 400"):
        ai.ask("S", "t")


def test_claude_request_and_reply(monkeypatch, capture):
    use(monkeypatch, "claude", "claude-haiku-5-5")
    calls = capture(FakeResponse({"content": [{"type": "text", "text": '{"ok": true}'}]}))
    assert ai.ask("SYS", "hello", file=(b"%PDF", "application/pdf")) == '{"ok": true}'
    assert calls["headers"]["x-api-key"] == "test-key"
    assert calls["body"]["messages"][0]["content"][0]["type"] == "document"


def test_unsupported_file_type_rejected(monkeypatch):
    use(monkeypatch, "gemini", "m")
    with pytest.raises(ai.AIError, match="Unsupported file type"):
        ai.ask("S", "t", file=(b"x", "image/heic"))


def test_parse_json_handles_code_fences():
    assert ai.parse_json('```json\n{"x": 2}\n```') == {"x": 2}
