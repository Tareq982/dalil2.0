// Personalization.
// - "About you": a few optional answers, edited in the My profile panel (the person button,
//   top right), together with the account. Never names or ID numbers.
// - "For you": on the My documents tab. Plain rules on the server (app/personal.py) match the
//   answers to the checked services and apply the official rules for this person, for example
//   the grace period for their residence type.
import { getLanguage, t } from "./i18n.js";
import { esc } from "./util.js";
import { getProfile, saveProfile } from "./store.js";
import { helpHtml } from "./help.js";

const EMIRATES = [["Dubai", "دبي"], ["Abu Dhabi", "أبوظبي"], ["Sharjah", "الشارقة"], ["Ajman", "عجمان"],
  ["Umm Al Quwain", "أم القيوين"], ["Ras Al Khaimah", "رأس الخيمة"], ["Fujairah", "الفجيرة"]];
const RESIDENCE = ["sponsored", "skilled", "golden", "owner", "graduate", "other", "citizen", "not_sure"];
const HOME = ["rent", "own", "other"];

const fill = (text, values) => Object.entries(values).reduce((s, [k, v]) => s.replace(`{${k}}`, v), text);
const has = (p) => Object.keys(p || {}).length > 0;

// Asks the My profile panel to open (account.js listens), without the two modules importing each other
export function openProfilePanel() {
  window.dispatchEvent(new CustomEvent("dalil:open-profile"));
}

// ---------------------------------------------------------------- About you (in the My profile panel)

export function aboutYouHtml() {
  const p = getProfile();
  const opt = (value, label, current) => `<option value="${esc(value)}"${value === current ? " selected" : ""}>${esc(label)}</option>`;
  return `
    <section class="about-you" aria-labelledby="about-title">
      <h3 class="panel-section" id="about-title">${esc(t("profile_title"))}</h3>
      <p class="muted">${esc(t("profile_lede"))}</p>
      <form id="profile-form" class="profile-form" autocomplete="off">
        <label class="field-label" for="pf-emirate">${esc(t("profile_emirate"))}</label>
        <select id="pf-emirate">${opt("", t("profile_choose"), p.emirate)}${EMIRATES.map(([en, ar]) => opt(en, `${en} · ${ar}`, p.emirate)).join("")}</select>
        <label class="field-label" for="pf-residence">${esc(t("profile_residence"))}</label>
        <select id="pf-residence">${opt("", t("profile_choose"), p.residence)}${RESIDENCE.map((r) => opt(r, t(`res_${r}`), p.residence)).join("")}</select>
        <label class="field-label" for="pf-expiry">${esc(t("profile_expiry"))}</label>
        <input type="date" id="pf-expiry" value="${esc(p.residence_expiry || "")}">
        <label class="field-label" for="pf-home">${esc(t("profile_home"))}</label>
        <select id="pf-home">${opt("", t("profile_choose"), p.home)}${HOME.map((h) => opt(h, t(`home_${h}`), p.home)).join("")}</select>
        <label class="check-row" for="pf-drives"><input type="checkbox" id="pf-drives"${p.drives ? " checked" : ""}><span>${esc(t("profile_drives"))}</span></label>
        <div class="profile-actions">
          <button class="btn small" type="submit" id="pf-save">${esc(t("profile_save"))}</button>
          <button class="link-btn plain" type="button" id="pf-clear">${esc(t("profile_clear"))}</button>
        </div>
        <p class="ok-note" id="pf-status" aria-live="polite"></p>
      </form>
    </section>`;
}

export function wireAboutYou(root) {
  const form = root.querySelector("#profile-form");
  if (!form) return;
  const status = root.querySelector("#pf-status");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const ok = await saveProfile({
      emirate: form.querySelector("#pf-emirate").value,
      residence: form.querySelector("#pf-residence").value,
      residence_expiry: form.querySelector("#pf-expiry").value,
      home: form.querySelector("#pf-home").value,
      drives: form.querySelector("#pf-drives").checked,
    });
    status.className = ok ? "ok-note" : "form-error";
    status.textContent = ok ? t("profile_saved_foryou") : t("save_failed");
  });
  root.querySelector("#pf-clear").addEventListener("click", async () => {
    await saveProfile({});
    form.reset();
    form.querySelectorAll("select").forEach((s) => { s.value = ""; });
    form.querySelector("#pf-expiry").value = "";
    status.className = "ok-note";
    status.textContent = t("profile_cleared");
  });
}

export function profileSummary(p = getProfile()) {
  if (!has(p)) return "";
  return [p.emirate, p.residence ? t(`res_${p.residence}`) : "", p.drives ? t("profile_drives") : ""].filter(Boolean).join(" · ");
}

// ---------------------------------------------------------------- For you (My documents tab)

export function forYouHtml() {
  const p = getProfile();
  return `
    <section class="foryou-wrap" aria-labelledby="foryou-title">
      <div class="foryou-head">
        <h2 class="section-title" id="foryou-title">${esc(t("foryou_title"))}</h2>
        ${has(p) ? `<button class="link-btn plain" type="button" id="foryou-edit">${esc(t("foryou_edit"))}</button>` : ""}
      </div>
      <p class="muted">${esc(has(p) ? profileSummary(p) : t("foryou_lede"))}</p>
      <div id="foryou" class="foryou" aria-live="polite"></div>
    </section>`;
}

export function wireForYou(panel) {
  panel.querySelector("#foryou-edit")?.addEventListener("click", openProfilePanel);
  loadForYou(panel);
}

async function loadForYou(panel) {
  const box = panel.querySelector("#foryou");
  if (!box) return;
  const p = getProfile();
  if (!has(p)) {
    box.innerHTML = `
      <div class="fy-card glass fy-start">
        <p class="fy-text">${esc(t("foryou_empty"))}</p>
        <button class="btn small" type="button" id="foryou-start">${esc(t("foryou_start"))}</button>
      </div>`;
    box.querySelector("#foryou-start").addEventListener("click", openProfilePanel);
    return;
  }
  try {
    const cards = await fetch("/for-you", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile: p }) }).then((r) => r.json());
    box.innerHTML = cards.length ? cards.map(card).join("") : `<p class="foryou-empty">${esc(t("foryou_none"))}</p>`;
  } catch {
    box.innerHTML = "";
  }
}

function card(c) {
  const s = c.service || {};
  let title = "", text = "", badge = "";
  if (c.reason === "residency") {
    title = t("foryou_residency");
    text = c.eligibility ? fill(t("foryou_grace"), { n: c.eligibility.grace_days }) : t("foryou_grace_check");
    if (c.days_left != null) {
      const cls = c.days_left < 0 || c.days_left <= 30 ? " urgent" : c.days_left <= 60 ? " soon" : "";
      badge = `<span class="days${cls}">${esc(c.days_left < 0 ? fill(t("foryou_overdue"), { n: -c.days_left }) : fill(t("foryou_days_left"), { n: c.days_left }))}</span>`;
    }
  } else if (c.reason === "driving") {
    const ar = (EMIRATES.find(([en]) => en === c.emirate) || [])[1];
    title = fill(t("foryou_driving"), { emirate: ["ar", "ur"].includes(getLanguage()) && ar ? ar : c.emirate });
    text = t("foryou_driving_text");
  } else if (c.reason === "renting") {
    title = t("foryou_renting");
    text = t("foryou_renting_text");
  }
  return `
    <article class="fy-card glass${c.urgent ? " is-urgent" : ""}">
      <div class="deadline-head"><div><p class="deadline-kind">${esc(s.authority || "")}</p><h3>${esc(title)}</h3></div>${badge}</div>
      <p class="fy-text">${esc(text)}</p>
      ${c.eligibility ? `<p class="fy-text fy-decision">${esc(fill(t("decision_note"), { authority: s.authority || "" }))}</p>` : ""}
      ${c.eligibility && c.eligibility.source ? `<p class="muted fy-source">${esc(t("source"))}: ${esc(c.eligibility.source)}</p>` : ""}
      <a class="btn btn-quiet small" href="${esc(s.official_url || "https://u.ae")}" target="_blank" rel="noopener">${esc(t("foryou_open"))} · ${esc(s.service_name || "")}</a>
      ${c.urgent ? helpHtml(s, getLanguage()) : ""}
    </article>`;
}

// ---------------------------------------------------------------- used by Find a service

export function profileForFind() {
  return getProfile();
}

// The official rule for this person, and who decides: Dalil explains, the authority decides
export function personalNote(personal, lang, authority = "") {
  if (!personal || !personal.grace_days) return "";
  const rule = fill(t("find_personal", lang), { n: personal.grace_days });
  return authority ? `${rule} ${fill(t("decision_note", lang), { authority })}` : rule;
}
