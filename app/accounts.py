"""Accounts and synced documents (saved across devices).

Privacy by design, enforced HERE on the server (not just in the browser):
- Only the fields in ALLOWED are ever stored. Anything else a client sends (names,
  reference or plate numbers, ID numbers, photos...) is dropped before saving.
- Passwords are stored as salted scrypt hashes (werkzeug), never as text.
- Users can delete their account and every saved document in one step.

Storage: one SQLite file (data/dalil.db by default, ignored by git). For a real launch
this would sit behind UAE PASS login and a managed database.
"""
import json
import re
import sqlite3
import time
from functools import wraps

from flask import Blueprint, g, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from . import config

bp = Blueprint("accounts", __name__, url_prefix="/api")

# field -> (type, max length). The only details Dalil keeps about a document.
ALLOWED = {
    "id": (str, 64),
    "kind": (str, 40),              # traffic_fine / visa_residency_notice / tenancy_contract
    "authority": (str, 120),        # e.g. "Dubai Police"
    "emirate": (str, 40),
    "subject": (str, 200),          # e.g. "Exceeding the speed limit"
    "amount_aed": (float, None),
    "issue_date": (str, 10),        # YYYY-MM-DD
    "date": (str, 10),              # deadline or reminder date, YYYY-MM-DD
    "date_is_reminder": (bool, None),
    "summary": (str, 600),          # the plain explanation sentence
    "answer_lang": (str, 5),
    "official_url": (str, 300),
    "service_id": (str, 60),
    "status": (str, 10),            # "open" or "paid"
    "saved_at": (str, 40),
}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_DOCS = 500


def clean(doc: dict) -> dict:
    """Keep only allowed, well-formed fields. This is the privacy filter."""
    out = {}
    for key, (kind, limit) in ALLOWED.items():
        value = doc.get(key)
        if value is None or value == "":
            continue
        try:
            if kind is float:
                value = float(value)
            elif kind is bool:
                value = bool(value)
            else:
                value = str(value)[:limit]
        except (TypeError, ValueError):
            continue
        if key in ("date", "issue_date") and not DATE.match(value):
            continue
        if key == "official_url" and not value.startswith("https://"):
            continue
        if key == "status" and value not in ("open", "paid"):
            continue
        out[key] = value
    return out


# ---------------------------------------------------------------- database

def db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(config.DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS documents (
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                id TEXT NOT NULL,
                data TEXT NOT NULL,
                updated_at REAL NOT NULL,
                PRIMARY KEY (user_id, id));
        """)
    return g.db


@bp.teardown_app_request
def close_db(_exc):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def signed_in(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session or not db().execute(
                "SELECT 1 FROM users WHERE id = ?", (session["user_id"],)).fetchone():
            session.clear()
            return jsonify({"error": "Sign in first."}), 401
        return view(*args, **kwargs)
    return wrapper


def body() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


# ---------------------------------------------------------------- account

@bp.post("/signup")
def signup():
    data = body()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    if not EMAIL.match(email) or len(email) > 200:
        return jsonify({"error": "Enter a valid email address."}), 400
    if len(password) < 8:
        return jsonify({"error": "Use a password of at least 8 characters."}), 400
    try:
        cur = db().execute("INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
                           (email, generate_password_hash(password), time.time()))
        db().commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "An account with this email already exists. Sign in instead."}), 409
    session.clear()
    session["user_id"], session["email"] = cur.lastrowid, email
    session.permanent = True
    return jsonify({"email": email})


@bp.post("/login")
def login():
    data = body()
    email = str(data.get("email", "")).strip().lower()
    row = db().execute("SELECT id, password_hash FROM users WHERE email = ?", (email,)).fetchone()
    if not row or not check_password_hash(row["password_hash"], str(data.get("password", ""))):
        time.sleep(0.4)  # slow down password guessing a little
        return jsonify({"error": "Email or password is wrong."}), 401
    session.clear()
    session["user_id"], session["email"] = row["id"], email
    session.permanent = True
    return jsonify({"email": email})


@bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@bp.get("/me")
def me():
    # The account may have been deleted from another device: then this device is signed out too.
    if "user_id" in session and not db().execute("SELECT 1 FROM users WHERE id = ?", (session["user_id"],)).fetchone():
        session.clear()
    return jsonify({"email": session.get("email")})


@bp.delete("/account")
@signed_in
def delete_account():
    db().execute("DELETE FROM users WHERE id = ?", (session["user_id"],))  # documents go too (cascade)
    db().commit()
    session.clear()
    return jsonify({"ok": True})


# ---------------------------------------------------------------- documents

@bp.get("/documents")
@signed_in
def list_documents():
    rows = db().execute("SELECT data FROM documents WHERE user_id = ? ORDER BY updated_at",
                        (session["user_id"],)).fetchall()
    return jsonify([json.loads(r["data"]) for r in rows])


@bp.post("/documents")
@signed_in
def save_documents():
    """Save one document, or a list of them (used to move this phone's documents into the account)."""
    data = request.get_json(silent=True)
    docs = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
    count = db().execute("SELECT COUNT(*) FROM documents WHERE user_id = ?", (session["user_id"],)).fetchone()[0]
    saved = []
    for raw in docs[:MAX_DOCS]:
        doc = clean(raw if isinstance(raw, dict) else {})
        if not doc.get("id"):
            continue
        exists = db().execute("SELECT 1 FROM documents WHERE user_id = ? AND id = ?",
                              (session["user_id"], doc["id"])).fetchone()
        if not exists and count >= MAX_DOCS:
            break
        db().execute("INSERT OR REPLACE INTO documents (user_id, id, data, updated_at) VALUES (?, ?, ?, ?)",
                     (session["user_id"], doc["id"], json.dumps(doc, ensure_ascii=False), time.time()))
        count += 0 if exists else 1
        saved.append(doc)
    db().commit()
    return jsonify(saved)


@bp.delete("/documents/<doc_id>")
@signed_in
def delete_document(doc_id):
    db().execute("DELETE FROM documents WHERE user_id = ? AND id = ?", (session["user_id"], doc_id))
    db().commit()
    return jsonify({"ok": True})
