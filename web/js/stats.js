// /stats: anonymous usage numbers (app/stats.py). Refreshes every 10 seconds, so it can stay
// open on a second screen during the demo.
import { esc } from "./util.js";

const TYPES = { traffic_fine: "Traffic fines", visa_residency_notice: "Residency or visa notices",
                tenancy_contract: "Tenancy contracts", other: "Other / not supported", unknown: "Unreadable" };
const RESULTS = { explained: "Explained", fallback: "Too unclear: asked for a better photo", not_supported: "Not a supported document" };
const CHECKS = { passed: "Every number matched the data", retried: "Fixed on the AI's second try", template: "Shown as the data-only version" };
const VERDICTS = { dont_pay: "Don't pay via this link", suspicious: "Suspicious", looks_official: "Looks official",
                   unclear: "Too unclear", not_message: "Not a message" };
let languages = {};

const main = document.getElementById("stats");

function tile(num, label, sub = "") {
  return `<div class="how-stat"><span class="num">${esc(num)}</span><span class="label">${esc(label)}</span>${sub ? `<span class="label">${esc(sub)}</span>` : ""}</div>`;
}

function bars(title, counts, names = {}, note = "") {
  const rows = Object.entries(counts || {});
  const total = rows.reduce((a, [, n]) => a + n, 0);
  const body = rows.length
    ? `<ul class="bars">${rows.map(([k, n]) => `
        <li><span class="bar-label">${esc(names[k] || k)}</span><span class="bar-num">${n}</span>
          <span class="bar"><i style="width:${Math.max(3, Math.round((n / total) * 100))}%"></i></span></li>`).join("")}</ul>`
    : `<p class="muted">Nothing yet.</p>`;
  return `<section class="how-card"><h2>${esc(title)}</h2>${note ? `<p class="how-intro">${esc(note)}</p>` : ""}${body}</section>`;
}

async function load() {
  try {
    if (!Object.keys(languages).length) languages = await fetch("/languages").then((r) => r.json());
    const s = await fetch("/api/stats", { cache: "no-store" }).then((r) => r.json());
    const t = s.totals || {};
    const votes = (s.helpful?.yes || 0) + (s.helpful?.no || 0);
    const helpful = votes ? `${Math.round((s.helpful.yes / votes) * 100)}%` : "–";
    main.innerHTML = `
      <h1>Dalil in numbers</h1>
      <p class="lede">Anonymous counts${s.since ? ` since ${esc(s.since)}` : ""}. Dalil never stores photos, message text,
        names or reference numbers: only what kind of document it was, the language and the result.</p>
      ${s.error ? `<p class="notice">${esc(s.error)}</p>` : ""}
      <div class="how-stats">
        ${tile(t.scan || 0, "documents scanned")}
        ${tile(t.message || 0, "messages checked for scams")}
        ${tile(t.chat || 0, "follow-up questions")}
        ${tile(helpful, "found it clear", votes ? `${votes} vote${votes === 1 ? "" : "s"}` : "")}
      </div>
      ${bars("Documents by type", s.scans_by_type, TYPES)}
      ${bars("Answer languages", s.scans_by_language, languages)}
      ${bars("Number check", s.number_check, CHECKS,
             "Code checks every number the AI writes against the document and the official data before it is shown.")}
      ${bars("Scan results", s.scan_results, RESULTS)}
      ${bars("Scam check results", s.message_verdicts, VERDICTS)}
      <section class="how-card"><h2>Also used</h2>
        <ul class="bars">
          <li><span class="bar-label">"Explain it simpler" taps</span><span class="bar-num">${t.simpler || 0}</span></li>
          <li><span class="bar-label">"Send to family" taps</span><span class="bar-num">${t.share || 0}</span></li>
        </ul></section>
      <p class="muted stats-foot">Updates every 10 seconds. <a href="/">Back to Dalil</a></p>`;
  } catch (err) {
    main.innerHTML = `<h1>Dalil in numbers</h1><p class="notice">Couldn't load the numbers: ${esc(err.message)}</p>`;
  }
}

load();
setInterval(load, 10000);
