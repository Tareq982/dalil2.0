// My documents tab: everything the user scanned and kept (fines, notices, contracts),
// with deadlines, paid status and Add to calendar. Synced across devices when signed in.
import { t } from "./i18n.js";
import { esc, formatAED, formatDate, RTL_LANGS } from "./util.js";
import { currentAccount, daysUntil, removeDocument, sortedDocuments, updateDocument } from "./store.js";
import { downloadICS } from "./calendar.js";
import { openAccount } from "./account.js";

let panel;

let listening = false;

export function render(el) {
  panel = el;
  draw();
  if (!listening) { // render() runs again when the language changes: only listen once
    listening = true;
    window.addEventListener("dalil:documents-changed", () => { if (!panel.hidden) draw(); });
  }
}

export function onShow() {
  draw(); // days left change every day, so redraw each time the tab opens
}

function badge(d) {
  if (d.status === "paid") return `<span class="days paid">${esc(t("doc_paid"))}</span>`;
  const days = daysUntil(d.date);
  if (days === null) return "";
  const text = days < 0 ? `${-days} ${t("stamp_overdue")}` : days === 0 ? t("stamp_today")
    : `${days} ${days === 1 ? t("stamp_day_left") : t("stamp_days_left")}`;
  return `<span class="days${days <= 7 ? " urgent" : days <= 14 ? " soon" : ""}">${esc(text)}</span>`;
}

function card(d) {
  const kind = t(`kind_${d.kind || "other"}`);
  const head = d.authority ? t("kind_line").replace("{kind}", kind).replace("{authority}", d.authority) : kind;
  const dateLine = d.date
    ? `${esc(d.date_is_reminder ? t("dl_reminder_on") : t("dl_due"))} ${esc(formatDate(d.date))}`
    : esc(t("doc_no_deadline"));
  const dir = RTL_LANGS.includes(d.answer_lang) ? "rtl" : "ltr";
  const paid = d.status === "paid";
  return `
    <li class="deadline${paid ? " is-paid" : ""}" data-id="${esc(d.id)}">
      <div class="deadline-head">
        <div><p class="deadline-kind">${esc(head)}</p><p class="deadline-date">${dateLine}</p></div>
        ${badge(d)}
      </div>
      ${d.summary ? `<p class="deadline-summary" dir="${dir}" lang="${esc(d.answer_lang || "en")}">${esc(d.summary)}</p>` : ""}
      ${d.amount_aed != null ? `<p class="deadline-amount">${esc(t("fact_amount"))}: <strong>${esc(formatAED(d.amount_aed))}</strong></p>` : ""}
      <div class="deadline-actions">
        ${d.date && !paid ? `<button class="btn" data-action="calendar">${esc(t("dl_add_calendar"))}</button>` : ""}
        ${d.official_url ? `<a class="btn btn-quiet" href="${esc(d.official_url)}" target="_blank" rel="noopener">${esc(t("open_official"))}</a>` : ""}
        ${d.kind === "traffic_fine" || d.amount_aed != null
          ? `<button class="btn btn-quiet" data-action="paid">${esc(t(paid ? "doc_mark_unpaid" : "doc_mark_paid"))}</button>` : ""}
        <button class="link-btn" data-action="remove">${esc(t("dl_remove"))}</button>
      </div>
    </li>`;
}

function draw() {
  const items = sortedDocuments();
  const email = currentAccount();
  panel.innerHTML = `
    <h1>${esc(t("tab_deadlines"))}</h1>
    <div class="sync-banner">
      ${email
        ? `<p><strong>${esc(t("doc_synced"))}</strong> ${esc(email)}</p><p class="muted">${esc(t("doc_synced_hint"))}</p>`
        : `<p>${esc(t("doc_local"))}</p><button class="btn btn-quiet small" id="doc-signin">${esc(t("doc_sign_in_sync"))}</button>`}
    </div>
    ${items.length ? `<ul class="deadline-list">${items.map(card).join("")}</ul>` : `
      <div class="placeholder">
        <p>${esc(t("dl_empty"))}</p>
        <a class="btn" href="#scan" style="margin-top:16px">${esc(t("dl_scan"))}</a>
      </div>`}`;

  panel.querySelector("#doc-signin")?.addEventListener("click", openAccount);
  panel.querySelectorAll(".deadline").forEach((li) => {
    const item = items.find((d) => d.id === li.dataset.id);
    li.querySelector('[data-action="calendar"]')?.addEventListener("click", () => {
      const kind = t(`kind_${item.kind || "other"}`);
      downloadICS({
        id: item.id,
        title: `${kind}${item.authority ? ` (${item.authority})` : ""}: ${t("dl_calendar_title")}`,
        date: item.date,
        description: [item.summary, item.amount_aed != null ? formatAED(item.amount_aed) : "", item.official_url, t("disclaimer_short")]
          .filter(Boolean).join("\n"),
        url: item.official_url,
      });
    });
    li.querySelector('[data-action="paid"]')?.addEventListener("click", () =>
      updateDocument(item.id, { status: item.status === "paid" ? "open" : "paid" }));
    li.querySelector('[data-action="remove"]').addEventListener("click", () => removeDocument(item.id));
  });
}
