// Scan tab (issue #12): photo in -> marked-up explanation out.
import { t } from "./i18n.js";
import { esc, formatAED, formatDate, RTL_LANGS } from "./util.js";
import { addDocument, currentAccount, removeDocument, updateDocument } from "./store.js";
import { openAccount } from "./account.js";

let panel;
let upload = null; // { blob, name, previewUrl? }

const ICON_CAMERA = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9a2 2 0 0 1 2-2h1.7l1.4-2h5.8l1.4 2H18a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/><circle cx="12" cy="13.2" r="3.4"/></svg>';
const ICON_LOCK = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="10" width="14" height="10" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></svg>';
const ICON_SEAL = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l2.4 1.8 3-.2.9 2.9 2.4 1.8-1 2.8 1 2.8-2.4 1.8-.9 2.9-3-.2L12 21l-2.4-1.8-3 .2-.9-2.9-2.4-1.8 1-2.8-1-2.8 2.4-1.8.9-2.9 3 .2z"/><path d="M8.5 12.2l2.3 2.3 4.7-4.7"/></svg>';
const ICON_WARN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4l9 16H3z"/><path d="M12 10v4M12 17v.5"/></svg>';

export function render(el) {
  panel = el;
  panel.innerHTML = `
    <h1 id="scan-title">${esc(t("scan_title"))}</h1>
    <p class="lede">${esc(t("scan_lede"))}</p>

    <div id="scan-form">
      <label class="drop" id="drop" for="file">
        <span id="drop-inner"></span>
      </label>
      <input type="file" id="file" accept="image/*,application/pdf">

      <label class="field-label" for="lang">${esc(t("answer_language"))}</label>
      <select id="lang"></select>

      <div class="scan-actions">
        <button class="btn" id="go" disabled>${esc(t("explain_button"))}</button>
        <p class="privacy-note">${ICON_LOCK}<span>${esc(t("privacy"))}</span></p>
      </div>
    </div>

    <ol class="progress" id="progress" hidden aria-live="polite"></ol>
    <div id="result" aria-live="polite"></div>
  `;
  resetDrop();

  fetch("/languages").then((r) => r.json()).then((langs) => {
    const select = panel.querySelector("#lang");
    for (const [code, name] of Object.entries(langs)) select.add(new Option(name, code));
    select.value = "en";
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
  panel.querySelector("#go").addEventListener("click", analyze);
}

function resetDrop() {
  panel.querySelector("#drop-inner").innerHTML = `
    <span class="icon-circle">${ICON_CAMERA}</span>
    <strong>${esc(t("drop_title"))}</strong>
    <small>${esc(t("drop_hint"))}</small>`;
}

async function choose(file) {
  if (upload?.previewUrl) URL.revokeObjectURL(upload.previewUrl);
  const inner = panel.querySelector("#drop-inner");
  if (file.type === "application/pdf") {
    upload = { blob: file, name: file.name };
    inner.innerHTML = `<span class="file-name">${esc(file.name)}</span><span class="drop-change">${esc(t("drop_change"))}</span>`;
  } else {
    const blob = await shrink(file);
    upload = { blob, name: "photo.jpg", previewUrl: URL.createObjectURL(blob) };
    inner.innerHTML = `<img src="${upload.previewUrl}" alt=""><span class="drop-change">${esc(t("drop_change"))}</span>`;
  }
  panel.querySelector("#go").disabled = false;
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

// The server does all three steps in one request, so the list moves forward on a timer
// and jumps to done as soon as the answer arrives.
function startProgress() {
  const list = panel.querySelector("#progress");
  list.hidden = false;
  list.innerHTML = STEPS.map((k) => `<li><span class="dot"></span><span>${esc(t(k))}</span></li>`).join("");
  const items = [...list.children];
  let i = 0;
  const mark = () => items.forEach((li, n) => {
    li.className = n < i ? "done" : n === i ? "active" : "";
  });
  mark();
  const timers = [setTimeout(() => { i = 1; mark(); }, 2600), setTimeout(() => { i = 2; mark(); }, 4200)];
  return {
    finish() { timers.forEach(clearTimeout); i = STEPS.length; mark(); },
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
    if (data.explanation) autoSave(result, data);
  } catch (err) {
    progress.hide();
    result.innerHTML = `
      <div class="notice error" role="alert"><strong>${esc(t("error_title"))}</strong><br>${esc(t("error_hint"))}
      <br><small>${esc(err.message)}</small></div>`;
  }
  result.insertAdjacentHTML("beforeend", `<button class="btn btn-quiet again" id="again">${esc(t("scan_another"))}</button>`);
  result.querySelector("#again").addEventListener("click", () => {
    result.innerHTML = "";
    form.hidden = false;
    panel.querySelector("#file").value = "";
    if (upload?.previewUrl) URL.revokeObjectURL(upload.previewUrl);
    upload = null;
    resetDrop();
    panel.querySelector("#go").disabled = true;
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  result.scrollIntoView({ behavior: "smooth", block: "start" });
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
    box.innerHTML = `<p>${esc(t("save_failed"))}</p>`;
    result.appendChild(box);
    return;
  }
  const inWeek = new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10);
  box.innerHTML = `
    <div class="saved-row">
      <span class="saved-check" aria-hidden="true"></span>
      <div><strong>${esc(t("auto_saved"))}</strong>
        <p class="muted">${esc(t(currentAccount() ? "auto_saved_synced" : "auto_saved_local"))}</p></div>
      <button class="link-btn plain" id="undo-save">${esc(t("undo"))}</button>
    </div>
    ${printed ? "" : `
      <div class="reminder">
        <label class="field-label" for="remind-date">${esc(t("save_hint_none"))}</label>
        <div class="reminder-row">
          <input type="date" id="remind-date" value="${inWeek}" min="${new Date().toISOString().slice(0, 10)}">
          <button class="btn small" id="add-reminder">${esc(t("add_reminder"))}</button>
        </div>
      </div>`}
    <div class="saved-links">
      <a href="#deadlines">${esc(t("saved_link"))}</a>
      ${currentAccount() ? "" : `<button class="link-btn plain" id="sync-signin">${esc(t("doc_sign_in_sync"))}</button>`}
    </div>
    <p id="save-status" aria-live="polite"></p>`;
  result.appendChild(box);

  box.querySelector("#undo-save").addEventListener("click", async () => {
    await removeDocument(saved.id);
    box.innerHTML = `<p class="muted">${esc(t("not_saved"))}</p>`;
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
    ? { label: tr("fact_amount"), value: formatAED(f.amount_aed) }
    : s && s.fee_aed != null ? { label: tr("fact_fee"), value: formatAED(s.fee_aed) } : null;
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
    ["read_amount", f.amount_aed != null ? formatAED(f.amount_aed) : ""], ["read_issue", formatDate(f.issue_date, lang)],
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
