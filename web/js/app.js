// App shell: switches tabs from the URL (#scan, #deadlines, #services, #how)
// and asks each tab's module to draw itself the first time it is opened.
// Also owns the interface language picker in the header (issue #16).
import { applyStatic, getLanguage, initLanguage, LANGUAGES, setLanguage } from "./i18n.js";
import { initAccount, openCount } from "./store.js";
import { refreshAccount, setupAccount } from "./account.js";
import * as scan from "./scan.js";
import * as deadlines from "./deadlines.js";
import * as services from "./services.js";
import * as how from "./how.js";

const TABS = { scan, deadlines, services, how };
const rendered = new Set();

function currentTab() {
  const name = location.hash.slice(1);
  return TABS[name] ? name : "scan";
}

function show(name) {
  if (!TABS[name]) name = "scan";
  for (const key of Object.keys(TABS)) {
    document.getElementById(`tab-${key}`).hidden = key !== name;
  }
  document.querySelectorAll(".tabs a").forEach((a) => {
    if (a.dataset.tab === name) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  moveIndicator();
  const panel = document.getElementById(`tab-${name}`);
  if (!rendered.has(name)) {
    TABS[name].render(panel);
    rendered.add(name);
  } else if (TABS[name].onShow) {
    TABS[name].onShow(panel);
  }
}

// Slide the glass pill behind the active tab
function moveIndicator() {
  const active = document.querySelector('.tabs a[aria-current="page"]');
  const pill = document.querySelector(".tab-indicator");
  if (!active || !pill) return;
  pill.style.width = `${active.offsetWidth}px`;
  pill.style.transform = `translateX(${active.offsetLeft}px)`;
}
window.addEventListener("resize", moveIndicator);

// Small count of open (unpaid) documents on the My documents tab
function updateBadge() {
  const link = document.querySelector('.tabs a[data-tab="deadlines"]');
  let badge = link.querySelector(".tab-count");
  const n = openCount();
  if (!n) { if (badge) badge.remove(); return; }
  if (!badge) { badge = document.createElement("span"); badge.className = "tab-count"; link.appendChild(badge); }
  badge.textContent = n;
}

// ---------------------------------------------------------------- interface language

function setupLanguagePicker() {
  const select = document.getElementById("ui-lang");
  for (const [code, name] of Object.entries(LANGUAGES)) {
    const option = new Option(name, code);
    option.lang = code; // each name is written in its own script
    select.add(option);
  }
  select.value = getLanguage();
  select.addEventListener("change", () => setLanguage(select.value));
}

// When the language changes, every label on screen changes with it:
// - the header, tab bar and anything marked data-i18n are re-filled in place;
// - the Scan tab keeps your photo and answer (it only re-labels itself);
// - the other tabs are simply drawn again (they are quick and hold nothing typed in).
window.addEventListener("dalil:language-changed", (e) => {
  document.getElementById("ui-lang").value = e.detail.lang;
  applyStatic();
  scan.onLanguage(e.detail.previous, e.detail.lang);
  for (const name of [...rendered]) if (name !== "scan") rendered.delete(name);
  show(currentTab());
  refreshAccount();
  requestAnimationFrame(moveIndicator); // tab labels changed width, and RTL flips their order
});

initLanguage(); // before anything is drawn, so the first paint is already in the right language
setupLanguagePicker();
applyStatic();
setupAccount();
window.addEventListener("dalil:documents-changed", updateBadge);
initAccount(); // checks if this browser is signed in, then loads the right documents
window.addEventListener("hashchange", () => show(currentTab()));
show(currentTab());
