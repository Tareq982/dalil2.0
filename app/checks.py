"""Number check (issue #20): the AI writes, code checks.

After explain.py writes the explanation, code finds every number in it (amounts, dates,
days, percentages) and checks each one appears in the data the AI was given: the details
read from the document, the matched official service, or the days left.

    1. All numbers found in the data          -> show the explanation        ("passed")
    2. A number isn't in the data              -> ask the AI once more, with a warning ("retried")
    3. Still a number that isn't in the data   -> a plain template built ONLY from the data ("template")

So the AI can't invent a fee, a discount or a deadline. COUNTS keeps how often each case
happened since the server started (shown on /health, useful for the feasibility slide).
"""
import json
import logging
import re
import unicodedata
from collections import Counter
from datetime import date

log = logging.getLogger("dalil")
COUNTS = Counter()

# Explanation parts that state facts (suggested questions are questions, not claims)
CHECKED_PARTS = ("what_it_is", "cost", "deadline", "next_steps")

# Small counting words ("2 steps", "1 day", "step 3") are fine without being in the data.
ALWAYS_OK = {0, 1, 2, 3}

# A number in any script: 600 / 1,000 / 177.75 / ٦٠٠ / ١٬٠٠٠ / ६०० / ৬০০ / ൬൦൦
NUMBER = re.compile(r"\d+(?:[,٬]\d+)*(?:[.٫]\d+)?")

# Never treat these document details as "allowed": the explanation must not repeat them.
PRIVATE = ("reference_number",)


def _value(token: str) -> float | None:
    """'1,000' -> 1000.0, '٦٠٠' -> 600.0, '03' -> 3.0"""
    digits = "".join(str(unicodedata.decimal(c)) if c.isdigit() else c for c in token)
    digits = digits.replace(",", "").replace("٬", "").replace("٫", ".")
    try:
        return float(digits)
    except ValueError:
        return None


def numbers(text) -> set[float]:
    found = set()
    for token in NUMBER.findall(str(text or "")):
        v = _value(token)
        if v is not None:
            found.add(v)
    return found


def allowed_numbers(fields: dict, service: dict | None, days_left: int | None) -> set[float]:
    """Every number the explanation may use: what the AI was given, plus simple sums of the fees."""
    doc = {k: v for k, v in (fields or {}).items() if k not in PRIVATE}
    allowed = numbers(json.dumps(doc, ensure_ascii=False)) | numbers(json.dumps(service or {}, ensure_ascii=False))
    if days_left is not None:
        allowed.add(float(abs(days_left)))
    # "AED 600 fine + AED 20 fee = AED 620 in total"
    money = {float(x) for x in (doc.get("amount_aed"), (service or {}).get("fee_aed")) if isinstance(x, (int, float))}
    money |= numbers((service or {}).get("fee_note"))
    allowed |= {a + b for a in money for b in money if a != b}
    return allowed | {float(n) for n in ALWAYS_OK}


def unsupported(explanation: dict, fields: dict, service: dict | None, days_left: int | None) -> list[str]:
    """Numbers in the explanation that aren't in the data, e.g. ['35', '24']. Empty list = all good."""
    allowed = allowed_numbers(fields, service, days_left)
    bad = []
    for part in CHECKED_PARTS:
        value = explanation.get(part)
        for text in (value if isinstance(value, list) else [value]):
            for token in NUMBER.findall(str(text or "")):
                v = _value(token)
                if v is not None and v not in allowed and token not in bad:
                    bad.append(token)
    return bad


def record(outcome: str, bad: list[str] | None = None) -> None:
    COUNTS[outcome] += 1
    if bad:
        log.warning("number check: %s (numbers not in the data: %s)", outcome, ", ".join(bad))


# ---------------------------------------------------------------- the plain template

# Built only from the data, so every number in it is correct by construction.
# Written by Claude: a native speaker should check each language.
TEMPLATE = {
    "en": {
        "kinds": {"traffic_fine": "a traffic fine", "visa_residency_notice": "a residency or visa notice",
                  "tenancy_contract": "a tenancy contract", "other": "an official document"},
        "what": "This is {kind}{from_}.", "from": " from {authority}",
        "cost": "The amount on the document is AED {amount}.", "no_cost": "No amount is shown on the document. Check it on the official link.",
        "deadline": "The deadline on the document is {date} ({days}).", "no_deadline": "No deadline is printed. Check the official link soon.",
        "days_left": "{n} days left", "day_left": "1 day left", "today": "today", "overdue": "{n} days overdue",
        "steps": ["Open the official link below.", "Check that the amount and the date there match your paper.",
                  "Pay or act only in the official app or website."],
    },
    "ar": {
        "kinds": {"traffic_fine": "مخالفة مرورية", "visa_residency_notice": "إشعار إقامة أو تأشيرة",
                  "tenancy_contract": "عقد إيجار", "other": "مستند رسمي"},
        "what": "هذه {kind}{from_}.", "from": " من {authority}",
        "cost": "المبلغ المكتوب في المستند هو {amount} درهم.", "no_cost": "لا يوجد مبلغ في المستند. تحقق منه عبر الرابط الرسمي.",
        "deadline": "الموعد النهائي في المستند هو {date} ({days}).", "no_deadline": "لا يوجد موعد نهائي مكتوب. تحقق من الرابط الرسمي قريباً.",
        "days_left": "متبقٍ {n} يوم", "day_left": "متبقٍ يوم واحد", "today": "اليوم", "overdue": "متأخر {n} يوم",
        "steps": ["افتح الرابط الرسمي أدناه.", "تأكد أن المبلغ والتاريخ هناك يطابقان ورقتك.",
                  "ادفع أو تصرّف فقط عبر التطبيق أو الموقع الرسمي."],
    },
    "hi": {
        "kinds": {"traffic_fine": "एक ट्रैफ़िक जुर्माना", "visa_residency_notice": "एक रेज़िडेंसी या वीज़ा नोटिस",
                  "tenancy_contract": "एक किराया अनुबंध", "other": "एक आधिकारिक दस्तावेज़"},
        "what": "यह {kind} है{from_}।", "from": " ({authority} से)",
        "cost": "दस्तावेज़ पर राशि AED {amount} है।", "no_cost": "दस्तावेज़ पर कोई राशि नहीं दी गई है। आधिकारिक लिंक पर जाँचें।",
        "deadline": "दस्तावेज़ पर अंतिम तिथि {date} है ({days})।", "no_deadline": "कोई अंतिम तिथि नहीं छपी है। जल्द ही आधिकारिक लिंक देखें।",
        "days_left": "{n} दिन बाकी", "day_left": "1 दिन बाकी", "today": "आज", "overdue": "{n} दिन देर",
        "steps": ["नीचे दिया आधिकारिक लिंक खोलें।", "जाँचें कि वहाँ राशि और तिथि आपके कागज़ से मेल खाती हैं।",
                  "भुगतान केवल आधिकारिक ऐप या वेबसाइट पर करें।"],
    },
    "ur": {
        "kinds": {"traffic_fine": "ٹریفک جرمانہ", "visa_residency_notice": "اقامہ یا ویزا نوٹس",
                  "tenancy_contract": "کرایہ داری کا معاہدہ", "other": "سرکاری دستاویز"},
        "what": "یہ ایک {kind} ہے{from_}۔", "from": " ({authority} کی طرف سے)",
        "cost": "دستاویز پر رقم {amount} درہم ہے۔", "no_cost": "دستاویز پر کوئی رقم نہیں لکھی۔ سرکاری لنک پر چیک کریں۔",
        "deadline": "دستاویز پر آخری تاریخ {date} ہے ({days})۔", "no_deadline": "کوئی آخری تاریخ نہیں لکھی۔ جلد سرکاری لنک دیکھیں۔",
        "days_left": "{n} دن باقی", "day_left": "1 دن باقی", "today": "آج", "overdue": "{n} دن تاخیر",
        "steps": ["نیچے دیا گیا سرکاری لنک کھولیں۔", "چیک کریں کہ وہاں رقم اور تاریخ آپ کے کاغذ سے ملتی ہیں۔",
                  "ادائیگی صرف سرکاری ایپ یا ویب سائٹ پر کریں۔"],
    },
    "tl": {
        "kinds": {"traffic_fine": "isang multa sa trapiko", "visa_residency_notice": "isang abiso ng residency o visa",
                  "tenancy_contract": "isang kontrata ng upa", "other": "isang opisyal na dokumento"},
        "what": "Ito ay {kind}{from_}.", "from": " mula sa {authority}",
        "cost": "Ang halaga sa dokumento ay AED {amount}.", "no_cost": "Walang nakasulat na halaga sa dokumento. Tingnan ito sa opisyal na link.",
        "deadline": "Ang deadline sa dokumento ay {date} ({days}).", "no_deadline": "Walang nakasulat na deadline. Tingnan agad ang opisyal na link.",
        "days_left": "{n} araw na lang", "day_left": "1 araw na lang", "today": "ngayon", "overdue": "{n} araw nang lampas",
        "steps": ["Buksan ang opisyal na link sa ibaba.", "Tingnan kung tugma ang halaga at petsa doon sa iyong papel.",
                  "Magbayad lamang sa opisyal na app o website."],
    },
    "bn": {
        "kinds": {"traffic_fine": "একটি ট্রাফিক জরিমানা", "visa_residency_notice": "একটি রেসিডেন্সি বা ভিসা নোটিশ",
                  "tenancy_contract": "একটি ভাড়ার চুক্তি", "other": "একটি সরকারি কাগজ"},
        "what": "এটি {kind}{from_}।", "from": " ({authority} থেকে)",
        "cost": "কাগজে লেখা পরিমাণ AED {amount}।", "no_cost": "কাগজে কোনো পরিমাণ লেখা নেই। সরকারি লিংকে দেখে নিন।",
        "deadline": "কাগজে শেষ তারিখ {date} ({days})।", "no_deadline": "কোনো শেষ তারিখ লেখা নেই। শীঘ্রই সরকারি লিংক দেখুন।",
        "days_left": "{n} দিন বাকি", "day_left": "1 দিন বাকি", "today": "আজ", "overdue": "{n} দিন দেরি",
        "steps": ["নিচের সরকারি লিংকটি খুলুন।", "সেখানে পরিমাণ ও তারিখ আপনার কাগজের সাথে মিলছে কিনা দেখুন।",
                  "শুধু সরকারি অ্যাপ বা ওয়েবসাইটে টাকা দিন।"],
    },
    "ml": {
        "kinds": {"traffic_fine": "ഒരു ട്രാഫിക് പിഴ", "visa_residency_notice": "ഒരു റെസിഡൻസി അല്ലെങ്കിൽ വിസ അറിയിപ്പ്",
                  "tenancy_contract": "ഒരു വാടക കരാർ", "other": "ഒരു ഔദ്യോഗിക രേഖ"},
        "what": "ഇത് {kind} ആണ്{from_}.", "from": " ({authority} നൽകിയത്)",
        "cost": "രേഖയിലെ തുക AED {amount} ആണ്.", "no_cost": "രേഖയിൽ തുക കാണിച്ചിട്ടില്ല. ഔദ്യോഗിക ലിങ്കിൽ പരിശോധിക്കുക.",
        "deadline": "രേഖയിലെ അവസാന തീയതി {date} ആണ് ({days}).", "no_deadline": "അവസാന തീയതി രേഖപ്പെടുത്തിയിട്ടില്ല. ഉടൻ ഔദ്യോഗിക ലിങ്ക് പരിശോധിക്കുക.",
        "days_left": "{n} ദിവസം ബാക്കി", "day_left": "1 ദിവസം ബാക്കി", "today": "ഇന്ന്", "overdue": "{n} ദിവസം വൈകി",
        "steps": ["താഴെയുള്ള ഔദ്യോഗിക ലിങ്ക് തുറക്കുക.", "അവിടെയുള്ള തുകയും തീയതിയും നിങ്ങളുടെ രേഖയുമായി ഒത്തുപോകുന്നുണ്ടോ എന്ന് നോക്കുക.",
                  "ഔദ്യോഗിക ആപ്പിലോ വെബ്സൈറ്റിലോ മാത്രം പണമടയ്ക്കുക."],
    },
}


def template(fields: dict, days_left: int | None, lang: str) -> dict:
    """A plain explanation made only from the data. Used when the AI's numbers can't be trusted."""
    t = TEMPLATE.get(lang, TEMPLATE["en"])
    kind = t["kinds"].get(fields.get("doc_type"), t["kinds"]["other"])
    authority = fields.get("issuing_authority")
    amount = fields.get("amount_aed")
    deadline = fields.get("deadline_date")
    if days_left is None:
        days = ""
    elif days_left < 0:
        days = t["overdue"].format(n=-days_left)
    elif days_left == 0:
        days = t["today"]
    else:
        days = t["day_left"] if days_left == 1 else t["days_left"].format(n=days_left)
    try:
        shown_date = date.fromisoformat(deadline).strftime("%d/%m/%Y") if deadline else None
    except ValueError:
        shown_date = None
    return {
        "what_it_is": t["what"].format(kind=kind, from_=t["from"].format(authority=authority) if authority else ""),
        "cost": t["cost"].format(amount=f"{amount:,.2f}".rstrip("0").rstrip(".")) if isinstance(amount, (int, float)) else t["no_cost"],
        "deadline": (t["deadline"].format(date=shown_date, days=days).replace(" ()", "").replace(" ()", "")
                     if shown_date else t["no_deadline"]),
        "next_steps": list(t["steps"]),
        "suggested_questions": [],
    }
