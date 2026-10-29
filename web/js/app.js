// App shell: switches tabs from the URL (#scan, #deadlines, #services, #how)
// and asks each tab's module to draw itself the first time it is opened.
import { applyStatic } from "./i18n.js";
import { loadDeadlines } from "./store.js";
import * as scan from "./scan.js";
import * as deadlines from "./deadlines.js";
import * as services from "./services.js";
import * as how from "./how.js";

const TABS = { scan, deadlines, services, how };
const rendered = new Set();

function show(name) {
  if (!TABS[name]) name = "scan";
  for (const key of Object.keys(TABS)) {
    document.getElementById(`tab-${key}`).hidden = key !== name;
  }
  document.querySelectorAll(".tabs a").forEach((a) => {
    if (a.dataset.tab === name) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  const panel = document.getElementById(`tab-${name}`);
  if (!rendered.has(name)) {
    TABS[name].render(panel);
    rendered.add(name);
  } else if (TABS[name].onShow) {
    TABS[name].onShow(panel);
  }
}

// Small count on the My deadlines tab
function updateBadge() {
  const link = document.querySelector('.tabs a[data-tab="deadlines"]');
  let badge = link.querySelector(".tab-count");
  const n = loadDeadlines().length;
  if (!n) { if (badge) badge.remove(); return; }
  if (!badge) { badge = document.createElement("span"); badge.className = "tab-count"; link.appendChild(badge); }
  badge.textContent = n;
}

applyStatic();
updateBadge();
window.addEventListener("dalil:deadlines-changed", updateBadge);
window.addEventListener("hashchange", () => show(location.hash.slice(1)));
show(location.hash.slice(1) || "scan");
