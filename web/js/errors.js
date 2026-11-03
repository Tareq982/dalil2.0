// Errors in the person's language. The server sends a short "code" with each error
// (app/main.py, app/accounts.py); its English "error" text is kept for the team's logs only.
import { t, STRINGS } from "./i18n.js";
import { esc } from "./util.js";

// Turn a failed reply into an Error that remembers the server's code
export function apiError(data, status) {
  const err = new Error((data && data.error) || `Server error ${status}`);
  err.code = (data && data.code) || null;
  return err;
}

// The message to show: the translated one for a known code, otherwise a general one
export function errorText(err, lang) {
  const key = err && err.code ? `err_${err.code}` : "";
  return key && key in STRINGS.en ? t(key, lang) : t("err_generic", lang);
}

// For error boxes: the translated message, plus the technical details folded away (for the team)
export function errorHtml(err, lang) {
  const technical = !err || !err.code || err.code === "ai_error";
  return `<small>${esc(errorText(err, lang))}</small>${technical && err && err.message ? `
    <details class="err-details"><summary>${esc(t("err_details", lang))}</summary><code dir="ltr">${esc(err.message)}</code></details>` : ""}`;
}
