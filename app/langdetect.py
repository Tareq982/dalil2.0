"""Which of Dalil's languages is this question written in? (issue #16)

Used by Ask Dalil so a person can just type or speak in their own language and get the
answer back in that language, whatever language the document was explained in.

No AI and no extra package: each language has its own alphabet, so counting letters is
enough, with two small extra checks:
- Arabic and Urdu share an alphabet. Urdu uses some letters Arabic doesn't (ٹ ڈ ڑ ں ے ہ ک ی...)
  and Arabic uses some Urdu doesn't (ة ي ك ى...), so we count both kinds.
- English and Tagalog share an alphabet, so we count common little words of each.

Returns a code from config.LANGUAGES, or None when it can't tell (for example "ok?",
a number, or Hindi/Urdu typed in English letters). Then the chat keeps its current
language, and the AI is still told to reply in the language the person writes in.
"""
import re

# (code, first letter, last letter) of each alphabet's Unicode block
SCRIPTS = [
    ("hi", "ऀ", "ॿ"),   # Devanagari
    ("bn", "ঀ", "৿"),   # Bengali
    ("ml", "ഀ", "ൿ"),   # Malayalam
    ("arabic", "؀", "ۿ"),  # Arabic and Urdu
    ("latin", "a", "z"),          # English and Tagalog (text is lower-cased first)
]

URDU_ONLY = set("ٹڈڑںےۓہھکگچپژیۂۃ")
ARABIC_ONLY = set("ةيكىه")

TAGALOG_WORDS = {
    "ang", "ng", "mga", "ko", "mo", "ba", "po", "opo", "paano", "saan", "magkano", "ito", "iyan", "yan",
    "kung", "hindi", "ako", "ano", "kailan", "bakit", "pwede", "puwede", "lang", "naman", "yung", "akin",
    "siya", "nila", "kami", "tayo", "natin", "namin", "kayo", "sa", "na", "wala", "meron", "dapat",
    "kailangan", "magbayad", "bayaran", "babayaran", "multa", "salamat", "ilang", "araw", "nito", "kong",
}
ENGLISH_WORDS = {
    "the", "is", "are", "what", "how", "can", "i", "do", "does", "to", "my", "when", "where", "of", "this",
    "it", "you", "if", "will", "should", "much", "need", "have", "be", "in", "for", "and", "why", "which",
    "there", "or", "not", "me", "an", "about", "pay", "late", "with", "please",
}


def detect(text: str) -> str | None:
    text = str(text or "").lower()
    counts = {name: 0 for name, _, _ in SCRIPTS}
    for ch in text:
        for name, first, last in SCRIPTS:
            if first <= ch <= last:
                counts[name] += 1
                break
    # People often mix English words ("RTA", "fine", "AED") into their own script,
    # so any other alphabet wins over Latin letters.
    native, native_letters = max(((k, v) for k, v in counts.items() if k != "latin"), key=lambda kv: kv[1])
    script, letters = (native, native_letters) if native_letters >= 2 else ("latin", counts["latin"])
    if letters < 2:
        return None
    if script == "arabic":
        urdu = sum(ch in URDU_ONLY for ch in text)
        arabic = sum(ch in ARABIC_ONLY for ch in text)
        return "ur" if urdu > arabic else "ar"
    if script == "latin":
        words = re.findall(r"[a-z]+", text)
        tagalog = sum(w in TAGALOG_WORDS for w in words)
        english = sum(w in ENGLISH_WORDS for w in words)
        if tagalog > english:
            return "tl"
        return "en" if english else None
    return script
