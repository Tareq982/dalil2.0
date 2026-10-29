// Small helpers shared by the tabs.

// Escape text before putting it inside HTML (never insert raw AI or user text).
export function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

export const RTL_LANGS = ["ar", "ur"];

const LOCALES = { en: "en-GB", ar: "ar-AE", hi: "hi-IN", ur: "ur-PK", tl: "fil-PH", bn: "bn-BD", ml: "ml-IN" };

// "2026-11-19" -> "19 Nov 2026" in the reader's language, with the same digits as the paper.
export function formatDate(iso, lang = "en") {
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

export function formatAED(amount, lang = "en") {
  if (amount === null || amount === undefined || amount === "") return "";
  const n = Number(amount);
  if (Number.isNaN(n)) return String(amount);
  try {
    return `AED ${new Intl.NumberFormat(lang, { maximumFractionDigits: 2 }).format(n)}`;
  } catch {
    return `AED ${n}`;
  }
}
