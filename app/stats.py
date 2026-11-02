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


# The timing test (/timing): the challenge's two targets, measured with real people.
# Each tester does one task WITHOUT Dalil (any phone, search engine or website) and a different
# task WITH Dalil; the order swaps for the next tester. The facilitator presses "Found it" when
# the tester opens the right official page, or "Gave up". A run stops itself at TIME_LIMIT.
TIME_LIMIT = 300  # seconds; giving up counts as the full 5 minutes
TARGETS = {"discovery_time_cut": 0.60, "adoption_increase": 0.45}  # from the challenge statement
CONDITIONS = ("without", "with")
TRIAL_TASKS = [
    {"id": "dubai-visa", "service_id": "dubai-residency-notice",
     "task": "Your Dubai residence visa expires in 3 weeks. Find the official service to renew it."},
    {"id": "dubai-fine", "service_id": "dubai-traffic-fine",
     "task": "You got this parking fine from Dubai (show the sample fine). Find where to pay it officially."},
    {"id": "dubai-rent", "service_id": "dubai-tenancy-contract",
     "task": "You just rented a flat in Dubai. Find the official service to register the tenancy contract."},
    {"id": "abudhabi-fine", "service_id": "abu-dhabi-traffic-fine",
     "task": "You got a traffic fine in Abu Dhabi. Find where to pay it officially."},
    {"id": "sharjah-visa", "service_id": "federal-residency-notice",
     "task": "You live in Sharjah and your residence expires next month. Find the official service to renew it."},
]
TASK_IDS = {t["id"] for t in TRIAL_TASKS}


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(config.DB_PATH, timeout=5)
    con.execute("""CREATE TABLE IF NOT EXISTS events (
        ts REAL NOT NULL, kind TEXT NOT NULL, doc_type TEXT, lang TEXT, outcome TEXT, detail TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS trials (
        ts REAL NOT NULL, task TEXT NOT NULL, condition TEXT NOT NULL, seconds REAL NOT NULL, found INTEGER NOT NULL)""")
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


def record_trial(task, condition, seconds, found) -> bool:
    """One timing-test run. Returns False (and stores nothing) if a value is not allowed."""
    try:
        seconds = float(seconds)
    except (TypeError, ValueError):
        return False
    if task not in TASK_IDS or condition not in CONDITIONS or not 0 < seconds <= TIME_LIMIT + 5 \
            or not isinstance(found, bool):
        return False
    try:
        with closing(_connect()) as con:
            con.execute("INSERT INTO trials (ts, task, condition, seconds, found) VALUES (?, ?, ?, ?, ?)",
                        (time.time(), task, condition, round(min(seconds, TIME_LIMIT), 1), int(found)))
            con.commit()
        return True
    except sqlite3.Error as e:
        log.warning("trial not saved: %s", e)
        return False


def undo_last_trial() -> bool:
    """Removes the most recent run (for a mis-tap during the test)."""
    try:
        with closing(_connect()) as con:
            n = con.execute("DELETE FROM trials WHERE rowid = (SELECT rowid FROM trials ORDER BY ts DESC LIMIT 1)").rowcount
            con.commit()
        return n > 0
    except sqlite3.Error as e:
        log.warning("trial not removed: %s", e)
        return False


def _median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    mid = len(xs) // 2
    return round(xs[mid] if len(xs) % 2 else (xs[mid - 1] + xs[mid]) / 2, 1)


def trial_results(con) -> dict:
    """Without Dalil vs with Dalil, compared with the challenge's two targets.

    discovery time: median seconds until the tester opened the right official service
      (gave up or out of time = TIME_LIMIT). Cut = (without - with) / without. Target: 60%.
    adoption: share of runs where the tester reached the right official service.
      Increase = (with - without) / without. Target: +45%."""
    rows = con.execute("SELECT task, condition, seconds, found FROM trials ORDER BY ts").fetchall()
    arms = {}
    for c in CONDITIONS:
        runs = [r for r in rows if r[1] == c]
        found = sum(r[3] for r in runs)
        arms[c] = {"runs": len(runs), "found": found,
                   "median_seconds": _median([r[2] if r[3] else TIME_LIMIT for r in runs]),
                   "found_rate": round(found / len(runs), 3) if runs else None}
    w, d = arms["without"], arms["with"]
    cut = increase = None
    if w["median_seconds"] and d["median_seconds"] is not None:
        cut = round((w["median_seconds"] - d["median_seconds"]) / w["median_seconds"], 3)
    if w["found_rate"] and d["found_rate"] is not None:
        increase = round((d["found_rate"] - w["found_rate"]) / w["found_rate"], 3)
    per_task = {t["id"]: {c: sum(1 for r in rows if r[0] == t["id"] and r[1] == c) for c in CONDITIONS}
                for t in TRIAL_TASKS}
    last = rows[-1] if rows else None
    return {"without": w, "with": d, "discovery_time_cut": cut, "adoption_increase": increase,
            "targets": TARGETS, "time_limit": TIME_LIMIT, "runs": len(rows), "per_task": per_task,
            "last": {"task": last[0], "condition": last[1]} if last else None,
            "enough": w["runs"] >= 5 and d["runs"] >= 5,
            "met": {"discovery": cut is not None and cut >= TARGETS["discovery_time_cut"],
                    "adoption": increase is not None and increase >= TARGETS["adoption_increase"]}}


def trials() -> dict:
    try:
        with closing(_connect()) as con:
            return {"tasks": TRIAL_TASKS, **trial_results(con)}
    except sqlite3.Error as e:
        log.warning("trials not read: %s", e)
        return {"tasks": TRIAL_TASKS, "error": "The timing test results are not available right now."}


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
    return {"median_seconds_to_official": _median(secs), "timed": len(secs), "answers": answers, "opened_official": opened,
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
                "trial": trial_results(con),
            }
    except sqlite3.Error as e:
        log.warning("stats not read: %s", e)
        return {"since": None, "totals": {k: 0 for k in sorted(KINDS)}, "error": "Stats are not available right now."}
