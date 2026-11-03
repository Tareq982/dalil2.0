// Small helpers shared by the tabs.

// Escape text before putting it inside HTML (never insert raw AI or user text).
export function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

export const RTL_LANGS = ["ar", "ur"];

// Full locale per language: used for dates and amounts, and by the microphone in Ask Dalil.
export const LOCALES = { en: "en-GB", ar: "ar-AE", hi: "hi-IN", ur: "ur-PK", tl: "fil-PH", bn: "bn-BD", ml: "ml-IN" };

// The interface language (set on <html lang> by i18n.js), used when no language is given.
const uiLang = () => document.documentElement.lang || "en";

// "2026-11-19" -> "19 Nov 2026" in the reader's language, with the same digits as the paper.
export function formatDate(iso, lang = uiLang()) {
  if (!iso) return "";
  const d = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(d.getTime())) return iso;
  try {
    return new Intl.DateTimeFormat(LOCALES[lang] || lang, {
      day: "numeric", month: "short", year: "numeric", numberingSystem: "latn",
    }).format(d);
  } catch {
    return iso;
  }
}

export function formatAED(amount, lang = uiLang()) {
  if (amount === null || amount === undefined || amount === "") return "";
  const n = Number(amount);
  if (Number.isNaN(n)) return String(amount);
  try {
    return `AED ${new Intl.NumberFormat(LOCALES[lang] || lang, { maximumFractionDigits: 2, numberingSystem: "latn" }).format(n)}`;
  } catch {
    return `AED ${n}`;
  }
}

// A checked service in the answer language (data/services.json "names": names, fee notes, deadline
// rules and steps), falling back to English. Translations keep the same numbers (tests/test_finder.py).
// The official link, fee amounts and rules are the same in every language.
export function localService(service, lang) {
  if (!service) return service;
  const n = (service.names || {})[lang] || {};
  const help = service.help ? { ...service.help, name: n.help || service.help.name } : service.help;
  return { ...service, service_name: n.service_name || service.service_name, authority: n.authority || service.authority, help,
    fee_note: n.fee_note || service.fee_note, deadline_rule: n.deadline_rule || service.deadline_rule,
    next_steps: n.next_steps || service.next_steps, emirate_name: n.emirate_name || service.emirate };
}
