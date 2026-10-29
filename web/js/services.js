// Services tab (issue #14): the verified catalog from data/services.json, via GET /services.
import { t } from "./i18n.js";
import { esc, formatAED, formatDate } from "./util.js";

// Open datasets referenced by "related_datasets" in services.json (details in data/sources.md).
const DATASETS = {
  "dubai-pulse-government-service-prices": "Dubai Government Service Prices (Dubai Pulse)",
  "dubai-pulse-ejari-rent-contracts": "Ejari rent contracts (Dubai Pulse)",
  "bayanat-cause-of-traffic-fines": "Cause of Traffic Fines (Bayanat, Ministry of Interior)",
  "bayanat-unified-federal-traffic-system-2023": "Unified Federal Traffic System 2023 (Bayanat)",
  "dubai-pulse-traffic-incidents": "Dubai Police traffic incidents (Dubai Pulse)",
};

const FILTERS = [
  ["all", "sv_all"],
  ["traffic_fine", "kind_traffic_fine"],
  ["visa_residency_notice", "kind_visa_residency_notice"],
  ["tenancy_contract", "kind_tenancy_contract"],
];

const ICON_SEAL = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l2.4 1.8 3-.2.9 2.9 2.4 1.8-1 2.8 1 2.8-2.4 1.8-.9 2.9-3-.2L12 21l-2.4-1.8-3 .2-.9-2.9-2.4-1.8 1-2.8-1-2.8 2.4-1.8.9-2.9 3 .2z"/><path d="M8.5 12.2l2.3 2.3 4.7-4.7"/></svg>';
const ICON_WARN = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4l9 16H3z"/><path d="M12 10v4M12 17v.5"/></svg>';

let panel;
let services = [];
let filter = "all";

export async function render(el) {
  panel = el;
  panel.innerHTML = `
    <h1>${esc(t("tab_services"))}</h1>
    <p class="lede">${esc(t("sv_lede"))}</p>
    <div class="chips" role="group" aria-label="${esc(t("sv_filter"))}">
      ${FILTERS.map(([key, label]) => `<button class="chip" data-filter="${key}" aria-pressed="${key === filter}">${esc(t(label))}</button>`).join("")}
    </div>
    <div id="service-list" aria-live="polite"><p class="lede">${esc(t("sv_loading"))}</p></div>`;
  panel.querySelectorAll(".chip").forEach((b) => b.addEventListener("click", () => {
    filter = b.dataset.filter;
    panel.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", c === b));
    draw();
  }));
  try {
    const r = await fetch("/services");
    if (!r.ok) throw new Error(`Server error ${r.status}`);
    services = await r.json();
    draw();
  } catch (err) {
    panel.querySelector("#service-list").innerHTML =
      `<div class="notice error" role="alert">${esc(t("sv_error"))}<br><small>${esc(err.message)}</small></div>`;
  }
}

function draw() {
  const shown = services.filter((s) => filter === "all" || s.doc_type === filter);
  panel.querySelector("#service-list").innerHTML = `<div class="service-list">${shown.map(card).join("")}</div>`;
}

function card(s) {
  const where = s.emirate || t("sv_all_emirates");
  const fee = [s.fee_aed != null ? formatAED(s.fee_aed) : "", s.fee_note].filter(Boolean).join(". ");
  const datasets = (s.related_datasets || []).map((id) => DATASETS[id] || id);
  return `
    <details class="service">
      <summary>
        <span class="service-name">${esc(s.service_name)}</span>
        <span class="service-meta">${esc(s.authority)}, ${esc(where)}</span>
        ${s.verified
          ? `<span class="seal">${ICON_SEAL}<span>${esc(t("sv_verified"))} ${esc(formatDate(s.last_checked))}</span></span>`
          : `<span class="seal unverified">${ICON_WARN}<span>${esc(t("sv_unverified"))}</span></span>`}
      </summary>
      <div class="service-body">
        ${fee ? `<div><h3>${esc(t("h_cost"))}</h3><p>${esc(fee)}</p></div>` : ""}
        ${s.deadline_rule ? `<div><h3>${esc(t("sv_deadline_rule"))}</h3><p>${esc(s.deadline_rule)}</p></div>` : ""}
        ${(s.next_steps || []).length ? `<div><h3>${esc(t("h_steps"))}</h3>
          <ol class="steps">${s.next_steps.map((x) => `<li><span>${esc(x)}</span></li>`).join("")}</ol></div>` : ""}
        <a class="btn" href="${esc(s.official_url)}" target="_blank" rel="noopener">${esc(t("open_official"))}</a>
        <div class="trust">
          ${s.source ? `<p class="muted">${esc(t("source"))}: ${esc(s.source)}</p>` : ""}
          ${s.legal_basis ? `<p class="muted">${esc(t("legal_basis"))}: ${esc(s.legal_basis)}</p>` : ""}
          ${(s.official_fee_codes || []).length ? `<p class="muted">${esc(t("sv_fee_codes"))}: ${esc(s.official_fee_codes.join(", "))}</p>` : ""}
          ${datasets.length ? `<p class="muted">${esc(t("sv_open_data"))}: ${esc(datasets.join("; "))}</p>` : ""}
        </div>
      </div>
    </details>`;
}
