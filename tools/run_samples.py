"""Run every mock document through Dalil and score it against samples/expected.csv (issue #6).

    python tools/run_samples.py                 # all samples, answers in English
    python tools/run_samples.py --lang ar,ml    # same documents, answers in Arabic and Malayalam
    python tools/run_samples.py --only fine_    # only files whose name contains "fine_"

Uses the real AI from your .env (each document = 2 AI calls). Prints a line per document,
then an accuracy table you can put on the feasibility slide, and saves both to
samples/results/.

How expected.csv is read: an empty cell = not scored; "none" = Dalil must NOT find a value
(e.g. no deadline printed, or no matching service); expect_fallback "yes" = Dalil should
refuse to guess.
"""
import argparse
import csv
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import config, pipeline  # noqa: E402
from app.ai import AIError  # noqa: E402

SAMPLES = ROOT / "samples"
MEDIA = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".pdf": "application/pdf"}
FIELDS = ["doc_type", "emirate", "amount_aed", "deadline_date", "service_id", "fallback"]


def check(field, expected, result):
    """Return True/False, or None when this field isn't scored for this document."""
    expected = (expected or "").strip()
    if not expected:
        return None
    f = result.get("fields", {})
    if field == "fallback":
        return bool(result.get("fallback")) == (expected.lower() == "yes")
    if field == "service_id":
        got = result.get("service_id")
        return got is None if expected == "none" else got == expected
    got = f.get(field)
    if expected == "none":
        return got in (None, "", 0)
    if field == "amount_aed":
        try:
            return got is not None and abs(float(got) - float(expected)) < 0.5
        except (TypeError, ValueError):
            return False
    if field == "emirate":
        return str(got or "").strip().lower() == expected.lower()
    return str(got or "").strip() == expected


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lang", default="en", help="answer languages, comma separated (default: en)")
    ap.add_argument("--only", default="", help="only run files whose name contains this text")
    ap.add_argument("--allow-mock", action="store_true", help="run even in mock mode (only to test this script)")
    args = ap.parse_args()

    if config.MOCK_AI and not args.allow_mock:
        sys.exit("Mock mode is on (no AI key in .env), so results would be fake. Add a key first.")

    with open(SAMPLES / "expected.csv", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if args.only in r["file"]]
    langs = [l.strip() for l in args.lang.split(",") if l.strip()]

    out_dir = SAMPLES / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    out_csv = out_dir / f"{stamp}_{config.AI_PROVIDER}_{'-'.join(langs)}.csv"
    records = []

    print(f"Dalil test run: {len(rows)} documents x {len(langs)} language(s), {config.AI_PROVIDER} ({config.AI_MODEL})\n")
    for lang in langs:
        for r in rows:
            path = SAMPLES / r["file"]
            media = MEDIA.get(path.suffix.lower(), "image/jpeg")
            t0 = time.time()
            error = ""
            try:
                result = pipeline.analyze(path.read_bytes(), media, lang)
            except (AIError, OSError) as e:
                result, error = {}, str(e)[:160]
            secs = time.time() - t0
            scores = {f: (check(f, r.get("expect_fallback" if f == "fallback" else f), result) if not error else False)
                      for f in FIELDS}
            fl = result.get("fields", {})
            rec = {
                "file": r["file"], "lang": lang, "seconds": round(secs, 1), "error": error,
                **{f"ok_{f}": scores[f] for f in FIELDS},
                "got_doc_type": fl.get("doc_type"), "got_emirate": fl.get("emirate"),
                "got_amount": fl.get("amount_aed"), "got_deadline": fl.get("deadline_date"),
                "got_service": result.get("service_id"), "got_fallback": bool(result.get("fallback")),
                "confidence": result.get("confidence"),
                "explanation": (result.get("explanation") or {}).get("what_it_is", result.get("fallback", "")),
                "expected_doc_type": r["doc_type"],
            }
            records.append(rec)
            marks = " ".join(f"{f[:8]}:{'-' if s is None else ('ok' if s else 'XX')}" for f, s in scores.items())
            print(f"[{lang}] {r['file']:<44} {secs:5.1f}s  {marks}" + (f"  ERROR {error}" if error else ""))

    # ---------------------------------------------------------------- summary
    lines = [f"# Dalil accuracy: {stamp}", "",
             f"{len(rows)} mock documents x {len(langs)} language(s) ({', '.join(langs)}), "
             f"{config.AI_PROVIDER} ({config.AI_MODEL}).", "",
             "| Check | Correct | Scored | Accuracy |", "|---|---|---|---|"]
    for f in FIELDS:
        scored = [x[f"ok_{f}"] for x in records if x[f"ok_{f}"] is not None]
        if scored:
            lines.append(f"| {f} | {sum(scored)} | {len(scored)} | {sum(scored) / len(scored):.0%} |")
    by_type = defaultdict(list)
    for x in records:
        checks = [x[f"ok_{f}"] for f in FIELDS if x[f"ok_{f}"] is not None]
        by_type[x["expected_doc_type"] or "unreadable"].append(all(checks) if checks else False)
    lines += ["", "| Document type | Fully correct | Documents |", "|---|---|---|"]
    for k, v in sorted(by_type.items()):
        lines.append(f"| {k} | {sum(v)} | {len(v)} |")
    times = [x["seconds"] for x in records if not x["error"]]
    if times:
        lines += ["", f"Average time per document: {sum(times) / len(times):.1f} s. Errors: {sum(1 for x in records if x['error'])}."]
    summary = "\n".join(lines)
    print("\n" + summary)

    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(records[0].keys()))
        w.writeheader()
        w.writerows(records)
    out_csv.with_suffix(".md").write_text(summary + "\n", encoding="utf-8")
    print(f"\nSaved {out_csv.relative_to(ROOT)} and {out_csv.with_suffix('.md').relative_to(ROOT)}")
    print("Also read the 'explanation' column: accuracy numbers don't show whether the wording is clear.")


if __name__ == "__main__":
    main()
