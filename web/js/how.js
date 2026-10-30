// How it works tab (issue #15): one screen judges can read during the demo.
// The pipeline, where facts come from (official pages + open data), what the confidence
// level means, privacy, and what Dalil never does. Every text is in i18n.js (how_*).
import { t } from "./i18n.js";
import { esc } from "./util.js";

const I = (d) => `<svg viewBox="0 0 24 24" aria-hidden="true">${d}</svg>`;
const ICONS = {
  read: I('<path d="M4 9a2 2 0 0 1 2-2h1.7l1.4-2h5.8l1.4 2H18a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/><circle cx="12" cy="13.2" r="3.4"/>'),
  match: I('<path d="M12 3l2.4 1.8 3-.2.9 2.9 2.4 1.8-1 2.8 1 2.8-2.4 1.8-.9 2.9-3-.2L12 21l-2.4-1.8-3 .2-.9-2.9-2.4-1.8 1-2.8-1-2.8 2.4-1.8.9-2.9 3 .2z"/><path d="M8.5 12.2l2.3 2.3 4.7-4.7"/>'),
  explain: I('<path d="M5 5h14a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-7l-4 3v-3H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z"/><path d="M8 10h8M8 13h5"/>'),
  check: I('<path d="M12 3l7 3v5c0 4.4-3 8.3-7 10-4-1.7-7-5.6-7-10V6z"/><path d="M9 12l2 2 4-4"/>'),
  ask: I('<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>'),
  lock: I('<rect x="5" y="10" width="14" height="10" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>'),
  no: I('<circle cx="12" cy="12" r="8.5"/><path d="M6 6l12 12"/>'),
  data: I('<ellipse cx="12" cy="6" rx="7" ry="2.8"/><path d="M5 6v12c0 1.5 3.1 2.8 7 2.8s7-1.3 7-2.8V6M5 12c0 1.5 3.1 2.8 7 2.8s7-1.3 7-2.8"/>'),
};

// Step id, who does it ("ai" or "code"), icon
const STEPS = [["read", "ai"], ["match", "code"], ["explain", "ai"], ["check", "code"]];

// The open datasets Dalil uses (details and links in data/sources.md)
const DATASETS = [
  { name: "Dubai Government Service Prices", portal: "Dubai Pulse", url: "https://www.dubaipulse.gov.ae/data/dof-pricing/dof_government_service_prices-open", use: "how_ds_prices" },
  { name: "Cause of Traffic Fines", portal: "Bayanat · Ministry of Interior", url: "https://bayanat.ae/en/Datasets/Dataset-info?id=CvrEX9sZ1jUcWJU4W2lyIv8yPCJm1bJ4XTJcDpQCUAg", use: "how_ds_causes" },
  { name: "Unified Federal Traffic System 2023", portal: "Bayanat · Ministry of Interior", url: "https://bayanat.ae/en/Datasets/Dataset-info?id=wUntGlYM4QgQrmL-ThqY_08k-Cr1-Xdyd2Hn5uT5B3I", use: "how_ds_vehicles" },
  { name: "Ejari rent contracts", portal: "Dubai Pulse · Dubai Land Department", url: "https://www.dubaipulse.gov.ae/data/dld-registration/dld_rent_contracts-open", use: "how_ds_ejari" },
];

export function render(el) {
  el.innerHTML = `
    <h1>${esc(t("tab_how"))}</h1>
    <p class="lede">${esc(t("how_lede"))}</p>

    <div class="how-stats" id="how-stats" aria-live="polite">
      ${stat("–", "how_stat_services")}${stat("–", "how_stat_checked")}${stat("–", "how_stat_languages")}${stat("0", "how_stat_photos")}
    </div>

    <section class="how-card" aria-labelledby="how-steps-title">
      <h2 id="how-steps-title">${esc(t("how_steps_title"))}</h2>
      <ol class="pipeline">
        ${STEPS.map(([id, who], i) => `
          <li>
            <span class="pipe-icon ${who}">${ICONS[id]}</span>
            <div>
              <p class="pipe-head"><strong>${i + 1}. ${esc(t(`how_step_${id}`))}</strong>
                <span class="who ${who}">${esc(t(who === "ai" ? "how_by_ai" : "how_by_code"))}</span></p>
              <p class="pipe-text">${esc(t(`how_step_${id}_text`))}</p>
            </div>
          </li>`).join("")}
      </ol>
      <div class="pipe-extra">
        <span class="pipe-icon ai">${ICONS.ask}</span>
        <div><p class="pipe-head"><strong>${esc(t("how_step_ask"))}</strong>
          <span class="who ai">${esc(t("how_by_ai"))}</span></p>
          <p class="pipe-text">${esc(t("how_step_ask_text"))}</p></div>
      </div>
      <p class="how-key muted">${esc(t("how_key"))}</p>
    </section>

    <section class="how-card" aria-labelledby="how-conf-title">
      <h2 id="how-conf-title">${esc(t("how_conf_title"))}</h2>
      <p class="how-intro">${esc(t("how_conf_intro"))}</p>
      <ul class="levels">
        ${[["high", "≥ 80%"], ["medium", "60–79%"], ["low", "< 60%"]].map(([k, range]) => `
          <li class="${k}"><span class="lvl-dot"></span>
            <div><p><strong>${esc(t(`how_conf_${k}`))}</strong> <span class="muted">${range}</span></p>
              <p class="pipe-text">${esc(t(`how_conf_${k}_text`))}</p></div></li>`).join("")}
      </ul>
    </section>

    <section class="how-card" aria-labelledby="how-data-title">
      <h2 id="how-data-title"><span class="h-icon">${ICONS.data}</span>${esc(t("how_data_title"))}</h2>
      <p class="how-intro">${esc(t("how_data_intro"))}</p>
      <ul class="datasets">
        ${DATASETS.map((d) => `
          <li><a href="${esc(d.url)}" target="_blank" rel="noopener">${esc(d.name)}</a>
            <span class="muted">${esc(d.portal)}</span>
            <p class="pipe-text">${esc(t(d.use))}</p></li>`).join("")}
      </ul>
      <a class="how-link" href="#services">${esc(t("how_data_link"))}</a>
    </section>

    <section class="how-card" aria-labelledby="how-privacy-title">
      <h2 id="how-privacy-title"><span class="h-icon">${ICONS.lock}</span>${esc(t("how_privacy_title"))}</h2>
      <ul class="ticks">
        ${["how_priv_photo", "how_priv_saved", "how_priv_device", "how_priv_chat"].map((k) => `<li>${esc(t(k))}</li>`).join("")}
      </ul>
    </section>

    <section class="how-card" aria-labelledby="how-never-title">
      <h2 id="how-never-title"><span class="h-icon">${ICONS.no}</span>${esc(t("how_never_title"))}</h2>
      <ul class="nevers">
        ${["how_never_legal", "how_never_invent", "how_never_card", "how_never_pay", "how_never_guess"].map((k) => `<li>${esc(t(k))}</li>`).join("")}
      </ul>
    </section>

    <p class="how-limits notice">${esc(t("how_limits"))}</p>`;

  loadStats(el);
}

function stat(value, key) {
  return `<div class="how-stat" data-stat="${key}"><span class="num">${esc(value)}</span><span class="label">${esc(t(key))}</span></div>`;
}

async function loadStats(el) {
  const set = (key, v) => { const n = el.querySelector(`[data-stat="${key}"] .num`); if (n) n.textContent = v; };
  try {
    const [services, langs] = await Promise.all([
      fetch("/services").then((r) => r.json()),
      fetch("/languages").then((r) => r.json()),
    ]);
    set("how_stat_services", services.length);
    set("how_stat_checked", services.filter((s) => s.verified).length);
    set("how_stat_languages", Object.keys(langs).length);
  } catch { /* the numbers are a nice extra; the page works without them */ }
}
