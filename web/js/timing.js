// /timing: the timing test for the challenge targets (results show on /stats).
// The facilitator reads a task out, presses Start, and presses "Found it" when the tester
// opens the right official page (or "Gave up"). Each tester does two different tasks:
// one without Dalil, one with Dalil, and the order swaps for the next tester.
import { esc } from "./util.js";

const main = document.getElementById("timing");
const NAMES = { without: "Without Dalil", with: "With Dalil" };
let data = null, services = {}, pick = { task: null, condition: "without" };
let startedAt = 0, tick = null, lastSaved = "";

const clock = (secs) => `${Math.floor(secs / 60)}:${String(Math.floor(secs % 60)).padStart(2, "0")}`;
const running = () => startedAt > 0;

// Which run comes next, so tasks and the order (without first / with first) stay balanced
function suggestion() {
  const { runs, last, per_task: per, tasks } = data;
  let condition, avoid = null;
  if (runs % 2 === 1) { condition = last.condition === "with" ? "without" : "with"; avoid = last.task; }
  else condition = runs === 0 ? "without" : last.condition; // the next tester starts the other way round
  const options = tasks.filter((t) => t.id !== avoid);
  options.sort((a, b) => per[a.id][condition] - per[b.id][condition]
    || (per[a.id].with + per[a.id].without) - (per[b.id].with + per[b.id].without));
  return { task: options[0].id, condition };
}

function render() {
  const { runs, tasks, per_task: per, time_limit: limit } = data;
  const task = tasks.find((t) => t.id === pick.task);
  const svc = services[task.service_id] || {};
  const tester = Math.floor(runs / 2) + 1, step = (runs % 2) + 1;
  main.innerHTML = `
    <h1>Timing test</h1>
    <p class="lede">Measures the challenge targets with real people: 60% less time to find the right service, and 45% more people reaching it.
      Results appear on <a href="/stats">Dalil in numbers</a>.</p>

    <section class="how-card">
      <h2>How to run it</h2>
      <ol class="timing-steps">
        <li>Find at least <b>5 testers</b>. Each does <b>two different tasks</b>: one <b>without Dalil</b> (their own phone, any search engine or website) and one <b>with Dalil</b>.</li>
        <li>Use what this page suggests: it swaps the order for each tester, so practice doesn't favour either side.</li>
        <li>Read the task out and press <b>Start</b>. Press <b>Found it</b> when they open the right official page (shown only to you below), or <b>Gave up</b>. It stops itself at ${clock(limit)}.</li>
        <li>Don't help them during a run.</li>
      </ol>
    </section>

    <section class="how-card">
      <h2>Tester ${tester} · run ${step} of 2</h2>
      <p class="suggest">Suggested: <b>${esc(NAMES[suggestion().condition])}</b>, task “${esc(tasks.find((t) => t.id === suggestion().task).task)}”</p>
      <div class="cond-toggle" role="group" aria-label="Without or with Dalil">
        ${["without", "with"].map((c) => `<button type="button" data-cond="${c}" class="${pick.condition === c ? "on" : ""}" ${running() ? "disabled" : ""}>${NAMES[c]}</button>`).join("")}
      </div>
      <label class="field-label" for="t-task" style="margin-top:4px">Task</label>
      <select id="t-task" ${running() ? "disabled" : ""}>
        ${tasks.map((t) => `<option value="${t.id}"${t.id === pick.task ? " selected" : ""}>${esc(t.task)}</option>`).join("")}
      </select>
      <p class="timer-task">${esc(task.task)}</p>
      <div class="timer-answer"><span class="k">Right answer (for you, not the tester)</span>
        <span>${esc(svc.service_name || task.service_id)}${svc.authority && !(svc.service_name || "").includes(svc.authority) ? ` · ${esc(svc.authority)}` : ""}</span>
        ${svc.official_url ? `<span class="muted">${esc(new URL(svc.official_url).hostname.replace(/^www\./, ""))}</span>` : ""}</div>
      <div class="timer-clock" id="t-clock" aria-live="off">${clock(running() ? (performance.now() - startedAt) / 1000 : 0)}</div>
      ${running()
        ? `<div class="timer-buttons"><button class="btn" type="button" id="t-found">Found it</button>
             <button class="btn gave-up" type="button" id="t-gave">Gave up</button></div>
           <button class="link-btn plain" type="button" id="t-cancel" style="justify-self:center">Cancel this run (not saved)</button>`
        : `<button class="btn" type="button" id="t-start">Start</button>`}
      <p class="ok-note" id="t-status" aria-live="polite">${esc(lastSaved)}</p>
    </section>

    <section class="how-card">
      <h2>Runs so far: ${runs}</h2>
      <table class="runs-table">
        <thead><tr><th>Task</th><th class="n">Without</th><th class="n">With</th></tr></thead>
        <tbody>${tasks.map((t) => `<tr><td>${esc(t.task.split(".")[0])}</td><td class="n">${per[t.id].without}</td><td class="n">${per[t.id].with}</td></tr>`).join("")}</tbody>
      </table>
      ${runs ? `<button class="link-btn" type="button" id="t-undo">Undo the last run</button>` : ""}
    </section>
    <p class="muted stats-foot"><a href="/stats">See the results</a> · <a href="/">Back to Dalil</a></p>`;
  wire();
}

function wire() {
  main.querySelectorAll("[data-cond]").forEach((b) => b.addEventListener("click", () => { pick.condition = b.dataset.cond; render(); }));
  main.querySelector("#t-task").addEventListener("change", (e) => { pick.task = e.target.value; render(); });
  main.querySelector("#t-start")?.addEventListener("click", start);
  main.querySelector("#t-found")?.addEventListener("click", () => finish(true));
  main.querySelector("#t-gave")?.addEventListener("click", () => finish(false));
  main.querySelector("#t-cancel")?.addEventListener("click", () => { stop(); lastSaved = "Run cancelled, nothing saved."; render(); });
  main.querySelector("#t-undo")?.addEventListener("click", async () => {
    data = await fetch("/api/trials/undo", { method: "POST" }).then((r) => r.json());
    lastSaved = "Last run removed."; pick = suggestion(); render();
  });
}

function start() {
  startedAt = performance.now(); lastSaved = "";
  render();
  tick = setInterval(() => {
    const secs = (performance.now() - startedAt) / 1000;
    const el = document.getElementById("t-clock");
    if (el) el.textContent = clock(secs);
    if (secs >= data.time_limit) finish(false, data.time_limit);
  }, 250);
}

function stop() { clearInterval(tick); tick = null; startedAt = 0; }

async function finish(found, forced) {
  if (!running()) return;
  const seconds = forced || Math.max(0.1, (performance.now() - startedAt) / 1000);
  const run = { task: pick.task, condition: pick.condition, seconds: Math.round(seconds * 10) / 10, found };
  stop();
  try {
    const r = await fetch("/api/trials", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(run) });
    const body = await r.json();
    if (!r.ok) throw new Error(body.error || "Not saved.");
    data = body;
    lastSaved = `Saved: ${NAMES[run.condition]}, ${clock(run.seconds)}, ${found ? "found it" : forced ? "ran out of time" : "gave up"}.`;
    pick = suggestion();
  } catch (err) {
    lastSaved = `Not saved: ${err.message}`;
  }
  render();
}

async function load() {
  try {
    const [d, list] = await Promise.all([fetch("/api/trials").then((r) => r.json()), fetch("/services").then((r) => r.json())]);
    data = d;
    services = Object.fromEntries(list.map((s) => [s.id, s]));
    if (data.error) throw new Error(data.error);
    pick = suggestion();
    render();
  } catch (err) {
    main.innerHTML = `<h1>Timing test</h1><p class="notice">Couldn't load the test: ${esc(err.message)}</p>`;
  }
}

load();
