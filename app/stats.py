"""Anonymous usage counts for the /stats page: is Dalil used, and does it help?

What is stored, per event: the time, what happened (a scan, a message check, a chat
question, a thumbs up/down, a "simpler" or "share" tap), the document type, the answer
language and the result (for example "explained" or "dont_pay").

Never stored: photos, text, names, reference/plate/ID numbers, accounts, IP addresses,
or anything else that could identify a person. Counting must never break the app, so
every error here is logged and ignored.
"""
import logging
import sqlite3
import time
from contextlib import closing

from . import config

log = logging.getLogger("dalil")

KINDS = {"scan", "message", "chat", "feedback", "simpler", "share", "find", "open_official", "paid"}
DOC_TYPES = {"traffic_fine", "visa_residency_notice", "tenancy_contract", "other"}


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(config.DB_PATH, timeout=5)
    con.execute("""CREATE TABLE IF NOT EXISTS events (
        ts REAL NOT NULL, kind TEXT NOT NULL, doc_type TEXT, lang TEXT, outcome TEXT, detail TEXT)""")
    return con


def _clean(value, allowed=None, limit=30):
    if value is None or value == "":
        return None
    value = str(value)[:limit]
    return value if allowed is None or value in allowed else None


def record(kind: str, doc_type=None, lang=None, outcome=None, detail=None) -> None:
    if kind not in KINDS:
        return
    row = (time.time(), kind, _clean(doc_type, DOC_TYPES), _clean(lang, set(config.LANGUAGES)),
           _clean(outcome), _clean(detail))
    try:
        with closing(_connect()) as con:
            con.execute("INSERT INTO events (ts, kind, doc_type, lang, outcome, detail) VALUES (?, ?, ?, ?, ?, ?)", row)
            con.commit()
    except sqlite3.Error as e:
        log.warning("stats not saved: %s", e)


def _count(con, sql, *args) -> dict:
    return {k or "unknown": n for k, n in con.execute(sql, args).fetchall()}


def targets(con) -> dict:
    """The challenge's two targets, measured inside the app.

    discovery: seconds from asking (tapping Explain, Find or Check) to opening the official service.
    adoption: share of answers (explained documents + services found) where the person went on
    to open the official service. Each answer counts at most once (the app sends one event)."""
    secs = sorted(float(r[0]) for r in con.execute(
        "SELECT detail FROM events WHERE kind = 'open_official' AND outcome IN ('scan', 'find') AND detail IS NOT NULL"))
    answers = con.execute("SELECT COUNT(*) FROM events WHERE (kind = 'scan' AND outcome = 'explained') "
                          "OR (kind = 'find' AND outcome = 'matched')").fetchone()[0]
    opened = con.execute("SELECT COUNT(*) FROM events WHERE kind = 'open_official' AND outcome IN ('scan', 'find')").fetchone()[0]
    median = None
    if secs:
        mid = len(secs) // 2
        median = round(secs[mid] if len(secs) % 2 else (secs[mid - 1] + secs[mid]) / 2, 1)
    return {"median_seconds_to_official": median, "timed": len(secs), "answers": answers, "opened_official": opened,
            "adoption_rate": round(min(1.0, opened / answers), 3) if answers else None,
            "marked_paid": con.execute("SELECT COUNT(*) FROM events WHERE kind = 'paid'").fetchone()[0]}


def summary() -> dict:
    try:
        with closing(_connect()) as con:
            by = lambda col, kind: _count(con, f"SELECT {col}, COUNT(*) FROM events WHERE kind = ? GROUP BY {col} ORDER BY 2 DESC", kind)
            first = con.execute("SELECT MIN(ts) FROM events").fetchone()[0]
            totals = _count(con, "SELECT kind, COUNT(*) FROM events GROUP BY kind")
            votes = _count(con, "SELECT outcome, COUNT(*) FROM events WHERE kind = 'feedback' GROUP BY outcome")
            return {
                "since": time.strftime("%Y-%m-%d", time.localtime(first)) if first else None,
                "totals": {k: totals.get(k, 0) for k in sorted(KINDS)},
                "scans_by_type": by("doc_type", "scan"),
                "scans_by_language": by("lang", "scan"),
                "scan_results": by("outcome", "scan"),
                "number_check": _count(con, "SELECT detail, COUNT(*) FROM events WHERE kind = 'scan' "
                                            "AND detail IS NOT NULL GROUP BY detail ORDER BY 2 DESC"),
                "helpful": {"yes": votes.get("yes", 0), "no": votes.get("no", 0)},
                "message_verdicts": by("outcome", "message"),
                "chat_by_language": by("lang", "chat"),
                "find_results": by("outcome", "find"),
                "targets": targets(con),
            }
    except sqlite3.Error as e:
        log.warning("stats not read: %s", e)
        return {"since": None, "totals": {k: 0 for k in sorted(KINDS)}, "error": "Stats are not available right now."}
