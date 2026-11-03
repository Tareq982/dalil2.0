// Handoff to a person, and a warning when checked data is getting old.
// The challenge asks for "a seamless handoff to completion or human assistance": every answer
// tied to a checked service shows that authority's official call centre (data/services.json,
// "help", each number read on a government website, see data/sources.md).
import { t } from "./i18n.js";
import { esc, localService } from "./util.js";

const ICON_PHONE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/></svg>';
const STALE_DAYS = 90;

export function helpHtml(service, lang) {
  const h = service && localService(service, lang).help;
  if (!h || !h.phone) return "";
  const tr = (key) => t(key, lang);
  const tel = h.phone.replace(/[^\d+]/g, "");
  return `
    <div class="human-help">
      <span class="hh-icon">${ICON_PHONE}</span>
      <div class="hh-body">
        <p class="hh-title">${esc(tr("help_title"))}</p>
        <p class="hh-text">${esc(tr("help_text"))}</p>
        <p class="hh-line"><a class="hh-call" href="tel:${esc(tel)}" dir="ltr" aria-label="${esc(tr("help_call"))} ${esc(h.name)} ${esc(h.phone)}">${esc(h.phone)}</a>
          <span class="hh-name" dir="ltr">${esc(h.name)}</span></p>
        ${h.page ? `<a class="hh-more" href="${esc(h.page)}" target="_blank" rel="noopener">${esc(tr("help_more"))}</a>` : ""}
      </div>
    </div>`;
}

// Checked more than 3 months ago: say so, so nobody relies on old fees or rules
export function staleHtml(service, lang, today = new Date()) {
  if (!service || !service.last_checked) return "";
  const days = (today - new Date(`${service.last_checked}T00:00:00`)) / 86400000;
  return days > STALE_DAYS ? `<p class="check-note">${esc(t("stale_note", lang))}</p>` : "";
}

// Placeholder for the pilot: a live chat with a support agent, translated both ways. Not built in
// the prototype; it shows what each side would see, using a sample question.
const ICON_CHAT = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16v10H9l-5 4z"/><path d="M8 9h8M8 12h5"/></svg>';

export function agentChatHtml(lang) {
  const tr = (key) => t(key, lang);
  // The agent reads Arabic; an Arabic reader's message would reach an English-speaking agent instead
  const agentLang = lang === "ar" ? "en" : "ar";
  return `
    <div class="human-help agent-chat" aria-disabled="true">
      <span class="hh-icon">${ICON_CHAT}</span>
      <div class="hh-body">
        <p class="hh-title">${esc(tr("agent_title"))} <span class="soon-badge">${esc(tr("agent_soon"))}</span></p>
        <p class="hh-text">${esc(tr("agent_text"))}</p>
        <div class="agent-preview" aria-hidden="true">
          <div class="agent-bubble you"><span>${esc(tr("agent_you"))}</span><p lang="${esc(lang)}" dir="auto">${esc(tr("agent_sample"))}</p></div>
          <div class="agent-bubble them"><span>${esc(tr("agent_sees"))}</span><p lang="${agentLang}" dir="auto">${esc(t("agent_sample", agentLang))}</p></div>
        </div>
        <button type="button" class="listen-btn" disabled>${esc(tr("agent_soon"))}</button>
      </div>
    </div>`;
}
