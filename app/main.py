"""Web server: the upload page, the /analyze API and the WhatsApp webhook.

Run it with:   python -m app.main      then open http://localhost:8000
"""
import logging
import threading
from xml.sax.saxutils import escape

import requests
from flask import Flask, Response, jsonify, request, send_from_directory

from . import claude, config, pipeline

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB upload limit
log = logging.getLogger("dalil")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# ---------------------------------------------------------------- web

@app.get("/")
def index():
    return send_from_directory(config.WEB_DIR, "index.html")


@app.get("/health")
def health():
    return {"ok": True, "mock_ai": config.MOCK_AI, "model": config.CLAUDE_MODEL}


@app.get("/languages")
def languages():
    return jsonify(config.LANGUAGES)


@app.post("/analyze")
def analyze():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    data = file.read()  # kept in memory only, never saved
    try:
        result = pipeline.analyze(data, file.mimetype, request.form.get("lang", "en"))
    except claude.AIError as e:
        log.warning("analyze failed: %s", e)
        return jsonify({"error": str(e)}), 502
    return jsonify(result)


# ---------------------------------------------------------------- WhatsApp (Twilio)

# Language each WhatsApp user picked. In memory only: resets when the server restarts.
user_lang: dict[str, str] = {}
MENU_ORDER = list(config.LANGUAGES)  # 1 = en, 2 = ar, ...
NATIVE_NAMES = {"en": "English", "ar": "العربية", "hi": "हिन्दी", "ur": "اردو",
                "tl": "Tagalog", "bn": "বাংলা", "ml": "മലയാളം"}

WELCOME = (
    "👋 Hi, I'm Dalil. Send me a photo of an official document (fine, visa notice, lease) "
    "and I'll explain it in your language.\n\nChoose your language by replying with a number:\n"
    + "\n".join(f"{i}. {NATIVE_NAMES[c]}" for i, c in enumerate(MENU_ORDER, 1))
)


def twiml(message: str) -> Response:
    xml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{escape(message)}</Message></Response>'
    return Response(xml, mimetype="application/xml")


def pick_language(body: str) -> str | None:
    b = body.strip().lower()
    if b.isdigit() and 1 <= int(b) <= len(MENU_ORDER):
        return MENU_ORDER[int(b) - 1]
    for code, name in config.LANGUAGES.items():
        if b in (code, name.lower(), NATIVE_NAMES[code].lower()):
            return code
    return None


@app.post("/whatsapp")
def whatsapp():
    sender = request.form.get("From", "")
    body = request.form.get("Body", "")
    num_media = int(request.form.get("NumMedia", "0") or 0)

    if num_media == 0:
        lang = pick_language(body)
        if lang:
            user_lang[sender] = lang
            return twiml(f"✅ {NATIVE_NAMES[lang]}. 📸 Now send a photo of your document.")
        return twiml(WELCOME)

    media_url = request.form.get("MediaUrl0")
    media_type = request.form.get("MediaContentType0", "image/jpeg")
    lang = pick_language(body) or user_lang.get(sender, "en")

    # Twilio waits max ~15 s for a reply, and the AI can take longer.
    # So we answer "reading..." now and send the real answer from a background thread.
    if config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN:
        threading.Thread(target=process_and_send, args=(sender, media_url, media_type, lang), daemon=True).start()
        return twiml("⏳ Reading your document…")

    # Without Twilio credentials we can't send later, so try to answer within the time limit.
    return twiml(process(media_url, media_type, lang))


def process(media_url: str, media_type: str, lang: str) -> str:
    auth = (config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN) if config.TWILIO_ACCOUNT_SID else None
    try:
        r = requests.get(media_url, auth=auth, timeout=30)
        r.raise_for_status()
        return pipeline.to_text(pipeline.analyze(r.content, media_type, lang))
    except Exception as e:  # keep the user informed whatever went wrong
        log.warning("whatsapp processing failed: %s", e)
        return "Sorry, something went wrong reading that document. Please try again with a clear photo."
    finally:
        delete_twilio_media(media_url, auth)


def process_and_send(to: str, media_url: str, media_type: str, lang: str):
    text = process(media_url, media_type, lang)
    r = requests.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{config.TWILIO_ACCOUNT_SID}/Messages.json",
        data={"From": config.TWILIO_WHATSAPP_FROM, "To": to, "Body": text},
        auth=(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN),
        timeout=30,
    )
    if r.status_code >= 300:
        log.warning("twilio send failed %s: %s", r.status_code, r.text[:300])


def delete_twilio_media(media_url: str, auth):
    """Privacy: remove the photo from Twilio's servers once we've read it (best effort)."""
    if not auth or not media_url:
        return
    try:
        requests.delete(media_url, auth=auth, timeout=15)
    except requests.RequestException:
        pass


if __name__ == "__main__":
    if config.MOCK_AI:
        log.warning("MOCK_AI is on (no ANTHROPIC_API_KEY or MOCK_AI=1): answers are fake.")
    # debug stays off: the debugger must never be reachable through ngrok/Codespaces
    app.run(host="0.0.0.0", port=config.PORT, debug=False)
