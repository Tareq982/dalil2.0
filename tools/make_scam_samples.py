"""Generate the MOCK scam and real-looking messages for "Is this message real?" (samples/scam_*).

    python tools/make_scam_samples.py

Each message is written twice:
- samples/<name>.png  a screenshot (SMS, email or website) to upload, plus one phone photo
- samples/<name>.txt  the same text, to paste into the box

Every message is fictional. Scam links point to made-up addresses that imitate official
ones: never put a real scam link (or a real person's message) in this folder. Every image
says SAMPLE. The expected verdicts are in samples/scam_expected.csv.

Needs Playwright and Pillow, like tools/make_samples.py.
"""
import io
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_samples import photo  # noqa: E402  (same phone-photo effect as the documents)

OUT = Path(__file__).resolve().parent.parent / "samples"

CSS = """
* { box-sizing: border-box; }
body { margin: 0; font-family: "DejaVu Sans", "Noto Sans Arabic", Arial, sans-serif; color: #111; }
.tag { position: absolute; top: 8px; right: 10px; font-size: 11px; font-weight: bold; color: #c00;
       border: 1.5px solid #c00; padding: 1px 6px; border-radius: 4px; background: #fff; }
.sms { position: relative; width: 420px; padding: 24px; background: #e9e9ee; }
.sms .from { text-align: center; color: #555; font-size: 14px; margin-bottom: 14px; }
.bubble { background: #fff; border-radius: 18px; padding: 14px 16px; font-size: 16px; line-height: 1.45; white-space: pre-wrap; }
.bubble.rtl { direction: rtl; text-align: right; }
.bubble a, .mail a, .site a { color: #1a5fd0; text-decoration: underline; }
.mail { position: relative; width: 620px; background: #fff; border: 1px solid #ccc; }
.mail .bar { background: #f3f3f3; padding: 14px 18px; font-size: 14px; line-height: 1.6; border-bottom: 1px solid #ddd; }
.mail .body { padding: 22px 24px 28px; font-size: 15px; line-height: 1.55; white-space: pre-wrap; }
.mail .btn { display: inline-block; margin-top: 8px; background: #0a7f45; color: #fff; padding: 10px 22px; border-radius: 6px; font-weight: bold; }
.site { position: relative; width: 640px; background: #fff; border: 1px solid #bbb; }
.site .chrome { background: #dfe1e5; padding: 10px 12px; }
.site .addr { background: #fff; border-radius: 16px; padding: 6px 14px; font-size: 14px; color: #222; }
.site .page { padding: 26px 30px 30px; }
.site h2 { margin: 0 0 6px; font-size: 22px; }
.site .promo { background: #fff3cd; border: 1px solid #e0b400; padding: 8px 12px; margin: 12px 0; font-weight: bold; }
.site label { display: block; font-size: 13px; color: #555; margin-top: 12px; }
.site .input { border: 1px solid #aaa; border-radius: 4px; height: 34px; margin-top: 4px; }
.site .pay { margin-top: 18px; background: #b00020; color: #fff; text-align: center; padding: 12px; border-radius: 6px; font-weight: bold; }
"""

TAG = '<span class="tag">SAMPLE</span>'


def link(text: str, url: str) -> str:
    return text.replace(url, f"<a>{url}</a>")


def sms(sender: str, text: str, url: str = "", rtl: bool = False) -> str:
    return (f'<div class="sms">{TAG}<div class="from">{sender}<br>Today 10:41</div>'
            f'<div class="bubble{" rtl" if rtl else ""}">{link(text, url) if url else text}</div></div>')


# name -> (screenshot html, text to paste). Keep the two in step.
MESSAGES = {}

text = ("Salik: You have an unpaid toll of AED 48.50. Pay now to avoid a fine of AED 500: "
        "https://salik-toll-pay.top/uae\n(sample message)")
MESSAGES["scam_sms_salik_toll"] = (sms("+971 52 000 0101 (sample)", text, "https://salik-toll-pay.top/uae"),
                                   "From: +971 52 000 0101\n" + text)

text = ("Emirates Post: Your parcel is on hold because the address is incomplete. Pay AED 12.50 "
        "redelivery fee within 12 hours or it will be returned: http://bit.ly/ep-redeliver\n(sample message)")
MESSAGES["scam_sms_post_parcel"] = (sms("+44 7700 900000 (sample)", text, "http://bit.ly/ep-redeliver"),
                                    "From: +44 7700 900000\n" + text)

text = ("شرطة دبي: لديك مخالفة مرورية غير مدفوعة بقيمة 2,000 درهم. ادفع خلال 24 ساعة واحصل على خصم 80%، "
        "وإلا سيتم إيقاف رخصتك: dubaipolice.gov.ae.fines-pay.info\n(رسالة تجريبية)")
MESSAGES["scam_sms_police_arabic"] = (sms("+971 56 000 0202 (sample)", text, "dubaipolice.gov.ae.fines-pay.info", rtl=True),
                                      "From: +971 56 000 0202\n" + text)

body = ("Dear customer,\n\nGood news! For the National Day celebration, RTA is offering a 70% DISCOUNT on all "
        "traffic fines. This offer ends TODAY at midnight.\n\nTo get your discount, confirm your card details "
        "at the link below:\n\nhttps://rta-ae-discount.com/pay\n\nRoads and Transport Authority\n(sample email)")
MESSAGES["scam_email_rta_discount"] = (
    f'<div class="mail">{TAG}<div class="bar"><b>From:</b> RTA Fines &lt;offers@rta-discounts.com&gt;<br>'
    f'<b>Subject:</b> 70% discount on all traffic fines - today only</div>'
    f'<div class="body">{link(body, "https://rta-ae-discount.com/pay")}<br><span class="btn">Pay with 70% off</span></div></div>',
    "From: RTA Fines <offers@rta-discounts.com>\nSubject: 70% discount on all traffic fines - today only\n\n" + body)

MESSAGES["scam_website_tamm_fines"] = (
    f'<div class="site">{TAG}<div class="chrome"><div class="addr">https://tamm-abudhabi-fines.online/pay</div></div>'
    '<div class="page"><h2>Abu Dhabi Traffic Fines Payment</h2>'
    '<div class="promo">Limited offer: 50% off all fines. Ends in 02:59:41</div>'
    'Amount due: <b>AED 1,200</b>'
    '<label>Card number</label><div class="input"></div>'
    '<label>Expiry / CVV</label><div class="input"></div>'
    '<label>SMS code (OTP)</label><div class="input"></div>'
    '<div class="pay">PAY NOW</div><p style="font-size:11px;color:#888">(sample website - fictional)</p></div></div>',
    "Website address: https://tamm-abudhabi-fines.online/pay\nAbu Dhabi Traffic Fines Payment\n"
    "Limited offer: 50% off all fines. Ends in 02:59:41\nAmount due: AED 1,200\n"
    "Card number / Expiry / CVV / SMS code (OTP)\nPAY NOW\n(sample website - fictional)")

text = ("Nol Rewards: your Nol card has 1,250 bonus points. Check them before they expire: "
        "nol-rewards-club.info\n(sample message)")
MESSAGES["suspicious_sms_nol_points"] = (sms("NolRewards (sample)", text, "nol-rewards-club.info"),
                                         "From: NolRewards\n" + text)

text = ("RTA: Reminder: you have unpaid traffic fines on your file. To see and pay them, open the "
        "RTA Dubai app or visit www.rta.ae\nRTA will never ask for your card details by SMS.\n(sample message)")
MESSAGES["real_sms_rta_reminder"] = (sms("RTA (sample)", text, "www.rta.ae"), "From: RTA\n" + text)


# The scam text message from tools/make_samples.py (scam_sms_fine.png) also gets a text version.
TEXT_ONLY = {
    "scam_sms_fine": ("From: +971 55 000 0000\nDubai Police: You have an unpaid traffic fine of AED 1,500. Pay within "
                      "24 hours to get a 90% discount, or your licence will be blocked: http://dubai-p0lice-fines.top/pay"),
}


def main():
    renders = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 800, "height": 1000}, device_scale_factor=1)
        for name, (html, pasted) in MESSAGES.items():
            page.set_content(f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{html}</body></html>")
            renders[name] = Image.open(io.BytesIO(page.locator("body > div").first.screenshot()))
            renders[name].save(OUT / f"{name}.png", optimize=True)
            (OUT / f"{name}.txt").write_text(pasted + "\n", encoding="utf-8")
        browser.close()
    for name, pasted in TEXT_ONLY.items():
        (OUT / f"{name}.txt").write_text(pasted + "\n", encoding="utf-8")
    photo(renders["scam_sms_salik_toll"], 21).save(OUT / "scam_sms_salik_toll__photo.jpg", quality=82)
    print(f"Wrote {len(renders)} screenshots, {len(renders)} text files and 1 photo to {OUT}")


if __name__ == "__main__":
    main()
