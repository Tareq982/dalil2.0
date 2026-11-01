# Mock test documents

**Fictional documents only.** Invented people, plates and reference numbers, no logos, and a
"SAMPLE - NOT AN OFFICIAL DOCUMENT" watermark. Never put a real person's fine, visa or contract
in this folder. Real documents for private testing go in `samples/private/`, which git ignores.

## What's here (22 files)

| Type | Documents | What they test |
|---|---|---|
| Traffic fines | Dubai speeding, red light with deadline, RTA parking, overdue reminder; Abu Dhabi speeding, Abu Dhabi Arabic-only; Sharjah seatbelt | Different emirates and authorities, amounts written as "1,000", a deadline that has already passed, Arabic-only text, an emirate with no catalog record |
| Residency and visa | GDRFA Dubai expiry, ICP overstay in Sharjah, ICP cancellation in Ajman | Expiry date and grace period end as deadlines, overstay totals, federal versus Dubai matching |
| Tenancy | Ejari certificate, Dubai unified tenancy contract (also as a **PDF**), Abu Dhabi Tawtheeq | Rent that is not an amount due, the PDF path, an emirate with no catalog record |
| Phone photos | `__photo.jpg` versions: tilted, shadowed, noisy | Real-world photo quality |
| Hard cases | `__blurry.jpg`, `__cropped.jpg` (bottom half missing), a cafe receipt, a scam text message | Dalil must refuse to guess, must not invent missing values, and must not treat a scam as a real fine |

The correct answer for each file is in `expected.csv`:
- An empty cell means the field isn't scored.
- `none` means Dalil must **not** find a value, for example when no deadline is printed or the catalog has no matching service.
- `expect_fallback` set to `yes` means Dalil should say it can't read the document.

## Mock messages for "Is this message real?"

Fictional scam and real-looking messages: SMS, an email and a fake payment website. Each one is a
`.png` screenshot to upload and a `.txt` to paste. The scam links are made-up addresses that imitate
official ones. Never add a real scam link or someone's real message.

| File | Should say | Tests |
|---|---|---|
| `scam_sms_fine` | Don't pay | `p0lice` with a zero, 90% discount, 24-hour pressure |
| `scam_sms_salik_toll` (+ `__photo.jpg`) | Don't pay | `salik-toll-pay.top` imitates salik.ae |
| `scam_sms_post_parcel` | Don't pay | A `bit.ly` short link hides the address, foreign number |
| `scam_sms_police_arabic` | Don't pay | Arabic only; `dubaipolice.gov.ae.fines-pay.info` starts with the real address but isn't it |
| `scam_email_rta_discount` | Don't pay | Fake RTA email, 70% off today only, asks for card details |
| `scam_website_tamm_fines` | Don't pay | Fake payment page asking for card and OTP |
| `suspicious_sms_nol_points` | Suspicious | A non-official link with no payment asked |
| `real_sms_rta_reminder` | Looks official | Only links to `www.rta.ae` (still: pay in the app) |

Expected results are in `scam_expected.csv`. Score them with `python tools/run_scam_samples.py`.
To change them, edit `tools/make_scam_samples.py` and run it (needs Playwright, like below).

## Run the test

With an AI key in `.env`:

```
python tools/run_samples.py
python tools/run_samples.py --lang ar,ur,ml
python tools/run_samples.py --only fine_
```

The script prints a line per document and an accuracy table. It saves both in `samples/results/`, and the table goes on the feasibility slide (#6). Also read the `explanation` column in the CSV, because accuracy numbers don't show whether the wording is clear.

To change or add documents, edit `tools/make_samples.py` and run `python tools/make_samples.py`. That needs Playwright: run `pip install playwright` and then `python -m playwright install chromium`.
