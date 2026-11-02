// "For you" + "About you" on the My documents tab (personalization).
// The person answers a few optional questions; plain rules on the server (app/personal.py)
// match them to the checked services and apply the official rules for their situation,
// for example the grace period for their residence type.
import { getLanguage, t } from "./i18n.js";
import { esc } from "./util.js";
import { getProfile, saveProfile } from "./store.js";

const EMIRATES = [["Dubai", "دبي"], ["Abu Dhabi", "أبوظبي"], ["Sharjah", "الشارقة"], ["Ajman", "عجمان"],
  ["Umm Al Quwain", "أم القيوين"], ["Ras Al Khaimah", "رأس الخيمة"], ["Fujairah", "الفجيرة"]];
const RESIDENCE = ["sponsored", "skilled", "golden", "owner", "graduate", "other", "citizen", "not_sure"];
const HOME = ["rent", "own", "other"];

const fill = (text, values) => Object.entries(values).reduce((s, [k, v]) => s.replace(`{${k}}`, v), text);
const has = (p) => Object.keys(p || {}).length > 0;

export function sectionsHtml() {
  const p = getProfile();
  const opt = (value, label, current) => `<option value="${esc(value)}"${value === current ? " selected" : ""}>${esc(label)}</option>`;
  return `
    <section class="foryou-wrap" aria-labelledby="foryou-title">
      <h2 class="section-title" id="foryou-title">${esc(t("foryou_title"))}</h2>
      <p class="muted">${esc(t("foryou_lede"))}</p>
      <div id="foryou" class="foryou" aria-live="polite"></div>
    </section>

    <details class="profile glass" id="profile"${has(p) ? "" : " open"}>
      <summary><span><strong>${esc(t("profile_title"))}</strong>
        <span class="muted profile-sum">${esc(summary(p))}</span></span></summary>
      <form id="profile-form" class="profile-form" autocomplete="off">
        <p class="muted">${esc(t("profile_lede"))}</p>
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
          <button class="btn small" type="submit">${esc(t("profile_save"))}</button>
          <button class="link-btn plain" type="button" id="pf-clear">${esc(t("profile_clear"))}</button>
          <span class="muted" id="pf-status" aria-live="polite"></span>
        </div>
      </form>
    </details>`;
}

function summary(p) {
  if (!has(p)) return "";
  return [p.emirate, p.residence ? t(`res_${p.residence}`) : "", p.drives ? t("profile_drives") : ""].filter(Boolean).join(" · ");
}

export function wire(panel) {
  const form = panel.querySelector("#profile-form");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const ok = await saveProfile({
      emirate: form.querySelector("#pf-emirate").value,
      residence: form.querySelector("#pf-residence").value,
      residence_expiry: form.querySelector("#pf-expiry").value,
      home: form.querySelector("#pf-home").value,
      drives: form.querySelector("#pf-drives").checked,
    });
    // saving redraws the tab (dalil:documents-changed); show the result on the new form
    const status = document.querySelector("#pf-status");
    if (status) status.textContent = ok ? t("profile_saved") : t("save_failed");
  });
  panel.querySelector("#pf-clear").addEventListener("click", () => saveProfile({}));
  loadForYou(panel);
}

async function loadForYou(panel) {
  const box = panel.querySelector("#foryou");
  const p = getProfile();
  if (!has(p)) {
    box.innerHTML = `<p class="foryou-empty">${esc(t("foryou_empty"))}</p>`;
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
      ${c.eligibility && c.eligibility.source ? `<p class="muted fy-source">${esc(t("source"))}: ${esc(c.eligibility.source)}</p>` : ""}
      <a class="btn btn-quiet small" href="${esc(s.official_url || "https://u.ae")}" target="_blank" rel="noopener">${esc(t("foryou_open"))} · ${esc(s.service_name || "")}</a>
    </article>`;
}

// For "Find a service": the profile goes with the question, so Dalil can skip what it already knows
export function profileForFind() {
  return getProfile();
}

// Used by the Find a service result: "For your residence type: 90 days of grace period"
export function personalNote(personal, lang) {
  return personal && personal.grace_days ? fill(t("find_personal", lang), { n: personal.grace_days }) : "";
}
