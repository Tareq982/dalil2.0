// services tab: placeholder until issue #14 is built.
// Replace the body of render() with the real tab. Keep the exported names:
//   render(el)  - called once, the first time the tab is opened
//   onShow(el)  - optional, called every time the tab is opened again
import { t } from "./i18n.js";
import { esc } from "./util.js";

export function render(el) {
  el.innerHTML = `
    <h1>${esc(t("tab_services"))}</h1>
    <p class="placeholder">${esc(t("coming_services"))}</p>`;
}
