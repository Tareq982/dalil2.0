// Small helpers shared by the tabs.

// Escape text before putting it inside HTML (never insert raw AI or user text).
export function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

export const RTL_LANGS = ["ar", "ur"];

// "2026-11-19" -> "19 Nov 2026" in the reader's language (falls back to the raw text).
export function formatDate(iso, lang = "en") {
  if (!iso) return "";
  const d = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(d.getTime())) return iso;
  try {
    return new Intl.DateTimeFormat(lang, { day: "numeric", month: "short", year: "numeric" }).format(d);
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
