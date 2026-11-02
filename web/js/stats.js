// /stats: anonymous usage numbers (app/stats.py). Refreshes every 10 seconds, so it can stay
// open on a second screen during the demo.
import { esc } from "./util.js";

const TYPES = { traffic_fine: "Traffic fines", visa_residency_notice: "Residency or visa notices",
                tenancy_contract: "Tenancy contracts", other: "Other / not supported", unknown: "Unreadable" };
const RESULTS = { explained: "Explained", fallback: "Too unclear: asked for a better photo", not_supported: "Not a supported document" };
const CHECKS = { passed: "Every number matched the data", retried: "Fixed on the AI's second try", template: "Shown as the data-only version" };
const FINDS = { matched: "Found the right service", question: "Asked one question first", none: "Not in the catalog yet: sent to u.ae" };
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

const pct = (x) => `${Math.round(x * 100)}%`;
const dur = (secs) => (secs == null ? "–" : secs < 90 ? `${Math.round(secs)} s` : `${(secs / 60).toFixed(1)} min`);

// One target: the verdict, without vs with Dalil, and a bar with the target marked
function targetRow({ title, met, value, valueText, target, scaleMax, without, withDalil, empty }) {
  const status = value == null ? ["nodata", empty] : met ? ["met", "Target met"] : ["notyet", "Not met yet"];
  const width = value == null ? 0 : Math.max(0, Math.min(1, value / scaleMax)) * 100;
  return `
    <div class="target">
      <div class="target-head"><h3>${esc(title)}</h3><span class="target-badge ${status[0]}">${esc(status[1])}</span></div>
      ${value == null ? "" : `<p class="target-value">${esc(valueText)}</p>`}
      <div class="target-meter" role="img" aria-label="${esc(value == null ? "No result yet" : valueText)}; target ${esc(pct(target))}">
        <i class="${status[0]}" style="width:${width}%"></i><b style="left:${(target / scaleMax) * 100}%"><span>target ${esc(pct(target))}</span></b>
      </div>
      <div class="target-compare">
        <div><span class="k">Without Dalil</span><span class="v">${esc(without)}</span></div>
        <div><span class="k">With Dalil</span><span class="v">${esc(withDalil)}</span></div>
      </div>
    </div>`;
}

// The challenge's two targets: from the timing test (real people, without vs with Dalil),
// plus what real use of the app shows.
function targetsHtml(tr, live) {
  const w = tr.without || {}, d = tr.with || {};
  const runs = (a) => `${a.runs} run${a.runs === 1 ? "" : "s"}`;
  const cut = tr.discovery_time_cut, inc = tr.adoption_increase;
  const T = tr.targets || { discovery_time_cut: 0.6, adoption_increase: 0.45 };
  const discovery = targetRow({
    title: "60% less time to find the right service", met: tr.met?.discovery, value: cut, target: T.discovery_time_cut, scaleMax: 1,
    valueText: cut == null ? "" : cut >= 0 ? `${pct(cut)} faster with Dalil` : `${pct(-cut)} slower with Dalil`,
    without: w.runs ? `${dur(w.median_seconds)} · ${runs(w)}` : "No runs yet",
    withDalil: d.runs ? `${dur(d.median_seconds)} · ${runs(d)}` : "No runs yet",
    empty: "Needs runs with and without Dalil",
  });
  const adoption = targetRow({
    title: "45% more people reach the official service", met: tr.met?.adoption, value: inc, target: T.adoption_increase, scaleMax: 1,
    valueText: inc == null ? "" : inc >= 0 ? `${pct(inc)} more reached it with Dalil` : `${pct(-inc)} fewer reached it with Dalil`,
    without: w.runs ? `${w.found} of ${w.runs} (${pct(w.found_rate)})` : "No runs yet",
    withDalil: d.runs ? `${d.found} of ${d.runs} (${pct(d.found_rate)})` : "No runs yet",
    empty: w.runs && !w.found ? "Nobody reached it without Dalil, so a % increase can't be worked out" : "Needs runs with and without Dalil",
  });
  let note = "";
  if (!tr.runs) note = `<p class="notice">No timing test yet. <a href="/timing">Run it</a> with at least 5 people: each does one task without Dalil and a different task with Dalil.</p>`;
  else if (!tr.enough) note = `<p class="notice">Only ${w.runs} run${w.runs === 1 ? "" : "s"} without and ${d.runs} with Dalil so far. Aim for at least 5 of each before you quote these numbers.</p>`;
  const say = cut != null && inc != null && tr.enough
    ? `<p class="target-say"><span class="k">What to say</span>“In our timing test with ${Math.round(tr.runs / 2)} people, they found the right official service ${pct(cut)} faster with Dalil${inc > 0 ? `, and ${pct(inc)} more of them got there` : ""}.”</p>`
    : "";
  const liveRate = live.adoption_rate == null ? null : live.adoption_rate;
  return `<section class="how-card targets"><h2>Challenge targets</h2>
    <p class="how-intro">From the <a href="/timing">timing test</a>: real people doing the same kinds of tasks without Dalil
      (any phone, search engine or website) and with Dalil. Time stops when they open the right official page.
      Giving up counts as ${Math.round((tr.time_limit || 300) / 60)} minutes.</p>
    ${discovery}${adoption}${note}${say}
    <div class="live-use">
      <h3>In real use of the app</h3>
      <ul class="bars">
        <li><span class="bar-label">Median time from asking to opening the official service</span><span class="bar-num">${esc(live.timed ? dur(live.median_seconds_to_official) : "–")}</span></li>
        <li><span class="bar-label">Answers where the person opened the official service</span><span class="bar-num">${esc(live.answers ? `${live.opened_official} of ${live.answers} (${pct(liveRate)})` : "–")}</span></li>
        <li><span class="bar-label">Documents marked as paid</span><span class="bar-num">${live.marked_paid || 0}</span></li>
      </ul>
      <p class="muted">${live.answers && !live.opened_official
        ? "Nobody has tapped “Open the official service” after an answer yet, so there is no time to show."
        : "Counted when someone taps “Open the official service” on an answer. This is what a pilot would track."}</p>
    </div></section>`;
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
      ${targetsHtml(s.trial || {}, s.targets || {})}
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
      ${bars("Find a service (no document)", s.find_results, FINDS)}
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
