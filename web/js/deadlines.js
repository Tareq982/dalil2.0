// My deadlines tab (issue #13): saved deadlines, days left, Add to calendar.
import { t } from "./i18n.js";
import { esc, formatAED, formatDate, RTL_LANGS } from "./util.js";
import { daysUntil, removeDeadline, sortedDeadlines } from "./store.js";
import { downloadICS } from "./calendar.js";

let panel;

export function render(el) {
  panel = el;
  draw();
  window.addEventListener("dalil:deadlines-changed", draw);
}

export function onShow() {
  draw(); // days left change every day, so redraw each time the tab opens
}

function badge(days) {
  if (days === null) return "";
  const urgent = days <= 7;
  const text = days < 0 ? `${-days} ${t("stamp_overdue")}` : days === 0 ? t("stamp_today")
    : `${days} ${days === 1 ? t("stamp_day_left") : t("stamp_days_left")}`;
  return `<span class="days${urgent ? " urgent" : ""}">${esc(text)}</span>`;
}

function draw() {
  const items = sortedDeadlines();
  const list = items.map((d) => {
    const days = daysUntil(d.date);
    const kind = t(`kind_${d.kind || "other"}`);
    const dateLabel = d.date_is_reminder ? t("dl_reminder_on") : t("dl_due");
    const dir = RTL_LANGS.includes(d.answer_lang) ? "rtl" : "ltr";
    return `
      <li class="deadline" data-id="${esc(d.id)}">
        <div class="deadline-head">
          <div>
            <p class="deadline-kind">${esc(d.authority ? t("kind_line").replace("{kind}", kind).replace("{authority}", d.authority) : kind)}</p>
            <p class="deadline-date">${esc(dateLabel)} <span class="mark">${esc(formatDate(d.date))}</span></p>
          </div>
          ${badge(days)}
        </div>
        ${d.summary ? `<p class="deadline-summary" dir="${dir}" lang="${esc(d.answer_lang || "en")}">${esc(d.summary)}</p>` : ""}
        ${d.amount_aed != null ? `<p class="deadline-amount">${esc(t("fact_amount"))}: <strong>${esc(formatAED(d.amount_aed))}</strong></p>` : ""}
        <div class="deadline-actions">
          <button class="btn" data-action="calendar">${esc(t("dl_add_calendar"))}</button>
          ${d.official_url ? `<a class="btn btn-quiet" href="${esc(d.official_url)}" target="_blank" rel="noopener">${esc(t("open_official"))}</a>` : ""}
          <button class="link-btn" data-action="remove">${esc(t("dl_remove"))}</button>
        </div>
      </li>`;
  }).join("");

  panel.innerHTML = `
    <h1>${esc(t("tab_deadlines"))}</h1>
    <p class="lede">${esc(t("dl_lede"))}</p>
    ${items.length ? `<ul class="deadline-list">${list}</ul>` : `
      <div class="placeholder">
        <p>${esc(t("dl_empty"))}</p>
        <a class="btn" href="#scan" style="margin-top:16px">${esc(t("dl_scan"))}</a>
      </div>`}`;

  panel.querySelectorAll(".deadline").forEach((li) => {
    const item = items.find((d) => d.id === li.dataset.id);
    li.querySelector('[data-action="calendar"]').addEventListener("click", () => {
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
    li.querySelector('[data-action="remove"]').addEventListener("click", () => removeDeadline(item.id));
  });
}
