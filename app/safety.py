"""Responsible-AI text that is written by CODE, never by the model.

Every answer ends with: confidence level, the data source, the official link,
and a not-legal-advice line. Low-confidence answers are replaced by a fallback.

TODO (Demo/testing role): have a native speaker check each translation below.
"""
from . import config

GENERAL_URL = "https://u.ae"  # UAE government portal, used when no service matched

TEXT = {
    "en": {
        "confidence": "Confidence", "levels": ("High", "Medium", "Low"),
        "source": "Source", "link": "Official link",
        "disclaimer": "General guidance only, not legal advice. Always confirm on the official website.",
        "unverified": "Sample data, not yet verified",
        "fallback": "I couldn't read this document clearly enough to be sure. Please send a clearer photo, or check the official service directly.",
        "not_supported": "This doesn't look like an official document Dalil can explain (fines, residency notices, tenancy contracts). If it is a message asking you to pay through a link, don't use the link: check in the official app or website instead.",
    },
    "ar": {
        "confidence": "الثقة", "levels": ("عالية", "متوسطة", "منخفضة"),
        "source": "المصدر", "link": "الرابط الرسمي",
        "disclaimer": "هذه إرشادات عامة وليست استشارة قانونية. تأكد دائماً من الموقع الرسمي.",
        "unverified": "بيانات تجريبية لم يتم التحقق منها بعد",
        "fallback": "لم أتمكن من قراءة هذا المستند بوضوح كافٍ. يرجى إرسال صورة أوضح، أو التحقق من الخدمة الرسمية مباشرة.",
        "not_supported": "لا يبدو هذا مستنداً رسمياً يستطيع دليل شرحه (المخالفات، إشعارات الإقامة، عقود الإيجار). إذا كانت رسالة تطلب منك الدفع عبر رابط، فلا تستخدم الرابط، وتحقق من التطبيق أو الموقع الرسمي بدلاً من ذلك.",
    },
    "hi": {
        "confidence": "विश्वास स्तर", "levels": ("उच्च", "मध्यम", "कम"),
        "source": "स्रोत", "link": "आधिकारिक लिंक",
        "disclaimer": "यह केवल सामान्य मार्गदर्शन है, कानूनी सलाह नहीं। हमेशा आधिकारिक वेबसाइट पर पुष्टि करें।",
        "unverified": "नमूना डेटा, अभी सत्यापित नहीं",
        "fallback": "मैं इस दस्तावेज़ को ठीक से नहीं पढ़ पाया। कृपया एक साफ़ फ़ोटो भेजें, या सीधे आधिकारिक सेवा पर जाँच करें।",
        "not_supported": "यह कोई आधिकारिक दस्तावेज़ नहीं लगता जिसे दलील समझा सके (जुर्माना, रेज़िडेंसी नोटिस, किराया अनुबंध)। अगर यह कोई संदेश है जो आपसे लिंक के ज़रिए भुगतान करने को कहता है, तो उस लिंक का इस्तेमाल न करें, आधिकारिक ऐप या वेबसाइट पर जाँच करें।",
    },
    "ur": {
        "confidence": "اعتماد", "levels": ("زیادہ", "درمیانہ", "کم"),
        "source": "ماخذ", "link": "سرکاری لنک",
        "disclaimer": "یہ صرف عمومی رہنمائی ہے، قانونی مشورہ نہیں۔ ہمیشہ سرکاری ویب سائٹ پر تصدیق کریں۔",
        "unverified": "نمونہ ڈیٹا، ابھی تصدیق شدہ نہیں",
        "fallback": "میں اس دستاویز کو صاف طور پر نہیں پڑھ سکا۔ براہ کرم واضح تصویر بھیجیں، یا براہ راست سرکاری سروس پر چیک کریں۔",
        "not_supported": "یہ کوئی سرکاری دستاویز نہیں لگتی جسے دلیل سمجھا سکے (جرمانے، رہائش کے نوٹس، کرایہ داری کے معاہدے)۔ اگر یہ کوئی پیغام ہے جو آپ سے لنک کے ذریعے ادائیگی کرنے کو کہتا ہے تو وہ لنک استعمال نہ کریں، سرکاری ایپ یا ویب سائٹ پر چیک کریں۔",
    },
    "tl": {
        "confidence": "Antas ng katiyakan", "levels": ("Mataas", "Katamtaman", "Mababa"),
        "source": "Pinagmulan", "link": "Opisyal na link",
        "disclaimer": "Pangkalahatang gabay lamang ito, hindi legal na payo. Laging kumpirmahin sa opisyal na website.",
        "unverified": "Sample na datos, hindi pa beripikado",
        "fallback": "Hindi ko nabasa nang malinaw ang dokumentong ito. Magpadala ng mas malinaw na larawan, o direktang tingnan ang opisyal na serbisyo.",
        "not_supported": "Mukhang hindi ito opisyal na dokumento na kayang ipaliwanag ni Dalil (multa, abiso sa residency, kontrata sa pag-upa). Kung mensahe ito na humihiling na magbayad ka sa pamamagitan ng link, huwag gamitin ang link: tingnan sa opisyal na app o website.",
    },
    "bn": {
        "confidence": "নির্ভরযোগ্যতা", "levels": ("উচ্চ", "মাঝারি", "কম"),
        "source": "উৎস", "link": "অফিসিয়াল লিংক",
        "disclaimer": "এটি শুধুমাত্র সাধারণ নির্দেশনা, আইনি পরামর্শ নয়। সবসময় অফিসিয়াল ওয়েবসাইটে নিশ্চিত করুন।",
        "unverified": "নমুনা তথ্য, এখনও যাচাই করা হয়নি",
        "fallback": "আমি এই নথিটি পরিষ্কারভাবে পড়তে পারিনি। অনুগ্রহ করে একটি পরিষ্কার ছবি পাঠান, অথবা সরাসরি অফিসিয়াল সেবায় যাচাই করুন।",
        "not_supported": "এটি দলিল ব্যাখ্যা করতে পারে এমন কোনো সরকারি নথি বলে মনে হচ্ছে না (জরিমানা, রেসিডেন্সি নোটিশ, ভাড়ার চুক্তি)। যদি এটি কোনো বার্তা হয় যা লিংকের মাধ্যমে টাকা দিতে বলে, তাহলে লিংকটি ব্যবহার করবেন না, সরকারি অ্যাপ বা ওয়েবসাইটে যাচাই করুন।",
    },
    "ml": {
        "confidence": "വിശ്വാസ്യത", "levels": ("ഉയർന്നത്", "ഇടത്തരം", "കുറവ്"),
        "source": "ഉറവിടം", "link": "ഔദ്യോഗിക ലിങ്ക്",
        "disclaimer": "ഇത് പൊതുവായ മാർഗ്ഗനിർദ്ദേശം മാത്രമാണ്, നിയമോപദേശമല്ല. എപ്പോഴും ഔദ്യോഗിക വെബ്സൈറ്റിൽ ഉറപ്പാക്കുക.",
        "unverified": "സാമ്പിൾ ഡാറ്റ, ഇതുവരെ പരിശോധിച്ചിട്ടില്ല",
        "fallback": "ഈ രേഖ വ്യക്തമായി വായിക്കാൻ എനിക്ക് കഴിഞ്ഞില്ല. ദയവായി കൂടുതൽ വ്യക്തമായ ഫോട്ടോ അയയ്ക്കുക, അല്ലെങ്കിൽ ഔദ്യോഗിക സേവനത്തിൽ നേരിട്ട് പരിശോധിക്കുക.",
        "not_supported": "ദലീലിന് വിശദീകരിക്കാൻ കഴിയുന്ന ഒരു ഔദ്യോഗിക രേഖയായി ഇത് തോന്നുന്നില്ല (പിഴകൾ, റെസിഡൻസി അറിയിപ്പുകൾ, വാടക കരാറുകൾ). ലിങ്ക് വഴി പണം അടയ്ക്കാൻ ആവശ്യപ്പെടുന്ന സന്ദേശമാണെങ്കിൽ, ആ ലിങ്ക് ഉപയോഗിക്കരുത്; ഔദ്യോഗിക ആപ്പിലോ വെബ്സൈറ്റിലോ പരിശോധിക്കുക.",
    },
}


def text(lang: str) -> dict:
    return TEXT.get(lang, TEXT["en"])


# The details that prove Dalil actually READ a fine or notice, not just recognised its shape.
# (Tenancy contracts often have none of these printed, so the rule doesn't apply to them.)
KEY_DETAILS = ["reference_number", "amount_aed", "issue_date", "deadline_date"]
NEEDS_KEY_DETAILS = {"traffic_fine", "visa_residency_notice"}


def overall_confidence(fields: dict, service: dict | None) -> float:
    """Model's own confidence, reduced when we couldn't match a verified service.

    Code overrides the model: an official document where none of the key details could be
    read (e.g. a very blurry photo) is treated as unreadable, whatever the model says."""
    c = fields.get("confidence", 0.0)
    if not fields.get("readable"):
        return 0.0
    if fields.get("doc_type") in NEEDS_KEY_DETAILS and not any(fields.get(k) for k in KEY_DETAILS):
        return 0.0
    if service is None:
        c *= 0.7
    return round(c, 2)


def level(conf: float) -> int:
    """0 = high, 1 = medium, 2 = low (too low to answer)."""
    if conf >= 0.8:
        return 0
    if conf >= config.MIN_CONFIDENCE:
        return 1
    return 2


def footer(lang: str, conf: float, service: dict | None) -> dict:
    t = text(lang)
    return {
        "confidence_label": f"{t['confidence']}: {t['levels'][level(conf)]}",
        "source_label": f"{t['source']}: {(service or {}).get('authority') or 'u.ae'}",
        "link_label": t["link"],
        "link": (service or {}).get("official_url") or GENERAL_URL,
        "disclaimer": t["disclaimer"],
        "unverified": t["unverified"] if service and not service.get("verified") else None,
    }
