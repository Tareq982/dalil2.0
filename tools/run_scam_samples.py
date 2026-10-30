"""Run every mock message through "Is this message real?" and score it (samples/scam_expected.csv).

    python tools/run_scam_samples.py                # screenshots, photos and pasted text
    python tools/run_scam_samples.py --lang ar,ur   # warning signs written in Arabic and Urdu
    python tools/run_scam_samples.py --only .txt    # only the pasted-text versions

Uses the real AI from your .env (1 AI call per message). The verdict itself is decided by
code, so this mostly tests whether the AI READ the links, amount and sender correctly.
"""
import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import config, scamcheck  # noqa: E402
from app.ai import AIError  # noqa: E402

SAMPLES = ROOT / "samples"
MEDIA = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="en")
    parser.add_argument("--only", default="")
    args = parser.parse_args()
    if config.MOCK_AI:
        print("No AI key in .env (mock mode): screenshots get a fake reading. Add a key for a real test.")

    with open(SAMPLES / "scam_expected.csv", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if args.only in r["file"]]
    right = total = 0
    for lang in args.lang.split(","):
        for r in rows:
            path = SAMPLES / r["file"]
            try:
                if path.suffix == ".txt":
                    res = scamcheck.check(text=path.read_text(encoding="utf-8"), lang=lang)
                else:
                    res = scamcheck.check(file=(path.read_bytes(), MEDIA[path.suffix]), lang=lang)
            except AIError as e:
                print(f"ERR  {lang} {r['file']}: {e}")
                total += 1
                continue
            ok = res["verdict"] == r["verdict"] and res["check_instead"]["domain"] == r["check_instead"]
            right += ok
            total += 1
            links = ", ".join(f"{l['host']} ({l['status']})" for l in res["links"]) or "no links"
            print(f"{'OK ' if ok else 'BAD'}  {lang} {r['file']:34} {res['verdict']:15} "
                  f"(expected {r['verdict']})  {links}")
            for flag in res["red_flags"]:
                print(f"       - {flag}")
    print(f"\n{right}/{total} messages got the expected verdict and official link.")


if __name__ == "__main__":
    main()
