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
