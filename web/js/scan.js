// Scan tab (issue #12): photo in -> marked-up explanation out.
// Two modes: "Explain a document" (/analyze) and "Is this message real?" (/check-message):
// a screenshot or pasted text of a "pay your fine" SMS, email or website, checked before paying.
import { getLanguage, LANGUAGES, t } from "./i18n.js";
import { esc, formatAED, formatDate, RTL_LANGS } from "./util.js";
import { addDocument, currentAccount, removeDocument, updateDocument } from "./store.js";
import { openAccount } from "./account.js";
import { chatCard } from "./chat.js";

let panel;
let upload = null; // { blob, name, previewUrl? }
let mode = "doc"; // "doc" = explain a document, "msg" = is this message real?

// Texts that change with the mode: element id -> [key in doc mode, key in msg mode]
const MODE_TEXT = {
  "scan-title": ["scan_title", "msg_title"],
  "scan-lede": ["scan_lede", "msg_lede"],
  "lang-label": ["answer_language", "msg_answer_language"],
  "go": ["explain_button", "msg_button"],
  "privacy-text": ["privacy", "msg_privacy"],
};

const ICON_CAMERA = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9a2 2 0 0 1 2-2h1.7l1.4-2h5.8l1.4 2H18a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/><circle cx="12" cy="13.2" r="3.4"/></svg>';
const ICON_LOCK = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="10" width="14" height="10" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></svg>';
const ICON_SEAL = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l2.4 1.8 3-.2.9 2.9 2.4 1.8-1 2.8 1 2.8-2.4 1.8-.9 2.9-3-.2L12 21l-2.4-1.8-3 .2-.9-2.9-2.4-1.8 1-2.8-1-2.8 2.4-1.8.9-2.9 3 .2z"/><path d="M8.5 12.2l2.3 2.3 4.7-4.7"/></svg>';
const ICON_WARN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4l9 16H3z"/><path d="M12 10v4M12 17v.5"/></svg>';
const ICON_STOP = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8.2 3h7.6L21 8.2v7.6L15.8 21H8.2L3 15.8V8.2z"/><path d="M9 9l6 6M15 9l-6 6"/></svg>';
const ICON_CHECK = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M8 12.3l2.7 2.7L16 9.6"/></svg>';
const ICON_QUESTION = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M9.6 9.4a2.5 2.5 0 1 1 3.4 2.3c-.7.3-1 .8-1 1.5v.6M12 16.6v.4"/></svg>';
const ICON_MESSAGE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6.5A2.5 2.5 0 0 1 6.5 4h11A2.5 2.5 0 0 1 20 6.5v8a2.5 2.5 0 0 1-2.5 2.5H10l-4.5 3.5V17h0A2.5 2.5 0 0 1 4 14.5z"/><path d="M8.5 9h7M8.5 12.5h4.5"/></svg>';

// Labels that only show a translated text carry data-i18n="key", so when the interface
// language changes they are re-filled in place (applyStatic) and the photo and answer stay.
const L = (key) => `data-i18n="${key}"`;

export function render(el) {
  panel = el;
  panel.innerHTML = `
    <div class="mode-switch" role="tablist" aria-label="Scan">
      <button type="button" role="tab" data-mode="doc" aria-selected="true" ${L("mode_doc")}>${esc(t("mode_doc"))}</button>
      <button type="button" role="tab" data-mode="msg" aria-selected="false" ${L("mode_msg")}>${esc(t("mode_msg"))}</button>
    </div>
    <h1 id="scan-title" ${L("scan_title")}>${esc(t("scan_title"))}</h1>
    <p class="lede" id="scan-lede" ${L("scan_lede")}>${esc(t("scan_lede"))}</p>

    <div id="scan-form">
      <label class="drop" id="drop" for="file">
        <span id="drop-inner"></span>
      </label>
      <input type="file" id="file" accept="image/*,application/pdf">

      <div id="paste-box" hidden>
        <label class="field-label" for="msg-text" ${L("msg_paste_label")}>${esc(t("msg_paste_label"))}</label>
        <textarea id="msg-text" rows="4" maxlength="4000" dir="auto" data-i18n-placeholder="msg_paste_placeholder"
          placeholder="${esc(t("msg_paste_placeholder"))}"></textarea>
      </div>

      <label class="field-label" for="lang" id="lang-label" ${L("answer_language")}>${esc(t("answer_language"))}</label>
      <select id="lang"></select>

      <div class="scan-actions">
        <button class="btn" id="go" disabled ${L("explain_button")}>${esc(t("explain_button"))}</button>
        <p class="privacy-note">${ICON_LOCK}<span id="privacy-text" ${L("privacy")}>${esc(t("privacy"))}</span></p>
      </div>
    </div>

    <ol class="progress" id="progress" hidden aria-live="polite"></ol>
    <div id="result" aria-live="polite"></div>
  `;
  resetDrop();

  // Answer languages come from the server (config.LANGUAGES), shown in their own script.
  // Default: the language picked last time, else the interface language.
  fetch("/languages").then((r) => r.json()).then((langs) => {
    const select = panel.querySelector("#lang");
    for (const [code, name] of Object.entries(langs)) {
      const option = new Option(LANGUAGES[code] || name, code);
      option.lang = code;
      select.add(option);
    }
    select.value = langs[getLanguage()] ? getLanguage() : "en";
    try { const saved = localStorage.getItem("dalil.answerLang"); if (saved && langs[saved]) select.value = saved; } catch {}
  });
  panel.querySelector("#lang").addEventListener("change", (e) => {
    try { localStorage.setItem("dalil.answerLang", e.target.value); } catch {}
  });

  const input = panel.querySelector("#file");
  input.addEventListener("change", () => input.files[0] && choose(input.files[0]));
  const drop = panel.querySelector("#drop");
  drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("dragging"); });
  drop.addEventListener("dragleave", () => drop.classList.remove("dragging"));
  drop.addEventListener("drop", (e) => {
    e.preventDefault(); drop.classList.remove("dragging");
    if (e.dataTransfer.files[0]) choose(e.dataTransfer.files[0]);
  });
  panel.querySelector("#go").addEventListener("click", () => (mode === "msg" ? checkMessage() : analyze()));
  panel.querySelector("#msg-text").addEventListener("input", updateGo);
  panel.querySelectorAll(".mode-switch button").forEach((b) => b.addEventListener("click", () => setMode(b.dataset.mode)));
}

// Switch between "Explain a document" and "Is this message real?". The chosen photo stays.
function setMode(next) {
  if (next === mode) return;
  mode = next;
  const i = mode === "msg" ? 1 : 0;
  panel.querySelectorAll(".mode-switch button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.mode === mode)));
  for (const [id, keys] of Object.entries(MODE_TEXT)) {
    const el = panel.querySelector(`#${id}`);
    el.dataset.i18n = keys[i];
    el.textContent = t(keys[i]);
  }
  panel.querySelector("#paste-box").hidden = mode !== "msg";
  panel.querySelector("#scan-form").hidden = false;
  panel.querySelector("#result").innerHTML = "";
  if (!upload) resetDrop();
  updateGo();
}

function updateGo() {
  const text = panel.querySelector("#msg-text").value.trim();
  panel.querySelector("#go").disabled = !(upload || (mode === "msg" && text));
}

// The interface language changed: labels marked data-i18n were already re-filled.
// If the answer language was the same as the old interface language, move it along too
// (someone who switches the app to Urdu most likely wants the explanation in Urdu).
export function onLanguage(previous, next) {
  if (!panel) return;
  const select = panel.querySelector("#lang");
  if (select && select.value === previous && [...select.options].some((o) => o.value === next)) {
    select.value = next;
    try { localStorage.setItem("dalil.answerLang", next); } catch {}
  }
}

function resetDrop() {
  const [title, hint, icon] = mode === "msg" ? ["msg_drop_title", "msg_drop_hint", ICON_MESSAGE] : ["drop_title", "drop_hint", ICON_CAMERA];
  panel.querySelector("#drop-inner").innerHTML = `
    <span class="icon-circle">${icon}</span>
    <strong ${L(title)}>${esc(t(title))}</strong>
    <small ${L(hint)}>${esc(t(hint))}</small>`;
}

async function choose(file) {
  if (upload?.previewUrl) URL.revokeObjectURL(upload.previewUrl);
  const inner = panel.querySelector("#drop-inner");
  if (file.type === "application/pdf") {
    upload = { blob: file, name: file.name };
    inner.innerHTML = `<span class="file-name">${esc(file.name)}</span><span class="drop-change" ${L("drop_change")}>${esc(t("drop_change"))}</span>`;
  } else {
    const blob = await shrink(file);
    upload = { blob, name: "photo.jpg", previewUrl: URL.createObjectURL(blob) };
    inner.innerHTML = `<img src="${upload.previewUrl}" alt=""><span class="drop-change" ${L("drop_change")}>${esc(t("drop_change"))}</span>`;
  }
  updateGo();
  panel.querySelector("#result").innerHTML = "";
}

// Phone photos are big: shrink to max 2000px so uploads are quick and fit the AI's limits.
function shrink(file) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const scale = Math.min(1, 2000 / Math.max(img.width, img.height));
      const c = document.createElement("canvas");
      c.width = Math.round(img.width * scale);
      c.height = Math.round(img.height * scale);
      c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
      URL.revokeObjectURL(img.src);
      c.toBlob((b) => resolve(b || file), "image/jpeg", 0.85);
    };
    img.onerror = () => resolve(file);
    img.src = URL.createObjectURL(file);
  });
}

// ---------------------------------------------------------------- progress

const STEPS = ["step_read", "step_match", "step_explain"];
const MSG_STEPS = ["msg_step_read", "msg_step_links", "msg_step_flags"];

// The server does all three steps in one request, so the list moves forward on a timer
// and jumps to done as soon as the answer arrives.
function startProgress(steps = STEPS) {
  const list = panel.querySelector("#progress");
  list.hidden = false;
  list.innerHTML = steps.map((k) => `<li><span class="dot"></span><span ${L(k)}>${esc(t(k))}</span></li>`).join("");
  const items = [...list.children];
  let i = 0;
  const mark = () => items.forEach((li, n) => {
    li.className = n < i ? "done" : n === i ? "active" : "";
  });
  mark();
  const timers = [setTimeout(() => { i = 1; mark(); }, 2600), setTimeout(() => { i = 2; mark(); }, 4200)];
  return {
    finish() { timers.forEach(clearTimeout); i = steps.length; mark(); },
    hide() { timers.forEach(clearTimeout); list.hidden = true; },
  };
}

async function analyze() {
  const form = panel.querySelector("#scan-form");
  const result = panel.querySelector("#result");
  const lang = panel.querySelector("#lang").value || "en";
  form.hidden = true;
  result.innerHTML = "";
  const progress = startProgress();

  const fd = new FormData();
  fd.append("file", upload.blob, upload.name);
  fd.append("lang", lang);
  try {
    const r = await fetch("/analyze", { method: "POST", body: fd });
    const data = await r.json().catch(() => ({ error: `Server error ${r.status}` }));
    if (!r.ok) throw new Error(data.error || `Server error ${r.status}`);
    progress.finish();
    await new Promise((res) => setTimeout(res, 350));
    progress.hide();
    result.innerHTML = renderResult(data);
    if (data.explanation) {
      result.appendChild(chatCard(data)); // Ask Dalil: follow-up questions (#19)
      autoSave(result, data);
    }
    if (data.not_supported && upload) {
      // Not a document Dalil explains: maybe a "pay your fine" message. Check the same photo.
      result.insertAdjacentHTML("beforeend", `<button class="btn btn-quiet again" id="try-check" ${L("msg_try_check")}>${esc(t("msg_try_check"))}</button>`);
      result.querySelector("#try-check").addEventListener("click", () => { setMode("msg"); checkMessage(); });
    }
  } catch (err) {
    progress.hide();
    result.innerHTML = `
      <div class="notice error" role="alert"><strong ${L("error_title")}>${esc(t("error_title"))}</strong><br><span ${L("error_hint")}>${esc(t("error_hint"))}</span>
      <br><small>${esc(err.message)}</small></div>`;
  }
  addAgain(result, form, "scan_another");
}

// "Scan another" / "Check another message": back to an empty form.
function addAgain(result, form, key) {
  result.insertAdjacentHTML("beforeend", `<button class="btn btn-quiet again" id="again" ${L(key)}>${esc(t(key))}</button>`);
  result.querySelector("#again").addEventListener("click", () => {
    result.innerHTML = "";
    form.hidden = false;
    panel.querySelector("#file").value = "";
    panel.querySelector("#msg-text").value = "";
    if (upload?.previewUrl) URL.revokeObjectURL(upload.previewUrl);
    upload = null;
    resetDrop();
    updateGo();
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  result.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ---------------------------------------------------------------- is this message real?

async function checkMessage() {
  const form = panel.querySelector("#scan-form");
  const result = panel.querySelector("#result");
  const fd = new FormData();
  const text = panel.querySelector("#msg-text").value.trim();
  if (text) fd.append("text", text);
  if (upload) fd.append("file", upload.blob, upload.name);
  fd.append("lang", panel.querySelector("#lang").value || "en");
  form.hidden = true;
  result.innerHTML = "";
  const progress = startProgress(MSG_STEPS);
  try {
    const r = await fetch("/check-message", { method: "POST", body: fd });
    const data = await r.json().catch(() => ({ error: `Server error ${r.status}` }));
    if (!r.ok) throw new Error(data.error || `Server error ${r.status}`);
    progress.finish();
    await new Promise((res) => setTimeout(res, 350));
    progress.hide();
    result.innerHTML = renderCheck(data);
  } catch (err) {
    progress.hide();
    result.innerHTML = `
      <div class="notice error" role="alert"><strong ${L("msg_error_title")}>${esc(t("msg_error_title"))}</strong><br><span ${L("msg_error_hint")}>${esc(t("msg_error_hint"))}</span>
      <br><small>${esc(err.message)}</small></div>`;
  }
  addAgain(result, form, "msg_check_another");
}

// Verdict -> look. The words come from i18n (code-written), never from the AI.
const VERDICT = {
  looks_official: { cls: "v-ok", icon: ICON_CHECK },
  suspicious: { cls: "v-warn", icon: ICON_WARN },
  dont_pay: { cls: "v-bad", icon: ICON_STOP },
  unclear: { cls: "v-unclear", icon: ICON_QUESTION },
  not_message: { cls: "v-unclear", icon: ICON_QUESTION },
};

// A web address inside text: always left-to-right, even in Arabic and Urdu.
const addr = (value) => `<bdi dir="ltr">${esc(value)}</bdi>`;
const fill = (text, key, html) => esc(text).replace(`{${key}}`, html);

function renderCheck(d) {
  const lang = d.language || "en";
  const dir = RTL_LANGS.includes(lang) ? "rtl" : "ltr";
  const tr = (key) => t(key, lang);
  const v = VERDICT[d.verdict] ? d.verdict : "unclear";
  const m = d.message || {};
  const go = d.check_instead || { name: "u.ae", domain: "u.ae", url: "https://u.ae" };
  const read = ["unclear", "not_message"].includes(v) ? null : d;

  // Links are shown as text, never as clickable links: the whole point is not to open them.
  const links = (d.links || []).map((l) => {
    const status = l.status === "official" ? tr("link_official")
      : l.status === "lookalike" ? (l.looks_like ? fill(tr("link_lookalike"), "domain", addr(l.looks_like)) : esc(tr("link_lookalike_plain")))
      : esc(tr("link_not_official"));
    const notes = (l.notes || []).map((n) => esc(tr(`note_${n}`))).join(" · ");
    return `<li class="link-row s-${esc(l.status)}">
        <span class="link-host" dir="ltr">${esc(l.host)}</span>
        <span class="link-status">${l.status === "official" ? esc(status) : status}</span>
        ${notes ? `<small>${notes}</small>` : ""}
      </li>`;
  }).join("");

  // Warning signs: the code's own checks first (sender), then the AI's list in the answer language.
  const flags = [];
  const s = d.sender_check;
  if (s && s.flag === "personal_number") flags.push(esc(tr("sender_personal_number")));
  if (s && s.flag === "email_not_official") flags.push(fill(tr("sender_email_not_official"), "domain", addr(s.domain)));
  for (const f of d.red_flags || []) flags.push(esc(f));

  const rows = [
    ["msg_read_sender", m.sender], ["msg_read_claims", m.claims_to_be],
    ["msg_read_amount", m.amount_aed != null ? formatAED(m.amount_aed, lang) : ""], ["msg_read_discount", m.discount_claim],
  ].filter(([, val]) => val);

  return `
    <article class="sheet check" dir="${dir}" lang="${esc(lang)}">
      ${d.mock ? `<span class="mock-flag">${esc(tr("mock"))}</span>` : ""}
      <div class="verdict ${VERDICT[v].cls}" role="status">
        <span class="verdict-icon">${VERDICT[v].icon}</span>
        <div><h2>${esc(tr(`v_${v}`))}</h2><p>${esc(tr(`v_${v}_sub`))}</p></div>
      </div>
      ${read && m.summary ? `<p class="check-summary">${esc(m.summary)}</p>` : ""}

      ${v === "not_message" ? "" : `
      <section class="check-instead">
        <h3>${esc(tr("msg_check_instead"))}</h3>
        <a class="btn" href="${esc(go.url)}" target="_blank" rel="noopener noreferrer">${fill(tr("msg_open_official"), "domain", addr(go.domain))}</a>
        <p class="muted">${esc(go.name)}. ${esc(tr("msg_official_note"))}</p>
      </section>`}

      ${read ? `
      <section class="check-section">
        <h3>${esc(tr("msg_links"))}</h3>
        ${links ? `<ul class="link-list">${links}</ul>` : `<p class="muted">${esc(tr("msg_no_links"))}</p>`}
      </section>
      <section class="check-section">
        <h3>${esc(tr("msg_flags"))}</h3>
        ${flags.length ? `<ul class="flag-list">${flags.map((f) => `<li>${f}</li>`).join("")}</ul>` : `<p class="muted">${esc(tr("msg_no_flags"))}</p>`}
      </section>
      ${rows.length ? `<details class="read"><summary>${esc(tr("msg_read_title"))}</summary>
        <dl>${rows.map(([k, val]) => `<dt>${esc(tr(k))}</dt><dd>${esc(val)}</dd>`).join("")}</dl></details>` : ""}` : ""}

      <p class="never-safe">${ICON_LOCK}<span>${esc(tr("msg_never_safe"))}</span></p>
    </article>`;
}

// ---------------------------------------------------------------- auto-save to My documents

// Every explained document is saved automatically (summary only, never the photo),
// with Undo. If no deadline is printed, the user can add a reminder date.
async function autoSave(result, d) {
  const f = d.fields || {};
  const printed = Boolean(f.deadline_date);
  const saved = await addDocument({
    kind: f.doc_type,
    authority: f.issuing_authority,
    emirate: f.emirate,
    subject: f.subject,
    amount_aed: f.amount_aed,
    issue_date: f.issue_date,
    date: f.deadline_date || null,
    date_is_reminder: false,
    summary: d.explanation.what_it_is,
    answer_lang: d.language,
    official_url: (d.footer || {}).link,
    service_id: d.service_id,
  });
  const box = document.createElement("div");
  box.className = "save-box";
  box.id = "save-box";
  if (!saved) {
    box.innerHTML = `<p ${L("save_failed")}>${esc(t("save_failed"))}</p>`;
    result.insertBefore(box, result.querySelector("#chat") || result.querySelector("#again"));
    return;
  }
  const inWeek = new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10);
  box.innerHTML = `
    <div class="saved-row">
      <span class="saved-check" aria-hidden="true"></span>
      <div><strong ${L("auto_saved")}>${esc(t("auto_saved"))}</strong>
        <p class="muted" ${L(currentAccount() ? "auto_saved_synced" : "auto_saved_local")}>${esc(t(currentAccount() ? "auto_saved_synced" : "auto_saved_local"))}</p></div>
      <button class="link-btn plain" id="undo-save" ${L("undo")}>${esc(t("undo"))}</button>
    </div>
    ${printed ? "" : `
      <div class="reminder">
        <label class="field-label" for="remind-date" ${L("save_hint_none")}>${esc(t("save_hint_none"))}</label>
        <div class="reminder-row">
          <input type="date" id="remind-date" value="${inWeek}" min="${new Date().toISOString().slice(0, 10)}">
          <button class="btn small" id="add-reminder" ${L("add_reminder")}>${esc(t("add_reminder"))}</button>
        </div>
      </div>`}
    <div class="saved-links">
      <a href="#deadlines" ${L("saved_link")}>${esc(t("saved_link"))}</a>
      ${currentAccount() ? "" : `<button class="link-btn plain" id="sync-signin" ${L("doc_sign_in_sync")}>${esc(t("doc_sign_in_sync"))}</button>`}
    </div>
    <p id="save-status" aria-live="polite"></p>`;
  result.insertBefore(box, result.querySelector("#chat") || result.querySelector("#again"));

  box.querySelector("#undo-save").addEventListener("click", async () => {
    await removeDocument(saved.id);
    box.innerHTML = `<p class="muted" ${L("not_saved")}>${esc(t("not_saved"))}</p>`;
  });
  box.querySelector("#sync-signin")?.addEventListener("click", openAccount);
  box.querySelector("#add-reminder")?.addEventListener("click", async (e) => {
    const date = box.querySelector("#remind-date").value;
    if (!date) return;
    const ok = await updateDocument(saved.id, { date, date_is_reminder: true });
    if (ok) {
      e.target.disabled = true;
      box.querySelector("#save-status").textContent = `${t("reminder_set")} ${formatDate(date)}`;
    }
  });
}

// ---------------------------------------------------------------- result

// The deadline ring: full at 30+ days, empties as the deadline gets close.
function stamp(daysLeft, tr) {
  if (daysLeft === null || daysLeft === undefined) return "";
  const state = daysLeft <= 7 ? " urgent" : daysLeft <= 14 ? " soon" : "";
  let num = Math.abs(daysLeft);
  let unit = daysLeft < 0 ? tr("stamp_overdue") : daysLeft === 1 ? tr("stamp_day_left") : tr("stamp_days_left");
  if (daysLeft === 0) { num = "0"; unit = tr("stamp_today"); }
  const C = 2 * Math.PI * 38;
  const filled = daysLeft < 0 ? 1 : Math.max(0.04, Math.min(1, daysLeft / 30));
  return `<div class="ring${state}" role="img" aria-label="${esc(`${num} ${unit}`)}">
      <svg viewBox="0 0 92 92" aria-hidden="true"><circle class="track" cx="46" cy="46" r="38"/>
        <circle class="bar" cx="46" cy="46" r="38" stroke-dasharray="${C.toFixed(1)}" stroke-dashoffset="${(C * (1 - filled)).toFixed(1)}"/></svg>
      <span class="center"><span><span class="num">${esc(num)}</span><span class="unit">${esc(unit)}</span></span></span>
    </div>`;
}

function renderResult(d) {
  const f = d.fields || {};
  const s = d.service;
  const foot = d.footer || {};
  const lang = d.language || "en";
  const dir = RTL_LANGS.includes(lang) ? "rtl" : "ltr";
  const tr = (key) => t(key, lang); // labels in the answer language, not the interface language
  const kind = tr(`kind_${f.doc_type || "other"}`);
  const kindLine = f.issuing_authority
    ? tr("kind_line").replace("{kind}", kind).replace("{authority}", f.issuing_authority)
    : kind;

  const amount = f.amount_aed != null
    ? { label: tr("fact_amount"), value: formatAED(f.amount_aed, lang) }
    : s && s.fee_aed != null ? { label: tr("fact_fee"), value: formatAED(s.fee_aed, lang) } : null;
  const deadline = f.deadline_date ? formatDate(f.deadline_date, lang) : null;

  const facts = `
    <div class="facts">
      <div class="fact"><span class="label">${esc(amount ? amount.label : tr("fact_amount"))}</span>
        <span class="value">${amount ? `<span class="mark">${esc(amount.value)}</span>` : esc(tr("fact_none"))}</span></div>
      <div class="fact"><span class="label">${esc(tr("fact_deadline"))}</span>
        <span class="value">${deadline ? `<span class="mark">${esc(deadline)}</span>` : esc(tr("fact_none"))}</span></div>
    </div>`;

  let body;
  if (d.fallback) {
    body = `<h2>${esc(kindLine)}</h2><p class="notice">${esc(d.fallback)}</p>`;
  } else {
    const e = d.explanation || {};
    body = `
      ${stamp(d.days_left, tr)}
      <p class="doc-kind">${esc(kindLine)}</p>
      <h2>${esc(e.what_it_is)}</h2>
      ${facts}
      <div class="explain">
        <div><h3>${esc(tr("h_cost"))}</h3><p>${esc(e.cost)}</p></div>
        <div><h3>${esc(tr("h_deadline"))}</h3><p>${esc(e.deadline)}</p></div>
        <div><h3>${esc(tr("h_steps"))}</h3>
          <ol class="steps">${(e.next_steps || []).map((x) => `<li><span>${esc(x)}</span></li>`).join("")}</ol></div>
      </div>`;
  }

  const trust = `
    <div class="trust">
      ${s ? (s.verified
        ? `<p class="seal">${ICON_SEAL}<span>${esc(tr("verified"))}${s.last_checked ? ` (${esc(formatDate(s.last_checked, lang))})` : ""}</span></p>`
        : `<p class="seal unverified">${ICON_WARN}<span>${esc(tr("unverified"))}</span></p>`) : ""}
      ${s && s.source ? `<p class="muted">${esc(tr("source"))}: ${esc(s.source)}</p>` : ""}
      ${s && s.legal_basis ? `<p class="muted">${esc(tr("legal_basis"))}: ${esc(s.legal_basis)}</p>` : ""}
      <p>${esc(foot.confidence_label)}</p>
      <p class="muted">${esc(foot.disclaimer)}</p>
    </div>`;

  const rows = [
    ["read_type", kind], ["read_authority", f.issuing_authority], ["read_reference", f.reference_number],
    ["read_amount", f.amount_aed != null ? formatAED(f.amount_aed, lang) : ""], ["read_issue", formatDate(f.issue_date, lang)],
    ["read_deadline", formatDate(f.deadline_date, lang)], ["read_subject", f.subject],
  ].filter(([, v]) => v);
  const read = `
    <details class="read"><summary>${esc(tr("read_title"))}</summary>
      <dl>${rows.map(([k, v]) => `<dt>${esc(tr(k))}</dt><dd>${esc(v)}</dd>`).join("")}</dl>
    </details>`;

  return `
    <article class="sheet" dir="${dir}" lang="${esc(lang)}">
      ${d.mock ? `<span class="mock-flag">${esc(tr("mock"))}</span>` : ""}
      ${body}
      ${foot.link ? `<a class="btn" href="${esc(foot.link)}" target="_blank" rel="noopener">${esc(tr("open_official"))}</a>` : ""}
      ${trust}
      ${read}
    </article>`;
}
