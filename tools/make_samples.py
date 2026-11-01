"""Generate the MOCK test documents in samples/ (issue #5).

    python tools/make_samples.py

Every document is fictional: invented people, plates and reference numbers, no
logos or emblems, and a visible "SAMPLE - NOT AN OFFICIAL DOCUMENT" watermark.
They exist only to test Dalil. The correct answers are in samples/expected.csv.

Needs Playwright (pip install playwright; python -m playwright install chromium)
and Pillow. You only need to run this to change the samples: the generated files
are already in the repo.
"""
import io
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "samples"

CSS = """
* { box-sizing: border-box; }
body { margin: 0; background: #fff; font-family: "DejaVu Sans", "Noto Sans Arabic", Arial, sans-serif; color: #111; }
.doc { position: relative; width: 860px; padding: 40px 48px 36px; background: #fff; overflow: hidden; }
.head { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 3px solid #333; padding-bottom: 14px; }
.head .en { font-size: 22px; font-weight: bold; }
.head .ar { font-size: 22px; font-weight: bold; direction: rtl; text-align: right; }
.sub { display: flex; justify-content: space-between; margin-top: 8px; font-size: 15px; color: #333; }
.sub .ar { direction: rtl; }
h1 { font-size: 24px; margin: 26px 0 4px; text-align: center; }
h1.ar { direction: rtl; margin-top: 0; }
table { width: 100%; border-collapse: collapse; margin-top: 18px; font-size: 16px; }
td { border: 1px solid #999; padding: 9px 10px; vertical-align: top; }
td.k { width: 30%; background: #f2f2f2; font-weight: bold; }
td.ar { direction: rtl; text-align: right; width: 30%; background: #f2f2f2; font-weight: bold; }
td.v { font-weight: bold; }
.note { margin-top: 18px; font-size: 14px; line-height: 1.5; border: 1px dashed #777; padding: 10px 12px; }
.note.ar { direction: rtl; text-align: right; }
.foot { margin-top: 26px; font-size: 12px; color: #444; display: flex; justify-content: space-between; }
.wm { position: absolute; inset: 0; display: grid; place-items: center; pointer-events: none; }
.wm span { transform: rotate(-28deg); font-size: 46px; font-weight: bold; color: rgba(200, 0, 0, 0.16);
           border: 6px solid rgba(200, 0, 0, 0.16); padding: 10px 24px; white-space: nowrap; }
.rtl { direction: rtl; text-align: right; }
.sms { width: 420px; padding: 24px; background: #e9e9ee; font-family: "DejaVu Sans", Arial, sans-serif; }
.sms .from { text-align: center; color: #555; font-size: 14px; margin-bottom: 14px; }
.bubble { background: #fff; border-radius: 18px; padding: 14px 16px; font-size: 16px; line-height: 1.45; }
.bubble a { color: #1a5fd0; }
.receipt { width: 420px; padding: 30px 28px; background: #fff; font-family: "DejaVu Sans Mono", monospace; font-size: 15px; }
.receipt .c { text-align: center; }
.receipt .row { display: flex; justify-content: space-between; }
"""

WM = '<div class="wm"><span>SAMPLE - NOT AN OFFICIAL DOCUMENT</span></div>'
FOOT = ('<div class="foot"><span>Fictional test document for the Dalil hackathon prototype.</span>'
        '<span class="rtl">مستند تجريبي - غير رسمي</span></div>')


def doc(head_en, head_ar, sub_en, sub_ar, title_en, title_ar, rows, note="", note_ar=""):
    tr = "".join(
        f'<tr><td class="k">{k}</td><td class="v">{v}</td><td class="ar">{a}</td></tr>' for k, v, a in rows
    )
    return f"""<div class="doc">
      <div class="head"><div class="en">{head_en}</div><div class="ar">{head_ar}</div></div>
      <div class="sub"><span>{sub_en}</span><span class="ar">{sub_ar}</span></div>
      <h1>{title_en}</h1><h1 class="ar">{title_ar}</h1>
      <table>{tr}</table>
      {f'<div class="note">{note}</div>' if note else ''}
      {f'<div class="note ar">{note_ar}</div>' if note_ar else ''}
      {FOOT}{WM}</div>"""


def doc_ar_only(head_ar, sub_ar, title_ar, rows, note_ar=""):
    tr = "".join(f'<tr><td class="ar">{k}</td><td class="v rtl">{v}</td></tr>' for k, v in rows)
    return f"""<div class="doc rtl">
      <div class="head"><div class="ar">{head_ar}</div></div>
      <div class="sub"><span class="ar">{sub_ar}</span></div>
      <h1 class="ar">{title_ar}</h1>
      <table>{tr}</table>
      {f'<div class="note ar">{note_ar}</div>' if note_ar else ''}
      {FOOT}{WM}</div>"""


DOCS = {
    # ---------------------------------------------------------------- traffic fines
    "fine_dubai_speeding": doc(
        "Dubai Police - General Department of Traffic", "شرطة دبي - الإدارة العامة للمرور",
        "Traffic violation notice", "إشعار مخالفة مرورية",
        "Traffic Fine Notice", "إشعار مخالفة مرورية", [
            ("Fine number", "DXB-TF-2026-0048812", "رقم المخالفة"),
            ("Date and time", "20/10/2026 07:42", "التاريخ والوقت"),
            ("Location", "Sheikh Zayed Road, near Interchange 4", "الموقع"),
            ("Violation", "Exceeding the speed limit by not more than 30 km/h<br>تجاوز السرعة المقررة بما لا يزيد عن 30 كم/ساعة", "نوع المخالفة"),
            ("Plate number", "Dubai Q 40512 (sample)", "رقم اللوحة"),
            ("Black points", "0", "النقاط السوداء"),
            ("Fine amount", "AED 600", "قيمة المخالفة"),
            ("Status", "Payable", "الحالة"),
        ], "Pay through the Dubai Police app or website, or the RTA website.",
        "يمكن السداد عبر تطبيق أو موقع شرطة دبي أو موقع هيئة الطرق والمواصلات."),

    "fine_dubai_redlight_deadline": doc(
        "Dubai Police - General Department of Traffic", "شرطة دبي - الإدارة العامة للمرور",
        "Traffic violation notice", "إشعار مخالفة مرورية",
        "Traffic Fine Notice", "إشعار مخالفة مرورية", [
            ("Fine number", "DXB-TF-2026-0051290", "رقم المخالفة"),
            ("Date and time", "18/10/2026 22:15", "التاريخ والوقت"),
            ("Location", "Al Khail Road / Al Quoz junction", "الموقع"),
            ("Violation", "Jumping a red light<br>تجاوز الإشارة الضوئية الحمراء", "نوع المخالفة"),
            ("Plate number", "Dubai F 77310 (sample)", "رقم اللوحة"),
            ("Black points", "12", "النقاط السوداء"),
            ("Vehicle impound", "30 days", "حجز المركبة"),
            ("Fine amount", "AED 1,000", "قيمة المخالفة"),
            ("Pay by", "08/11/2026", "يرجى السداد قبل"),
        ], "Please pay by the date above to avoid further action on the vehicle.",
        "يرجى السداد قبل التاريخ المذكور أعلاه."),

    "fine_dubai_parking_rta": doc(
        "Roads and Transport Authority - Parking", "هيئة الطرق والمواصلات - المواقف",
        "Parking violation", "مخالفة مواقف",
        "Parking Fine", "مخالفة مواقف", [
            ("Fine number", "RTA-PK-2026-7731045", "رقم المخالفة"),
            ("Date and time", "25/10/2026 13:05", "التاريخ والوقت"),
            ("Zone", "Zone 365C, Al Karama", "المنطقة"),
            ("Violation", "Not paying the parking fee<br>عدم دفع رسوم الموقف", "نوع المخالفة"),
            ("Plate number", "Dubai K 28844 (sample)", "رقم اللوحة"),
            ("Fine amount", "AED 150", "قيمة المخالفة"),
        ]),

    "fine_dubai_overdue": doc(
        "Dubai Police - General Department of Traffic", "شرطة دبي - الإدارة العامة للمرور",
        "Reminder: unpaid traffic fine", "تذكير: مخالفة غير مسددة",
        "Unpaid Fine Reminder", "تذكير بمخالفة غير مسددة", [
            ("Fine number", "DXB-TF-2026-0031177", "رقم المخالفة"),
            ("Date of violation", "02/09/2026", "تاريخ المخالفة"),
            ("Violation", "Sudden swerving<br>الانحراف المفاجئ", "نوع المخالفة"),
            ("Fine amount", "AED 1,000", "قيمة المخالفة"),
            ("Pay by", "01/10/2026", "يرجى السداد قبل"),
            ("Status", "Overdue", "الحالة"),
        ]),

    "fine_abudhabi_speeding": doc(
        "Abu Dhabi Police - Traffic and Patrols", "شرطة أبوظبي - المرور والدوريات",
        "Traffic violation notice", "إشعار مخالفة مرورية",
        "Traffic Fine", "مخالفة مرورية", [
            ("Fine number", "AUH-2026-4471902", "رقم المخالفة"),
            ("Date and time", "01/10/2026 16:20", "التاريخ والوقت"),
            ("Location", "Abu Dhabi - Al Ain Road", "الموقع"),
            ("Violation", "Exceeding the speed limit by not more than 40 km/h<br>تجاوز السرعة المقررة بما لا يزيد عن 40 كم/ساعة", "نوع المخالفة"),
            ("Plate number", "Abu Dhabi 13 / 55201 (sample)", "رقم اللوحة"),
            ("Fine amount", "AED 700", "قيمة المخالفة"),
        ]),

    "fine_abudhabi_arabic_only": doc_ar_only(
        "شرطة أبوظبي - المرور والدوريات", "إشعار مخالفة مرورية", "مخالفة مرورية", [
            ("رقم المخالفة", "AUH-2026-4380017"),
            ("التاريخ", "15/09/2026"),
            ("نوع المخالفة", "استخدام الهاتف المتحرك باليد أثناء القيادة"),
            ("رقم اللوحة", "أبوظبي 5 / 81920 (تجريبي)"),
            ("النقاط السوداء", "4"),
            ("قيمة المخالفة", "800 درهم"),
        ], "يمكن السداد عبر تطبيق شرطة أبوظبي أو منصة تم."),

    "fine_sharjah_seatbelt": doc(
        "Sharjah Police - Traffic", "شرطة الشارقة - المرور",
        "Traffic violation notice", "إشعار مخالفة مرورية",
        "Traffic Fine", "مخالفة مرورية", [
            ("Fine number", "SHJ-2026-0920334", "رقم المخالفة"),
            ("Date and time", "12/10/2026 09:10", "التاريخ والوقت"),
            ("Violation", "Driver not wearing a seatbelt<br>عدم ربط حزام الأمان", "نوع المخالفة"),
            ("Fine amount", "AED 400", "قيمة المخالفة"),
        ]),

    # ---------------------------------------------------------------- residency / visa
    "residency_dubai_expiry": doc(
        "General Directorate of Residency and Foreigners Affairs - Dubai", "الإدارة العامة للإقامة وشؤون الأجانب - دبي",
        "Notice", "إشعار",
        "Residence Permit Expiry Notice", "إشعار انتهاء الإقامة", [
            ("Name", "Arjun Menon (fictional)", "الاسم"),
            ("File number", "201/2024/7/123456 (sample)", "رقم الملف"),
            ("Sponsor", "Sample Trading LLC (private sector)", "الكفيل"),
            ("Residence expiry date", "15/11/2026", "تاريخ انتهاء الإقامة"),
        ], "Your residence permit expires on the date above. Please renew it before it expires. "
           "After expiry or cancellation there is a grace period; after that, overstay fines apply.",
        "تنتهي إقامتك في التاريخ المذكور أعلاه. يرجى التجديد قبل الانتهاء."),

    "residency_icp_overstay_sharjah": doc(
        "Federal Authority for Identity, Citizenship, Customs and Port Security (ICP)",
        "الهيئة الاتحادية للهوية والجنسية والجمارك وأمن المنافذ",
        "Sharjah - residency violation", "الشارقة - مخالفة إقامة",
        "Fine Notice: Overstay", "إشعار غرامة: تجاوز مدة البقاء", [
            ("Name", "Maria Santos (fictional)", "الاسم"),
            ("Unified number", "784-1990-0000000-0 (sample)", "الرقم الموحد"),
            ("Violation", "Staying after the residence permit expired and the grace period ended", "المخالفة"),
            ("Days of overstay", "12", "عدد الأيام"),
            ("Daily fine", "AED 50", "الغرامة اليومية"),
            ("Total fine", "AED 600", "إجمالي الغرامة"),
            ("Issued on", "27/10/2026", "تاريخ الإصدار"),
        ], "Pay the fine and adjust your status or leave the country.",
        "يجب سداد الغرامة وتعديل الوضع أو مغادرة الدولة."),

    "residency_ajman_cancellation": doc(
        "Federal Authority for Identity, Citizenship, Customs and Port Security (ICP)",
        "الهيئة الاتحادية للهوية والجنسية والجمارك وأمن المنافذ",
        "Ajman", "عجمان",
        "Residence Cancellation Notice", "إشعار إلغاء الإقامة", [
            ("Name", "Rahim Uddin (fictional)", "الاسم"),
            ("Cancellation date", "11/10/2026", "تاريخ الإلغاء"),
            ("Grace period ends", "10/12/2026", "نهاية مهلة السماح"),
        ], "You must leave the country or get a new residence permit before the grace period ends. "
           "After that, a fine of AED 50 per day applies.",
        "يجب مغادرة الدولة أو الحصول على إقامة جديدة قبل نهاية مهلة السماح."),

    # ---------------------------------------------------------------- tenancy
    "ejari_certificate_dubai": doc(
        "Dubai Land Department - Ejari", "دائرة الأراضي والأملاك - إيجاري",
        "Tenancy contract registration", "تسجيل عقد إيجار",
        "Ejari Registration Certificate", "شهادة تسجيل عقد إيجار", [
            ("Contract number", "0000-2026-0123456 (sample)", "رقم العقد"),
            ("Tenant", "Priya Nair (fictional)", "المستأجر"),
            ("Landlord", "Sample Properties LLC", "المؤجر"),
            ("Property", "Apartment 1204, Sample Tower, Al Barsha", "العقار"),
            ("Contract start", "01/11/2026", "تاريخ البداية"),
            ("Contract end", "31/10/2027", "تاريخ النهاية"),
            ("Annual rent", "AED 85,000", "قيمة الإيجار السنوي"),
            ("Number of cheques", "4", "عدد الشيكات"),
        ]),

    "tenancy_contract_dubai_unified": doc(
        "Government of Dubai - Land Department", "حكومة دبي - دائرة الأراضي والأملاك",
        "Unified tenancy contract", "عقد الإيجار الموحد",
        "Tenancy Contract", "عقد إيجار", [
            ("Tenant", "Mohammed Rafiq (fictional)", "المستأجر"),
            ("Landlord", "Sample Real Estate LLC", "المؤجر"),
            ("Property", "Studio 507, Sample Residence, International City", "العقار"),
            ("Usage", "Residential", "الاستخدام"),
            ("Contract period", "01/12/2026 to 30/11/2027", "مدة العقد"),
            ("Annual rent", "AED 42,000", "قيمة الإيجار السنوي"),
            ("Security deposit", "AED 2,100", "مبلغ التأمين"),
            ("Mode of payment", "6 cheques", "طريقة الدفع"),
        ], "This contract must be registered in Ejari.", "يجب تسجيل هذا العقد في نظام إيجاري."),

    "tenancy_abudhabi_tawtheeq": doc(
        "Abu Dhabi City Municipality - Tawtheeq", "بلدية مدينة أبوظبي - توثيق",
        "Lease contract", "عقد إيجار",
        "Lease Contract", "عقد إيجار", [
            ("Tenant", "Ana Reyes (fictional)", "المستأجر"),
            ("Property", "Flat 33, Sample Building, Mussafah", "العقار"),
            ("Contract period", "15/11/2026 to 14/11/2027", "مدة العقد"),
            ("Annual rent", "AED 55,000", "قيمة الإيجار السنوي"),
        ], "The contract must be registered (Tawtheeq).", "يجب توثيق العقد."),

    # ================================================================ second batch (sample size 50)
    # ---------------------------------------------------------------- traffic fines: more violations, all 7 emirates
    "fine_dubai_mobile_phone": doc(
        "Dubai Police - General Department of Traffic", "شرطة دبي - الإدارة العامة للمرور",
        "Traffic violation notice", "إشعار مخالفة مرورية",
        "Traffic Fine Notice", "إشعار مخالفة مرورية", [
            ("Fine number", "DXB-TF-2026-0060417", "رقم المخالفة"),
            ("Date and time", "22/10/2026 18:03", "التاريخ والوقت"),
            ("Location", "Al Ittihad Road, Deira", "الموقع"),
            ("Violation", "Using a mobile phone while driving<br>استخدام الهاتف المتحرك أثناء القيادة", "نوع المخالفة"),
            ("Plate number", "Dubai T 19034 (sample)", "رقم اللوحة"),
            ("Black points", "4", "النقاط السوداء"),
            ("Fine amount", "AED 800", "قيمة المخالفة"),
        ]),

    "fine_dubai_tailgating": doc(
        "Dubai Police - General Department of Traffic", "شرطة دبي - الإدارة العامة للمرور",
        "Traffic violation notice", "إشعار مخالفة مرورية",
        "Traffic Fine Notice", "إشعار مخالفة مرورية", [
            ("Fine number", "DXB-TF-2026-0058821", "رقم المخالفة"),
            ("Date and time", "24/10/2026 08:27", "التاريخ والوقت"),
            ("Location", "Emirates Road, Al Barsha South", "الموقع"),
            ("Violation", "Not leaving a safe distance from the vehicle in front<br>عدم ترك مسافة كافية", "نوع المخالفة"),
            ("Plate number", "Dubai H 50218 (sample)", "رقم اللوحة"),
            ("Black points", "4", "النقاط السوداء"),
            ("Fine amount", "AED 400", "قيمة المخالفة"),
            ("Pay by", "20/11/2026", "يرجى السداد قبل"),
        ]),

    "fine_dubai_parking_arabic_only": doc_ar_only(
        "هيئة الطرق والمواصلات - المواقف", "مخالفة مواقف", "مخالفة مواقف", [
            ("رقم المخالفة", "RTA-PK-2026-7790312"),
            ("التاريخ", "27/10/2026"),
            ("المنطقة", "منطقة 214، بر دبي"),
            ("نوع المخالفة", "تجاوز مدة الوقوف المدفوعة"),
            ("رقم اللوحة", "دبي ل 61270 (تجريبي)"),
            ("قيمة المخالفة", "200 درهم"),
        ]),

    "fine_dubai_tinted_windows": doc(
        "Dubai Police - General Department of Traffic", "شرطة دبي - الإدارة العامة للمرور",
        "Traffic violation notice", "إشعار مخالفة مرورية",
        "Traffic Fine Notice", "إشعار مخالفة مرورية", [
            ("Fine number", "DXB-TF-2026-0061902", "رقم المخالفة"),
            ("Date and time", "26/10/2026 21:40", "التاريخ والوقت"),
            ("Violation", "Window tint darker than the allowed limit<br>تظليل زجاج المركبة بنسبة أعلى من المسموح", "نوع المخالفة"),
            ("Plate number", "Dubai Z 31175 (sample)", "رقم اللوحة"),
            ("Fine amount", "AED 1,500", "قيمة المخالفة"),
        ]),

    "fine_dubai_statement_two_fines": doc(
        "Dubai Police - General Department of Traffic", "شرطة دبي - الإدارة العامة للمرور",
        "Statement of unpaid fines", "كشف المخالفات غير المسددة",
        "Traffic Fines Statement", "كشف مخالفات مرورية", [
            ("Plate number", "Dubai M 70461 (sample)", "رقم اللوحة"),
            ("Fine 1", "14/10/2026 - Exceeding the speed limit by not more than 20 km/h - AED 300", "المخالفة 1"),
            ("Fine 2", "19/10/2026 - Parking in a place not allowed - AED 500", "المخالفة 2"),
            ("Number of fines", "2", "عدد المخالفات"),
            ("Total amount due", "AED 800", "إجمالي المبلغ المستحق"),
        ], "The total must be paid before renewing the vehicle registration.",
        "يجب سداد الإجمالي قبل تجديد ترخيص المركبة."),

    "fine_abudhabi_redlight": doc(
        "Abu Dhabi Police - Traffic and Patrols", "شرطة أبوظبي - المرور والدوريات",
        "Traffic violation notice", "إشعار مخالفة مرورية",
        "Traffic Fine", "مخالفة مرورية", [
            ("Fine number", "AUH-2026-4502288", "رقم المخالفة"),
            ("Date and time", "23/10/2026 23:11", "التاريخ والوقت"),
            ("Location", "Abu Dhabi - Khalifa City", "الموقع"),
            ("Violation", "Jumping a red light<br>تجاوز الإشارة الضوئية الحمراء", "نوع المخالفة"),
            ("Plate number", "Abu Dhabi 7 / 30419 (sample)", "رقم اللوحة"),
            ("Black points", "12", "النقاط السوداء"),
            ("Fine amount", "AED 1,000", "قيمة المخالفة"),
        ]),

    "fine_sharjah_speeding": doc(
        "Sharjah Police - Traffic", "شرطة الشارقة - المرور",
        "Traffic violation notice", "إشعار مخالفة مرورية",
        "Traffic Fine", "مخالفة مرورية", [
            ("Fine number", "SHJ-2026-0944120", "رقم المخالفة"),
            ("Date and time", "21/10/2026 06:55", "التاريخ والوقت"),
            ("Location", "Sharjah - Al Wahda Street", "الموقع"),
            ("Violation", "Exceeding the speed limit by not more than 30 km/h<br>تجاوز السرعة المقررة بما لا يزيد عن 30 كم/ساعة", "نوع المخالفة"),
            ("Fine amount", "AED 600", "قيمة المخالفة"),
        ]),

    "fine_ajman_overtaking": doc(
        "Ajman Police - Traffic", "شرطة عجمان - المرور",
        "Traffic violation notice", "إشعار مخالفة مرورية",
        "Traffic Fine", "مخالفة مرورية", [
            ("Fine number", "AJM-2026-0113507", "رقم المخالفة"),
            ("Date and time", "17/10/2026 15:30", "التاريخ والوقت"),
            ("Violation", "Overtaking in a dangerous way<br>التجاوز بطريقة خطرة", "نوع المخالفة"),
            ("Fine amount", "AED 600", "قيمة المخالفة"),
            ("Pay by", "30/11/2026", "يرجى السداد قبل"),
        ]),

    "fine_rak_noise": doc(
        "Ras Al Khaimah Police - Traffic", "شرطة رأس الخيمة - المرور",
        "Traffic violation notice", "إشعار مخالفة مرورية",
        "Traffic Fine", "مخالفة مرورية", [
            ("Fine number", "RAK-2026-0072291", "رقم المخالفة"),
            ("Date and time", "16/10/2026 01:12", "التاريخ والوقت"),
            ("Violation", "Making noise with a modified vehicle<br>إحداث ضجيج بمركبة معدلة", "نوع المخالفة"),
            ("Fine amount", "AED 2,000", "قيمة المخالفة"),
        ]),

    "fine_uaq_expired_registration": doc(
        "Umm Al Quwain Police - Traffic", "شرطة أم القيوين - المرور",
        "Traffic violation notice", "إشعار مخالفة مرورية",
        "Traffic Fine", "مخالفة مرورية", [
            ("Fine number", "UAQ-2026-0030884", "رقم المخالفة"),
            ("Date and time", "13/10/2026 11:45", "التاريخ والوقت"),
            ("Violation", "Driving with an expired vehicle registration<br>قيادة مركبة منتهية الترخيص", "نوع المخالفة"),
            ("Fine amount", "AED 500", "قيمة المخالفة"),
        ]),

    # ---------------------------------------------------------------- residency / visa: more emirates and cases
    "residency_dubai_visit_visa_expiry": doc(
        "General Directorate of Residency and Foreigners Affairs - Dubai", "الإدارة العامة للإقامة وشؤون الأجانب - دبي",
        "Notice", "إشعار",
        "Visit Visa Expiry Notice", "إشعار انتهاء تأشيرة الزيارة", [
            ("Name", "Fatima Begum (fictional)", "الاسم"),
            ("Entry permit number", "201/2026/1/654321 (sample)", "رقم الإذن"),
            ("Visa type", "Visit visa, 60 days", "نوع التأشيرة"),
            ("Visa expiry date", "05/12/2026", "تاريخ انتهاء التأشيرة"),
        ], "Leave the country or change your status before the expiry date to avoid overstay fines.",
        "يجب المغادرة أو تعديل الوضع قبل تاريخ الانتهاء لتجنب غرامات التأخير."),

    "residency_dubai_overstay": doc(
        "General Directorate of Residency and Foreigners Affairs - Dubai", "الإدارة العامة للإقامة وشؤون الأجانب - دبي",
        "Residency violation", "مخالفة إقامة",
        "Fine Notice: Overstay", "إشعار غرامة: تجاوز مدة البقاء", [
            ("Name", "Joseph Mathew (fictional)", "الاسم"),
            ("File number", "201/2023/7/998877 (sample)", "رقم الملف"),
            ("Days of overstay", "8", "عدد الأيام"),
            ("Daily fine", "AED 50", "الغرامة اليومية"),
            ("Total fine", "AED 400", "إجمالي الغرامة"),
        ], "Pay the fine and renew your residence, or leave the country.",
        "يجب سداد الغرامة وتجديد الإقامة أو مغادرة الدولة."),

    "residency_abudhabi_renewal_reminder": doc(
        "Federal Authority for Identity, Citizenship, Customs and Port Security (ICP)",
        "الهيئة الاتحادية للهوية والجنسية والجمارك وأمن المنافذ",
        "Abu Dhabi", "أبوظبي",
        "Residence Renewal Reminder", "تذكير بتجديد الإقامة", [
            ("Name", "Grace Dela Cruz (fictional)", "الاسم"),
            ("Unified number", "784-1988-0000000-1 (sample)", "الرقم الموحد"),
            ("Residence expiry date", "30/11/2026", "تاريخ انتهاء الإقامة"),
        ], "Renew your residence permit before it expires.", "يرجى تجديد الإقامة قبل انتهائها."),

    "residency_rak_overstay": doc(
        "Federal Authority for Identity, Citizenship, Customs and Port Security (ICP)",
        "الهيئة الاتحادية للهوية والجنسية والجمارك وأمن المنافذ",
        "Ras Al Khaimah - residency violation", "رأس الخيمة - مخالفة إقامة",
        "Fine Notice: Overstay", "إشعار غرامة: تجاوز مدة البقاء", [
            ("Name", "Kamal Hossain (fictional)", "الاسم"),
            ("Days of overstay", "20", "عدد الأيام"),
            ("Daily fine", "AED 50", "الغرامة اليومية"),
            ("Total fine", "AED 1,000", "إجمالي الغرامة"),
            ("Issued on", "29/10/2026", "تاريخ الإصدار"),
        ], "Pay the fine and adjust your status or leave the country.",
        "يجب سداد الغرامة وتعديل الوضع أو مغادرة الدولة."),

    "residency_sharjah_expiry_arabic_only": doc_ar_only(
        "الهيئة الاتحادية للهوية والجنسية والجمارك وأمن المنافذ", "الشارقة - إشعار", "إشعار انتهاء الإقامة", [
            ("الاسم", "سميرة أحمد (اسم تجريبي)"),
            ("الرقم الموحد", "784-1992-0000000-2 (تجريبي)"),
            ("تاريخ انتهاء الإقامة", "20/12/2026"),
        ], "يرجى تجديد الإقامة قبل تاريخ الانتهاء لتجنب الغرامات."),

    "residency_fujairah_cancellation": doc(
        "Federal Authority for Identity, Citizenship, Customs and Port Security (ICP)",
        "الهيئة الاتحادية للهوية والجنسية والجمارك وأمن المنافذ",
        "Fujairah", "الفجيرة",
        "Residence Cancellation Notice", "إشعار إلغاء الإقامة", [
            ("Name", "Suresh Kumar (fictional)", "الاسم"),
            ("Cancellation date", "26/10/2026", "تاريخ الإلغاء"),
            ("Grace period ends", "25/12/2026", "نهاية مهلة السماح"),
        ], "Leave the country or get a new residence permit before the grace period ends.",
        "يجب مغادرة الدولة أو الحصول على إقامة جديدة قبل نهاية مهلة السماح."),

    # ---------------------------------------------------------------- tenancy: renewal, commercial, Arabic only, Sharjah
    "ejari_certificate_dubai_renewal": doc(
        "Dubai Land Department - Ejari", "دائرة الأراضي والأملاك - إيجاري",
        "Tenancy contract renewal", "تجديد عقد إيجار",
        "Ejari Registration Certificate (Renewal)", "شهادة تسجيل عقد إيجار (تجديد)", [
            ("Contract number", "0000-2026-0456789 (sample)", "رقم العقد"),
            ("Tenant", "Lakshmi Pillai (fictional)", "المستأجر"),
            ("Property", "Apartment 803, Sample Heights, Jumeirah Village Circle", "العقار"),
            ("Contract start", "15/11/2026", "تاريخ البداية"),
            ("Contract end", "14/11/2027", "تاريخ النهاية"),
            ("Annual rent", "AED 62,000", "قيمة الإيجار السنوي"),
        ]),

    "tenancy_contract_dubai_commercial": doc(
        "Government of Dubai - Land Department", "حكومة دبي - دائرة الأراضي والأملاك",
        "Unified tenancy contract", "عقد الإيجار الموحد",
        "Tenancy Contract", "عقد إيجار", [
            ("Tenant", "Sample Tailoring LLC", "المستأجر"),
            ("Landlord", "Sample Investments LLC", "المؤجر"),
            ("Property", "Shop 12, Sample Market, Naif", "العقار"),
            ("Usage", "Commercial", "الاستخدام"),
            ("Contract period", "01/01/2027 to 31/12/2027", "مدة العقد"),
            ("Annual rent", "AED 120,000", "قيمة الإيجار السنوي"),
        ], "This contract must be registered in Ejari.", "يجب تسجيل هذا العقد في نظام إيجاري."),

    "ejari_certificate_dubai_arabic_only": doc_ar_only(
        "دائرة الأراضي والأملاك - إيجاري", "تسجيل عقد إيجار", "شهادة تسجيل عقد إيجار", [
            ("رقم العقد", "0000-2026-0789012 (تجريبي)"),
            ("المستأجر", "عمر فاروق (اسم تجريبي)"),
            ("العقار", "شقة 402، برج تجريبي، القصيص"),
            ("تاريخ البداية", "01/12/2026"),
            ("تاريخ النهاية", "30/11/2027"),
            ("قيمة الإيجار السنوي", "48,000 درهم"),
        ]),

    "tenancy_sharjah_contract": doc(
        "Sharjah City Municipality", "بلدية مدينة الشارقة",
        "Lease contract", "عقد إيجار",
        "Lease Contract", "عقد إيجار", [
            ("Tenant", "Nimal Perera (fictional)", "المستأجر"),
            ("Property", "Flat 22, Sample Building, Al Nahda", "العقار"),
            ("Contract period", "01/12/2026 to 30/11/2027", "مدة العقد"),
            ("Annual rent", "AED 30,000", "قيمة الإيجار السنوي"),
        ], "The contract must be attested by the municipality.", "يجب تصديق العقد من البلدية."),

    # ---------------------------------------------------------------- not a supported document
    "not_a_document_utility_bill": doc(
        "Sample Utility Company", "شركة خدمات تجريبية",
        "Electricity and water bill", "فاتورة كهرباء ومياه",
        "Monthly Bill", "فاتورة شهرية", [
            ("Account number", "2000000000 (sample)", "رقم الحساب"),
            ("Billing period", "01/10/2026 - 31/10/2026", "فترة الفاتورة"),
            ("Electricity", "AED 312.40", "الكهرباء"),
            ("Water", "AED 96.10", "المياه"),
            ("Total due", "AED 408.50", "الإجمالي المستحق"),
            ("Due date", "20/11/2026", "تاريخ الاستحقاق"),
        ]),
}

SPECIAL = {
    "not_a_document_receipt": """<div class="receipt">
        <div class="c"><b>SAMPLE CAFE</b><br>Al Karama, Dubai<br>-------------------------</div>
        <div class="row"><span>Karak tea x2</span><span>6.00</span></div>
        <div class="row"><span>Chicken shawarma</span><span>9.00</span></div>
        <div class="row"><span>Water</span><span>2.00</span></div>
        <div class="c">-------------------------</div>
        <div class="row"><b>TOTAL AED</b><b>17.00</b></div>
        <div class="c"><br>Thank you!<br>(sample receipt)</div></div>""",
    "scam_sms_fine": """<div class="sms"><div class="from">+971 55 000 0000 (sample)<br>Today 10:41</div>
        <div class="bubble">Dubai Police: You have an unpaid traffic fine of AED 1,500. Pay within 24 hours to get a
        90% discount, or your licence will be blocked: <a>http://dubai-p0lice-fines.top/pay</a></div></div>""",
}


# ---------------------------------------------------------------- phone-photo effects

def photo(img: Image.Image, seed: int) -> Image.Image:
    """Make a clean render look like a phone photo: tilt, warm light, shadow, slight blur, noise."""
    rnd = random.Random(seed)
    img = img.convert("RGB")
    bg = Image.new("RGB", (img.width + 160, img.height + 160), (92, 84, 76))
    bg.paste(img, (80, 80))
    img = bg.rotate(rnd.uniform(-5, 5), resample=Image.BICUBIC, expand=False, fillcolor=(92, 84, 76))
    shade = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(shade)
    for i in range(img.width):
        d.line([(i, 0), (i, img.height)], fill=int(70 * i / img.width))
    img = Image.composite(Image.new("RGB", img.size, (0, 0, 0)), img, shade)
    img = ImageEnhance.Color(img).enhance(0.9)
    r, g, b = img.split()
    img = Image.merge("RGB", (r.point(lambda v: min(255, v + 8)), g, b.point(lambda v: max(0, v - 10))))
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    noise = Image.effect_noise(img.size, 18).convert("RGB")
    return Image.blend(img, noise, 0.06)


def blurry(img: Image.Image) -> Image.Image:
    return photo(img, 7).filter(ImageFilter.GaussianBlur(6))


def cropped(img: Image.Image) -> Image.Image:
    return photo(img.crop((0, 0, img.width, int(img.height * 0.5))), 11)


def main():
    OUT.mkdir(exist_ok=True)
    renders = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1000, "height": 1400}, device_scale_factor=1)
        for name, body in {**DOCS, **SPECIAL}.items():
            page.set_content(f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>")
            el = page.locator("body > div").first
            png = el.screenshot()
            renders[name] = Image.open(io.BytesIO(png))
            renders[name].save(OUT / f"{name}.png", optimize=True)
        # One PDF, to test the PDF path
        page.set_content(f"<html><head><meta charset='utf-8'><style>{CSS} @page {{ size: A4; margin: 12mm; }}</style></head>"
                         f"<body>{DOCS['tenancy_contract_dubai_unified']}</body></html>")
        page.pdf(path=str(OUT / "tenancy_contract_dubai_unified.pdf"), format="A4", print_background=True)
        browser.close()

    variants = {
        "fine_dubai_speeding__photo": photo(renders["fine_dubai_speeding"], 1),
        "ejari_certificate_dubai__photo": photo(renders["ejari_certificate_dubai"], 2),
        "residency_dubai_expiry__photo": photo(renders["residency_dubai_expiry"], 3),
        "fine_abudhabi_arabic_only__photo": photo(renders["fine_abudhabi_arabic_only"], 4),
        "fine_abudhabi_speeding__blurry": blurry(renders["fine_abudhabi_speeding"]),
        "fine_dubai_redlight_deadline__cropped": cropped(renders["fine_dubai_redlight_deadline"]),
        # second batch
        "fine_dubai_mobile_phone__photo": photo(renders["fine_dubai_mobile_phone"], 21),
        "fine_sharjah_speeding__photo": photo(renders["fine_sharjah_speeding"], 22),
        "fine_dubai_tailgating__cropped": cropped(renders["fine_dubai_tailgating"]),
        "residency_rak_overstay__photo": photo(renders["residency_rak_overstay"], 23),
        "residency_dubai_expiry__blurry": blurry(renders["residency_dubai_expiry"]),
        "ejari_certificate_dubai_renewal__photo": photo(renders["ejari_certificate_dubai_renewal"], 24),
    }
    for name, img in variants.items():
        img.save(OUT / f"{name}.jpg", quality=82)
    print(f"Wrote {len(renders)} PNGs, {len(variants)} photo-style JPGs and 1 PDF to {OUT}")


if __name__ == "__main__":
    main()
