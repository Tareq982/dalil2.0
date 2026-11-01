"""Ask Dalil answers in the language of the question (issue #16). No real API calls."""
import pytest

from app import config, langdetect
from app.main import app


@pytest.mark.parametrize("text, lang", [
    ("Where can I pay this fine?", "en"),
    ("أين يمكنني دفع هذه المخالفة؟", "ar"),
    ("هل يمكنني الدفع بالتقسيط؟", "ar"),
    ("میں یہ جرمانہ کہاں ادا کر سکتا ہوں؟", "ur"),
    ("کیا میں قسطوں میں ادائیگی کر سکتا ہوں؟", "ur"),
    ("मैं इसका भुगतान कहाँ कर सकता हूँ?", "hi"),
    ("আমি কোথায় এটা পরিশোধ করতে পারি?", "bn"),
    ("ഇത് എവിടെ അടയ്ക്കാം?", "ml"),
    ("Saan ko po ito mababayaran?", "tl"),
    ("Pwede ko bang bayaran nang hulugan ang multa?", "tl"),
    ("How much is the fine po?", "en"),            # one Tagalog word in an English question
    ("RTA ka fine kitna hai? मुझे बताइए", "hi"),     # mostly Devanagari letters
])
def test_detects_each_language(text, lang):
    assert langdetect.detect(text) == lang


@pytest.mark.parametrize("text", ["", "ok?", "600", "AED 600 ??", "mujhe kitna dena hai"])
def test_unsure_returns_none(text):
    assert langdetect.detect(text) is None


def test_every_detected_language_is_offered():
    for code in ["en", "ar", "ur", "hi", "bn", "ml", "tl"]:
        assert code in config.LANGUAGES


def ask(question, lang="en", history=()):
    messages = list(history) + [{"role": "user", "content": question}]
    return app.test_client().post("/chat", json={"fields": {"doc_type": "traffic_fine"}, "lang": lang,
                                                 "messages": messages})


def test_chat_replies_in_the_language_of_the_question(monkeypatch):
    monkeypatch.setattr(config, "MOCK_AI", True)
    assert ask("میں یہ جرمانہ کہاں ادا کر سکتا ہوں؟", lang="en").json["language"] == "ur"
    assert ask("Saan ko po ito mababayaran?", lang="ar").json["language"] == "tl"


def test_chat_keeps_its_language_when_it_cant_tell(monkeypatch):
    monkeypatch.setattr(config, "MOCK_AI", True)
    assert ask("ok?", lang="ml").json["language"] == "ml"
    assert ask("ok?", lang="xx").json["language"] == "en"


def test_detected_language_reaches_the_ai(monkeypatch):
    seen = {}
    monkeypatch.setattr(config, "MOCK_AI", False)
    monkeypatch.setattr("app.chat.ask", lambda fields, sid, messages, language: seen.setdefault("lang", language)
                        and {"answer": "ok", "sources": [], "searched": False, "live": False})
    ask("আমি কোথায় এটা পরিশোধ করতে পারি?", lang="en")
    assert seen["lang"] == "Bengali"
