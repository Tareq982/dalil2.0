"""Before the pitch: run the demo photo through Dalil several times and check it's stage-ready.

    python tools/check_demo.py path/to/demo_photo.jpg
    python tools/check_demo.py path/to/demo_photo.jpg --runs 5 --lang en
    python tools/check_demo.py path/to/demo_photo.jpg --expect-service dubai-traffic-fine

Uses the real AI from your .env (each run = 2 AI calls). The AI can answer slightly differently
each time, so one good run isn't enough: this runs the same photo several times and prints a line
per run, then READY or NOT READY. A run is good when Dalil:
  - reads it as the expected document type and matches the expected official service
  - is confident ("High"), with no "couldn't read" or "not supported" message
  - reads the amount and the deadline
  - passes the number check without falling back to the plain template
  - never mentions a watermark, "sample" or whether the document is real
"""
import argparse
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import config, pipeline, safety  # noqa: E402

MEDIA = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".pdf": "application/pdf"}
WORRY = re.compile(r"sample|specimen|watermark|not (an )?official|not real|fake|test document|fictional|scam"
                   r"|عينة|تجريبي|غير رسمي|مزيف|احتيال", re.I)


def problems(r: dict, doc_type: str, service_id: str) -> list[str]:
    f = r.get("fields", {})
    out = []
    if f.get("doc_type") != doc_type:
        out.append(f"read as {f.get('doc_type')}, not {doc_type}")
    if r.get("service_id") != service_id:
        out.append(f"matched {r.get('service_id')}, not {service_id}")
    if r.get("fallback"):
        out.append("showed a fallback message instead of an explanation")
    if safety.level(r.get("confidence", 0)) != 0:
        out.append(f"confidence {r.get('confidence')} is not High")
    if f.get("amount_aed") is None:
        out.append("didn't read the amount")
    if not f.get("deadline_date"):
        out.append("didn't read the deadline")
    if r.get("number_check") == "template":
        out.append("number check fell back to the plain template")
    text = " ".join(str(v) for v in (r.get("explanation") or {}).values())
    if WORRY.search(text):
        out.append(f"explanation mentions: {WORRY.search(text).group(0)!r}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--lang", default="en")
    ap.add_argument("--expect-type", default="traffic_fine")
    ap.add_argument("--expect-service", default="dubai-traffic-fine")
    a = ap.parse_args()

    if config.MOCK_AI:
        sys.exit("MOCK_AI is on: set MOCK_AI=false and an API key in .env to test the real AI.")
    path = Path(a.photo)
    media = MEDIA.get(path.suffix.lower())
    if not media:
        sys.exit(f"Use a JPG, PNG, WEBP or PDF (got {path.suffix}).")
    data = path.read_bytes()

    bad_runs = 0
    for i in range(1, a.runs + 1):
        start = time.time()
        try:
            r = pipeline.analyze(data, media, a.lang)
        except Exception as e:  # noqa: BLE001 - report any failure, keep going
            bad_runs += 1
            print(f"run {i}: ERROR {e}")
            continue
        f = r.get("fields", {})
        issues = problems(r, a.expect_type, a.expect_service)
        bad_runs += bool(issues)
        print(f"run {i} ({time.time() - start:.1f}s): {f.get('doc_type')}, {f.get('emirate')}, "
              f"AED {f.get('amount_aed')}, due {f.get('deadline_date')}, service {r.get('service_id')}, "
              f"confidence {r.get('confidence')}, numbers {r.get('number_check')}")
        print("   " + ("OK" if not issues else "PROBLEM: " + "; ".join(issues)))
        if i == 1 and r.get("explanation"):
            print("   says: " + r["explanation"].get("what_it_is", ""))

    print()
    print("READY: every run was good." if not bad_runs else
          f"NOT READY: {bad_runs} of {a.runs} runs had a problem (see above). "
          "Retake the photo in better light, flat and with the whole page in frame, and run this again.")
    sys.exit(1 if bad_runs else 0)


if __name__ == "__main__":
    main()
