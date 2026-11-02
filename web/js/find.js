// "Find a service" results (no document needed). Same card look as an explained document,
// so Listen and the chat work the same way. Every fact shown came from the checked catalog.
import { t } from "./i18n.js";
import { esc, formatDate, localService, RTL_LANGS } from "./util.js";
import { personalNote } from "./profile.js";
import { helpHtml, staleHtml } from "./help.js";

const ICON_SEAL = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l2.4 1.8 3-.2.9 2.9 2.4 1.8-1 2.8 1 2.8-2.4 1.8-.9 2.9-3-.2L12 21l-2.4-1.8-3 .2-.9-2.9-2.4-1.8 1-2.8-1-2.8 2.4-1.8.9-2.9 3 .2z"/><path d="M8.5 12.2l2.3 2.3 4.7-4.7"/></svg>';
const ICON_WARN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4l9 16H3z"/><path d="M12 10v4M12 17v.5"/></svg>';

// One short question before Dalil can choose (for example which emirate)
export function renderQuestion(d) {
  const lang = d.language || "en";
  const dir = RTL_LANGS.includes(lang) ? "rtl" : "ltr";
  const tr = (key) => t(key, lang);
  return `
    <article class="sheet find-question" dir="${dir}" lang="${esc(lang)}">
      ${d.mock ? `<span class="mock-flag">${esc(tr("mock"))}</span>` : ""}
      <p class="doc-kind">${esc(tr("find_one_question"))}</p>
      <h2>${esc(d.question)}</h2>
      <div class="chat-chips find-options">
        ${(d.options || []).map((o) => `<button type="button" class="chat-chip" data-answer="${esc(o)}" dir="auto">${esc(o)}</button>`).join("")}
      </div>
      <form class="chat-form" id="find-answer-form" autocomplete="off">
        <label class="visually-hidden" for="find-answer">${esc(tr("find_answer_label"))}</label>
        <input type="text" id="find-answer" dir="auto" maxlength="120" placeholder="${esc(tr("find_answer_label"))}">
        <button class="chat-send" type="submit" aria-label="${esc(tr("chat_send"))}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5M6 11l6-6 6 6"/></svg></button>
      </form>
    </article>`;
}

// The service Dalil found, or "not checked yet" with the official portal
export function renderFound(d) {
  const lang = d.language || "en";
  const dir = RTL_LANGS.includes(lang) ? "rtl" : "ltr";
  const tr = (key) => t(key, lang);
  const e = d.explanation || {};
  const s = localService(d.service, lang);
  if (!s) {
    return `
      <article class="sheet" dir="${dir}" lang="${esc(lang)}">
        ${d.mock ? `<span class="mock-flag">${esc(tr("mock"))}</span>` : ""}
        <p class="doc-kind">${esc(tr("find_none_kind"))}</p>
        <h2>${esc(e.what_it_is || tr("find_none_text"))}</h2>
        <div class="listen-slot"></div>
        <a class="btn" href="${esc(d.link)}" target="_blank" rel="noopener">${esc(tr("find_open_portal"))}</a>
        <div class="trust"><p class="muted">${esc(d.disclaimer || "")}</p></div>
      </article>`;
  }
  return `
    <article class="sheet" dir="${dir}" lang="${esc(lang)}">
      ${d.mock ? `<span class="mock-flag">${esc(tr("mock"))}</span>` : ""}
      <p class="doc-kind">${esc(s.service_name)} · ${esc(s.authority)}</p>
      <h2>${esc(e.what_it_is)}</h2>
      <div class="listen-slot"></div>
      ${d.personal ? `<p class="personal-note">${esc(personalNote(d.personal, lang, s.authority))}</p>` : ""}
      ${staleHtml(s, lang)}
      ${d.number_check === "template" ? `<p class="check-note">${esc(tr("number_check_template"))}</p>` : ""}
      <div class="explain">
        <div><h3>${esc(tr("h_cost"))}</h3><p>${esc(e.cost)}</p></div>
        <div><h3>${esc(tr("find_h_when"))}</h3><p>${esc(e.deadline)}</p></div>
        ${(e.next_steps || []).length ? `<div><h3>${esc(tr("h_steps"))}</h3>
          <ol class="steps">${e.next_steps.map((x) => `<li><span>${esc(x)}</span></li>`).join("")}</ol></div>` : ""}
      </div>
      <a class="btn" data-official="find" href="${esc(d.link)}" target="_blank" rel="noopener">${esc(tr("open_official"))}</a>
      ${helpHtml(s, lang)}
      <div class="trust">
        ${s.verified
          ? `<p class="seal">${ICON_SEAL}<span>${esc(tr("verified"))}${s.last_checked ? ` (${esc(formatDate(s.last_checked, lang))})` : ""}</span></p>`
          : `<p class="seal unverified">${ICON_WARN}<span>${esc(tr("unverified"))}</span></p>`}
        ${s.source ? `<p class="muted">${esc(tr("source"))}: ${esc(s.source)}</p>` : ""}
        <p class="muted">${esc(d.disclaimer || "")}</p>
      </div>
    </article>`;
}
