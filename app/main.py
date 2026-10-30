"""Web server: the app page, its files, and the JSON API it calls.

Run it with:   python -m app.main      then open http://localhost:8000

Front-end files live in web/ and are served under /web/ (web/js/scan.js -> /web/js/scan.js).
"""
import json
import logging

from datetime import timedelta

from flask import Flask, jsonify, request, send_from_directory

from . import accounts, ai, config, pipeline

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
    return {"ok": True, "mock_ai": config.MOCK_AI, "provider": config.AI_PROVIDER, "model": config.AI_MODEL}


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
    return jsonify(result)


if __name__ == "__main__":
    if config.MOCK_AI:
        log.warning("MOCK_AI is on (no API key for %s, or MOCK_AI=1): answers are fake.", config.AI_PROVIDER)
    else:
        log.info("Using %s (%s)", config.AI_PROVIDER, config.AI_MODEL)
    # debug stays off: the debugger must never be reachable from other devices
    app.run(host="0.0.0.0", port=config.PORT, debug=False)
