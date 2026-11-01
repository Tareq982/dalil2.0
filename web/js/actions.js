// Under an explanation: "Explain it simpler", "Send to family", and "Was this clear?" thumbs.
// Only the non-sensitive summary is ever shared or sent: never the photo or reference number.
import { t } from "./i18n.js";
import { esc } from "./util.js";
import { stopSpeaking } from "./speak.js";

const SAFE_FIELDS = ["doc_type", "emirate", "issuing_authority", "subject", "amount_aed", "issue_date", "deadline_date", "key_points"];
const I = (d) => `<svg viewBox="0 0 24 24" aria-hidden="true">${d}</svg>`;
const ICON_SIMPLE = I('<path d="M4 7h16M4 12h10M4 17h6"/><path d="M17 14l3 3-3 3"/>');
const ICON_SHARE = I('<path d="M12 15V4M8 8l4-4 4 4"/><path d="M6 12H5a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-6a1 1 0 0 0-1-1h-1"/>');
const ICON_SPIN = I('<path d="M12 4a8 8 0 1 0 8 8"/>');
const ICON_UP = I('<path d="M7 11v9H4v-9zM7 11l4-7c1.6 0 2.5 1.1 2.1 2.7L12.5 10H18a2 2 0 0 1 2 2.3l-1.1 6A2 2 0 0 1 17 20H7"/>');
const ICON_DOWN = I('<path d="M7 13V4H4v9zM7 13l4 7c1.6 0 2.5-1.1 2.1-2.7L12.5 14H18a2 2 0 0 0 2-2.3l-1.1-6A2 2 0 0 0 17 4H7"/>');

function event(body) {
  fetch("/event", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).catch(() => {});
}

export function addResultActions(result, d) {
  const sheet = result.querySelector(".sheet");
  const explainBox = sheet?.querySelector(".explain");
  if (!sheet || !explainBox || !d.explanation) return;
  const lang = d.language || "en";
  const tr = (key) => t(key, lang);
  const f = d.fields || {};

  // ---- buttons
  const row = document.createElement("div");
  row.className = "result-actions";
  row.innerHTML = `
    <button type="button" class="pill-btn" id="simpler-btn">${ICON_SIMPLE}<span>${esc(tr("simpler_button"))}</span></button>
    <button type="button" class="pill-btn" id="share-btn">${ICON_SHARE}<span>${esc(tr("share_button"))}</span></button>
    <p class="action-status" id="action-status" aria-live="polite"></p>`;
  explainBox.after(row);
  const status = row.querySelector("#action-status");

  // ---- Explain it simpler: same facts, easier words, number-checked again on the server
  const simpler = row.querySelector("#simpler-btn");
  simpler.addEventListener("click", async () => {
    simpler.disabled = true;
    simpler.classList.add("busy");
    simpler.innerHTML = `${ICON_SPIN}<span>${esc(tr("simpler_busy"))}</span>`;
    status.textContent = "";
    try {
      const fields = Object.fromEntries(SAFE_FIELDS.filter((k) => f[k] != null && f[k] !== "").map((k) => [k, f[k]]));
      const r = await fetch("/simplify", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fields, service_id: d.service_id, lang }),
      });
      const out = await r.json().catch(() => ({ error: `Server error ${r.status}` }));
      if (!r.ok) throw new Error(out.error || `Server error ${r.status}`);
      stopSpeaking();
      showExplanation(sheet, out.explanation, out.number_check, tr);
      d.explanation = { ...d.explanation, ...out.explanation, suggested_questions: d.explanation.suggested_questions };
      simpler.classList.remove("busy");
      simpler.innerHTML = `${ICON_SIMPLE}<span>${esc(tr("simpler_done"))}</span>`;
    } catch (err) {
      simpler.disabled = false;
      simpler.classList.remove("busy");
      simpler.innerHTML = `${ICON_SIMPLE}<span>${esc(tr("simpler_button"))}</span>`;
      status.textContent = `${tr("simpler_error")} (${err.message})`;
    }
  });

  // ---- Send to family: the phone's own share sheet, or copy where sharing isn't available
  row.querySelector("#share-btn").addEventListener("click", async () => {
    const text = shareText(d, tr);
    status.textContent = "";
    if (navigator.share) {
      try {
        await navigator.share({ title: "Dalil", text });
        event({ kind: "share", doc_type: f.doc_type, lang });
      } catch { /* the person closed the share sheet */ }
      return;
    }
    if (copy(text)) {
      status.textContent = tr("share_copied");
      event({ kind: "share", doc_type: f.doc_type, lang });
    }
  });

  // ---- Was this clear?
  const fb = document.createElement("div");
  fb.className = "feedback";
  fb.innerHTML = `
    <p>${esc(tr("fb_question"))}</p>
    <div class="thumbs">
      <button type="button" data-helpful="1" aria-pressed="false" aria-label="${esc(tr("fb_yes"))}" title="${esc(tr("fb_yes"))}">${ICON_UP}</button>
      <button type="button" data-helpful="0" aria-pressed="false" aria-label="${esc(tr("fb_no"))}" title="${esc(tr("fb_no"))}">${ICON_DOWN}</button>
    </div>
    <p class="thanks" aria-live="polite"></p>`;
  (sheet.querySelector(".trust") || row).before(fb);
  fb.querySelectorAll("[data-helpful]").forEach((b) => b.addEventListener("click", () => {
    const helpful = b.dataset.helpful === "1";
    fb.querySelectorAll("[data-helpful]").forEach((x) => { x.disabled = true; x.setAttribute("aria-pressed", String(x === b)); });
    fb.querySelector(".thanks").textContent = tr(helpful ? "fb_thanks_yes" : "fb_thanks_no");
    event({ kind: "feedback", helpful, doc_type: f.doc_type, lang });
  }));
}

// Put the simpler explanation into the card, in place.
function showExplanation(sheet, e, check, tr) {
  const h2 = sheet.querySelector("h2");
  h2.textContent = e.what_it_is;
  if (!sheet.querySelector(".simpler-flag")) h2.insertAdjacentHTML("beforebegin", `<span class="simpler-flag">${esc(tr("simpler_done"))}</span>`);
  const parts = sheet.querySelectorAll(".explain > div");
  if (parts[0]) parts[0].querySelector("p").textContent = e.cost;
  if (parts[1]) parts[1].querySelector("p").textContent = e.deadline;
  const steps = sheet.querySelector(".explain .steps");
  if (steps) steps.innerHTML = (e.next_steps || []).map((x) => `<li><span>${esc(x)}</span></li>`).join("");
  const note = sheet.querySelector(".check-note");
  if (check === "template" && !note) sheet.querySelector(".listen-slot")?.insertAdjacentHTML("afterend", `<p class="check-note">${esc(tr("number_check_template"))}</p>`);
  if (check !== "template" && note) note.remove();
}

function shareText(d, tr) {
  const e = d.explanation || {};
  const f = d.fields || {};
  const kind = tr(`kind_${f.doc_type || "other"}`);
  const head = f.issuing_authority ? tr("kind_line").replace("{kind}", kind).replace("{authority}", f.issuing_authority) : kind;
  const link = (d.footer || {}).link;
  return [
    head, e.what_it_is, "",
    `${tr("h_cost")}: ${e.cost}`,
    `${tr("h_deadline")}: ${e.deadline}`,
    `${tr("h_steps")}:`, ...(e.next_steps || []).map((s, i) => `${i + 1}. ${s}`),
    ...(link ? ["", `${tr("open_official")}: ${link}`] : []),
    "", tr("share_footer"),
  ].join("\n");
}

// Copy that also works on http://192.168.x.x, where the newer clipboard API is blocked.
function copy(text) {
  const area = document.createElement("textarea");
  area.value = text;
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.appendChild(area);
  area.select();
  let ok = false;
  try { ok = document.execCommand("copy"); } catch { ok = false; }
  area.remove();
  if (!ok && navigator.clipboard && window.isSecureContext) { navigator.clipboard.writeText(text); ok = true; }
  return ok;
}
