// "Show this to staff": a short note in Arabic and English that says what the person needs.
// The official call centres and counters work in Arabic and English, so a phone number alone
// doesn't help someone who reads Urdu or Malayalam. This card lets them show the screen at the
// counter, play it aloud on a call, or copy it into an email.
//
// Written by code, not by the AI: every line comes from the checked catalog (data/services.json,
// the service and authority names in Arabic and English) or from what Dalil read on the paper
// (reference number, amount, deadline). Nothing here can be invented.
import { t } from "./i18n.js";
import { esc, formatAED, formatDate, localService } from "./util.js";

// The person's language, named in Arabic and English, so staff know what they speak.
const LANGUAGE_NAMES_EN = { en: "English", ar: "Arabic", hi: "Hindi", ur: "Urdu", tl: "Tagalog", bn: "Bengali", ml: "Malayalam" };
const LANGUAGE_NAMES_AR = { en: "الإنجليزية", ar: "العربية", hi: "الهندية", ur: "الأردية", tl: "التاغالوغية", bn: "البنغالية", ml: "المالايالامية" };

const TEMPLATE = {
  en: {
    hello: "Hello. I need help with this:",
    service: "Service", authority: "Government entity", document: "Document", reference: "Reference number", amount: "Amount", deadline: "Deadline",
    my_language: "My language is {language}. Please speak slowly, or write your answer down for me. Thank you.",
    thanks: "Thank you.",
  },
  ar: {
    hello: "مرحباً، أحتاج إلى مساعدة في ما يلي:",
    service: "الخدمة", authority: "الجهة", document: "المستند", reference: "رقم المرجع", amount: "المبلغ", deadline: "الموعد النهائي",
    my_language: "لغتي هي {language}. أرجو التحدث ببطء، أو كتابة الرد لي. شكراً.",
    thanks: "شكراً.",
  },
};

const ICON_COPY = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></svg>';
const ICON_PEOPLE = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0"/><path d="M16 5.5a3 3 0 0 1 0 5M18 20a6 6 0 0 0-2.5-4.9"/></svg>';

/**
 * The note in one language ("ar" or "en"), as lines of text.
 * service: a checked service (or null); fields: what Dalil read on the paper (or {});
 * personLang: the language the person reads.
 */
export function staffLines(service, fields, personLang, noteLang) {
  const tp = TEMPLATE[noteLang];
  const f = fields || {};
  const s = service ? localService(service, noteLang) : null;
  const lines = [tp.hello];
  if (s) lines.push(`${tp.service}: ${s.service_name}`, `${tp.authority}: ${s.authority}`);
  if (f.doc_type) {
    const kind = t(`kind_${f.doc_type}`, noteLang);
    // The authority printed on the paper is only added when there is no checked service to name it
    const doc = !s && f.issuing_authority
      ? t("kind_line", noteLang).replace("{kind}", kind).replace("{authority}", f.issuing_authority)
      : kind;
    lines.push(`${tp.document}: ${doc}`);
  }
  if (f.reference_number) lines.push(`${tp.reference}: ${f.reference_number}`);
  if (f.amount_aed != null && f.amount_aed !== "") lines.push(`${tp.amount}: ${formatAED(f.amount_aed, noteLang)}`);
  if (f.deadline_date) lines.push(`${tp.deadline}: ${formatDate(f.deadline_date, noteLang)}`);
  if (lines.length === 1) return []; // nothing to say yet
  // Arabic and English speakers don't need the "my language is" line
  if (personLang && personLang !== "en" && personLang !== "ar") {
    const name = noteLang === "ar" ? LANGUAGE_NAMES_AR[personLang] : LANGUAGE_NAMES_EN[personLang];
    lines.push(tp.my_language.replace("{language}", name || personLang));
  } else {
    lines.push(tp.thanks);
  }
  return lines;
}

/** Both notes as plain text (for Copy and for tests). */
export function staffText(service, fields, personLang) {
  return {
    ar: staffLines(service, fields, personLang, "ar").join("\n"),
    en: staffLines(service, fields, personLang, "en").join("\n"),
  };
}

/** The card, with its heading and buttons in the person's language. Empty when there is nothing to say. */
export function staffCardHtml(service, fields, lang) {
  const ar = staffLines(service, fields, lang, "ar");
  const en = staffLines(service, fields, lang, "en");
  if (!ar.length || !en.length) return "";
  const tr = (key) => t(key, lang);
  const block = (noteLang, lines, label) => `
      <div class="staff-note" lang="${noteLang}" dir="${noteLang === "ar" ? "rtl" : "ltr"}">
        <p class="staff-lang">${esc(label)}</p>
        ${lines.map((l) => `<p>${esc(l)}</p>`).join("")}
      </div>`;
  return `
    <section class="staff-card" aria-label="${esc(tr("staff_title"))}">
      <div class="staff-head">
        <span class="hh-icon">${ICON_PEOPLE}</span>
        <div class="hh-body">
          <p class="hh-title">${esc(tr("staff_title"))}</p>
          <p class="hh-text">${esc(tr("staff_text"))}</p>
        </div>
      </div>
      ${block("ar", ar, "العربية")}
      ${block("en", en, "English")}
      <div class="staff-actions">
        <div class="staff-listen-slot"></div>
        <button type="button" class="listen-btn staff-copy" data-copied="${esc(tr("staff_copied"))}">${ICON_COPY}<span>${esc(tr("staff_copy"))}</span></button>
      </div>
    </section>`;
}

/** Copy button: both notes, Arabic first, ready to paste into an email or a message. */
export function wireStaffCard(root) {
  const card = root && root.querySelector(".staff-card");
  if (!card) return;
  const btn = card.querySelector(".staff-copy");
  btn.addEventListener("click", async () => {
    const text = [...card.querySelectorAll(".staff-note")]
      .map((n) => [...n.querySelectorAll("p:not(.staff-lang)")].map((p) => p.textContent).join("\n"))
      .join("\n\n");
    try {
      await navigator.clipboard.writeText(text);
      const label = btn.querySelector("span");
      const before = label.textContent;
      label.textContent = btn.dataset.copied;
      setTimeout(() => { label.textContent = before; }, 2000);
    } catch { /* clipboard blocked: the text is still on screen to show */ }
  });
}
