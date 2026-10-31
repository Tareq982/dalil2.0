// Ask Dalil (issue #19): follow-up questions about the scanned document.
// Only the non-sensitive details go to the server (the server filters again).
// Answers come from Dalil's checked data, plus a live search limited to official UAE sites.
// People can type or speak in any of Dalil's languages: the server detects the language of
// each question and answers in it (app/langdetect.py), so the chat follows the person.
import { LANGUAGES, t } from "./i18n.js";
import { esc, LOCALES, RTL_LANGS } from "./util.js";

const SAFE_FIELDS = ["doc_type", "emirate", "issuing_authority", "subject", "amount_aed", "issue_date", "deadline_date"];
const MAX_QUESTIONS = 12;
const ICON_SEND = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5M6 11l6-6 6 6"/></svg>';
const ICON_MIC = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21"/></svg>';
// Speech-to-text built into the browser (Chrome, Edge, Safari). Where it's missing, no mic button.
const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const ICON_CHAT = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5h14a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-7l-4 3v-3H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z"/><path d="M8 10h8M8 13h5"/></svg>';

// Builds the chat card for one result and returns the element.
export function chatCard(d) {
  const lang = d.language || "en";
  const tr = (key) => t(key, lang);
  const f = d.fields || {};
  const fields = Object.fromEntries(SAFE_FIELDS.filter((k) => f[k] != null && f[k] !== "").map((k) => [k, f[k]]));
  const suggested = (d.explanation?.suggested_questions || []).filter(Boolean);
  const chips = suggested.length ? suggested : [tr("chat_q1"), tr("chat_q2"), tr("chat_q3")];
  const messages = [];
  let busy = false;
  let chatLang = lang; // follows the language of the person's last question
  let recognition = null;

  const card = document.createElement("section");
  card.className = "chat";
  card.id = "chat";
  card.dir = RTL_LANGS.includes(lang) ? "rtl" : "ltr";
  card.lang = lang;
  card.setAttribute("aria-labelledby", "chat-title");
  card.innerHTML = `
    <div class="chat-head">
      <span class="icon-circle small">${ICON_CHAT}</span>
      <div><h3 id="chat-title">${esc(tr("chat_title"))}</h3>
        <p class="muted">${esc(tr("chat_lede"))}</p></div>
    </div>
    <div class="chat-log" id="chat-log" aria-live="polite"></div>
    <div class="chat-chips" id="chat-chips">
      ${chips.map((q) => `<button type="button" class="chat-chip" dir="auto">${esc(q)}</button>`).join("")}
    </div>
    <form class="chat-form" id="chat-form" autocomplete="off">
      <label class="visually-hidden" for="chat-input">${esc(tr("chat_placeholder"))}</label>
      <input type="text" id="chat-input" dir="auto" maxlength="500" placeholder="${esc(tr("chat_placeholder"))}" enterkeyhint="send">
      ${Recognition ? `<button class="chat-mic" type="button" aria-pressed="false" aria-label="${esc(tr("chat_mic"))}" title="${esc(tr("chat_mic"))}">${ICON_MIC}</button>` : ""}
      <button class="chat-send" type="submit" aria-label="${esc(tr("chat_send"))}" disabled>${ICON_SEND}</button>
    </form>
    <p class="chat-note muted">${esc(tr("chat_privacy"))}</p>`;

  const log = card.querySelector("#chat-log");
  const input = card.querySelector("#chat-input");
  const send = card.querySelector(".chat-send");
  const form = card.querySelector("#chat-form");
  const mic = card.querySelector(".chat-mic");
  mic?.addEventListener("click", listen);

  input.addEventListener("input", () => { send.disabled = busy || !input.value.trim(); });
  form.addEventListener("submit", (e) => { e.preventDefault(); ask(input.value); });
  card.querySelectorAll(".chat-chip").forEach((chip) => chip.addEventListener("click", () => {
    chip.remove();
    ask(chip.textContent);
  }));

  function bubble(role, html, extra = "") {
    const el = document.createElement("div");
    el.className = `bubble ${role} ${extra}`.trim();
    el.dir = "auto";
    el.innerHTML = html;
    log.appendChild(el);
    el.scrollIntoView({ behavior: "smooth", block: "nearest" });
    return el;
  }

  // Ask by voice: the browser turns speech into text, then it is sent like a typed question
  // (so the server detects its language the same way). The browser has to be told which
  // language to listen for: the chat's current language, which starts as the answer language.
  function listen() {
    if (recognition) { recognition.stop(); return; }
    if (busy) return;
    recognition = new Recognition();
    recognition.lang = LOCALES[chatLang] || chatLang;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    let heard = "";
    let failed = false;
    mic.classList.add("listening");
    mic.setAttribute("aria-pressed", "true");
    mic.setAttribute("aria-label", tr("chat_mic_stop"));
    input.placeholder = tr("chat_listening");
    recognition.onresult = (e) => {
      heard = [...e.results].map((r) => r[0].transcript).join("");
      input.value = heard; // show the words as they are heard
      send.disabled = !heard.trim();
    };
    recognition.onerror = (e) => {
      if (e.error !== "aborted") failed = true;
    };
    recognition.onend = () => {
      recognition = null;
      mic.classList.remove("listening");
      mic.setAttribute("aria-pressed", "false");
      mic.setAttribute("aria-label", tr("chat_mic"));
      input.placeholder = tr("chat_placeholder");
      if (heard.trim()) ask(heard);
      else if (failed) bubble("bot", esc(tr("chat_mic_error")), "note");
    };
    try { recognition.start(); } catch { recognition.onend(); }
  }

  async function ask(text) {
    const q = String(text || "").trim();
    if (!q || busy) return;
    if (messages.filter((m) => m.role === "user").length >= MAX_QUESTIONS) {
      bubble("bot", esc(tr("chat_limit")), "note");
      return;
    }
    busy = true;
    input.value = "";
    send.disabled = true;
    messages.push({ role: "user", content: q });
    bubble("user", esc(q));
    const typing = bubble("bot", `<span class="typing"><i></i><i></i><i></i></span><span class="typing-label">${esc(tr("chat_searching"))}</span>`, "pending");

    try {
      const r = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fields, service_id: d.service_id, lang: chatLang, messages }),
      });
      const out = await r.json().catch(() => ({ error: `Server error ${r.status}` }));
      if (!r.ok) throw new Error(out.error || `Server error ${r.status}`);
      messages.push({ role: "assistant", content: out.answer });
      // The reply is in the language of the question: label it when that changes.
      const replyLang = LANGUAGES[out.language] ? out.language : chatLang;
      const rt = (key) => t(key, replyLang);
      const switched = replyLang !== chatLang;
      chatLang = replyLang;
      typing.classList.remove("pending");
      typing.lang = replyLang;
      typing.innerHTML = (switched ? `<small class="reply-lang">${esc(rt("chat_replying_in").replace("{lang}", LANGUAGES[replyLang]))}</small>` : "")
        + formatAnswer(out.answer) + sourcesHtml(out, rt);
    } catch (err) {
      messages.pop(); // let them ask again
      typing.classList.remove("pending");
      typing.classList.add("error");
      typing.innerHTML = `${esc(tr("chat_error"))}<small>${esc(err.message)}</small>`;
    }
    busy = false;
    send.disabled = !input.value.trim();
    typing.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  return card;
}

// Plain text from the AI -> safe HTML: paragraphs, "- " bullets, **bold** removed.
function formatAnswer(text) {
  const lines = String(text || "").replace(/\*\*/g, "").split(/\n+/).map((l) => l.trim()).filter(Boolean);
  let html = "", list = false;
  for (const line of lines) {
    const item = line.match(/^(?:[-•*]|\d+[.)])\s+(.*)$/);
    if (item && !list) { html += '<ul dir="auto">'; list = true; }
    if (!item && list) { html += "</ul>"; list = false; }
    // dir="auto": each line reads right-to-left or left-to-right by its own first letters
    html += item ? `<li dir="auto">${esc(item[1])}</li>` : `<p dir="auto">${esc(line)}</p>`;
  }
  return html + (list ? "</ul>" : "");
}

function sourcesHtml(out, tr) {
  const sources = (out.sources || []).filter((s) => /^https:\/\//.test(s.url));
  const label = out.searched ? tr("chat_sources_live") : out.live === false ? tr("chat_offline") : tr("chat_sources");
  if (!sources.length) return `<p class="chat-src-label">${esc(label)}</p>`;
  return `<p class="chat-src-label">${esc(label)}</p>
    <div class="chat-sources">${sources.map((s) => {
      let host = s.url;
      try { host = new URL(s.url).hostname.replace(/^www\./, ""); } catch {}
      return `<a href="${esc(s.url)}" target="_blank" rel="noopener" title="${esc(s.title)}"><span>${esc(host)}</span></a>`;
    }).join("")}</div>`;
}
