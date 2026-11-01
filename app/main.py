"""Web server: the app page, its files, and the JSON API it calls.

Run it with:   python -m app.main      then open http://localhost:8000

Front-end files live in web/ and are served under /web/ (web/js/scan.js -> /web/js/scan.js).
"""
import json
import logging

from datetime import timedelta

from flask import Flask, jsonify, request, send_from_directory

from . import accounts, ai, catalog, chat, checks, config, langdetect, pipeline, scamcheck, stats

app = Flask(__name__, static_folder=str(config.WEB_DIR), static_url_path="/web")
app.json.sort_keys = False  # keep the language order from config.LANGUAGES
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB upload limit
app.config.update(
    SECRET_KEY=config.SECRET_KEY,
    SESSION_COOKIE_HTTPONLY=True,      # page scripts can't read the login cookie
    SESSION_COOKIE_SAMESITE="Lax",     # other sites can't make signed-in requests
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
)
app.register_blueprint(accounts.bp)
log = logging.getLogger("dalil")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


@app.get("/")
def index():
    return send_from_directory(config.WEB_DIR, "index.html")


@app.get("/health")
def health():
    return {"ok": True, "mock_ai": config.MOCK_AI, "provider": config.AI_PROVIDER, "model": config.AI_MODEL,
            "number_check": dict(checks.COUNTS)}  # passed / retried / template since the server started


@app.get("/languages")
def languages():
    return jsonify(config.LANGUAGES)


@app.get("/services")
def services():
    """The verified service catalog, for the Services tab (#14)."""
    with open(config.DATA_DIR / "services.json", encoding="utf-8") as f:
        return jsonify(json.load(f)["services"])


@app.post("/analyze")
def analyze():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file was uploaded. Choose a photo or PDF and try again."}), 400
    data = file.read()  # kept in memory only, never saved
    try:
        result = pipeline.analyze(data, file.mimetype, request.form.get("lang", "en"))
    except ai.AIError as e:
        log.warning("analyze failed: %s", e)
        return jsonify({"error": str(e)}), 502
    outcome = "not_supported" if result.get("not_supported") else "fallback" if result.get("fallback") else "explained"
    stats.record("scan", (result.get("fields") or {}).get("doc_type"), result.get("language"), outcome,
                 result.get("number_check"))
    return jsonify(result)


@app.post("/simplify")
def simplify():
    """'Explain it simpler': the same facts, rewritten in very easy words, number-checked again.
    Only the non-sensitive details are accepted; the service is looked up here, not trusted from the browser."""
    data = request.get_json(silent=True) or {}
    lang = data.get("lang") if data.get("lang") in config.LANGUAGES else "en"
    raw = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    fields = {k: raw.get(k) for k in chat.DOC_FIELDS + ["key_points"] if raw.get(k) not in (None, "")}
    service = next((s for s in catalog.load() if s["id"] == data.get("service_id")), None)
    try:
        explanation, outcome = pipeline.explain_checked(
            fields, service, pipeline.days_until(fields.get("deadline_date")), lang, simple=True)
    except ai.AIError as e:
        log.warning("simplify failed: %s", e)
        return jsonify({"error": str(e)}), 502
    stats.record("simpler", fields.get("doc_type"), lang, outcome)
    return jsonify({"language": lang, "explanation": explanation, "number_check": outcome})


@app.post("/event")
def event():
    """Anonymous taps: thumbs up/down ("feedback") and "Send to family" ("share"). Nothing personal."""
    data = request.get_json(silent=True) or {}
    kind = data.get("kind")
    if kind not in ("feedback", "share"):
        return jsonify({"error": "Unknown event."}), 400
    outcome = ("yes" if data.get("helpful") else "no") if kind == "feedback" else None
    stats.record(kind, data.get("doc_type"), data.get("lang"), outcome)
    return jsonify({"ok": True})


@app.get("/stats")
def stats_page():
    return send_from_directory(config.WEB_DIR, "stats.html")


@app.get("/api/stats")
def stats_data():
    return jsonify(stats.summary())


@app.post("/check-message")
def check_message():
    """'Is this message real?': a photo/screenshot of an SMS, email or website, or its pasted text.
    The AI reads it; code checks every link against the official allow-list (app/scamcheck.py)."""
    file = request.files.get("file")
    text = request.form.get("text", "")
    lang = request.form.get("lang", "en")
    upload = (file.read(), file.mimetype) if file else None  # kept in memory only, never saved
    if not text.strip() and not (upload and upload[0]):
        return jsonify({"error": "Add a photo or screenshot of the message, or paste its text."}), 400
    try:
        result = scamcheck.check(text=text, file=upload, lang=lang)
    except ai.AIError as e:
        log.warning("check-message failed: %s", e)
        return jsonify({"error": str(e)}), 502
    stats.record("message", None, result.get("language"), result.get("verdict"))
    return jsonify(result)


@app.post("/chat")
def ask_dalil():
    """Follow-up questions about a scanned document (only its non-sensitive details are sent)."""
    data = request.get_json(silent=True) or {}
    messages = data.get("messages") or []
    # Answer in the language of the question (typed or spoken). If it can't be told
    # (e.g. "ok?"), keep the language the browser sent: the chat's current language.
    question = next((str(m.get("content", "")) for m in reversed(messages)
                     if isinstance(m, dict) and m.get("role") == "user"), "")
    lang = langdetect.detect(question) or (data.get("lang") if data.get("lang") in config.LANGUAGES else "en")
    try:
        answer = chat.ask(data.get("fields") or {}, data.get("service_id"), messages, config.LANGUAGES[lang])
    except ai.AIError as e:
        log.warning("chat failed: %s", e)
        return jsonify({"error": str(e)}), 502
    answer["language"] = lang  # the app labels the reply and sets its direction with this
    stats.record("chat", (data.get("fields") or {}).get("doc_type"), lang, "searched" if answer.get("searched") else "answered")
    return jsonify(answer)


if __name__ == "__main__":
    if config.MOCK_AI:
        log.warning("MOCK_AI is on (no API key for %s, or MOCK_AI=1): answers are fake.", config.AI_PROVIDER)
    else:
        log.info("Using %s (%s)", config.AI_PROVIDER, config.AI_MODEL)
    # debug stays off: the debugger must never be reachable from other devices
    app.run(host="0.0.0.0", port=config.PORT, debug=False)
