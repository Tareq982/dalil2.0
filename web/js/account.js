// Account sheet: sign in / create account / sign out / delete. Opened from the header button.
import { t } from "./i18n.js";
import { esc } from "./util.js";
import { currentAccount, deleteAccount, signIn, signOut } from "./store.js";

const ICON_PERSON = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8.5" r="3.8"/><path d="M4.8 19.5c1.3-3.3 4-5 7.2-5s5.9 1.7 7.2 5"/></svg>';
const ICON_LOCK = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="10" width="14" height="10" rx="2.5"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></svg>';

let dialog;
let mode = "login";

export function setupAccount() {
  dialog = document.getElementById("account-dialog");
  document.getElementById("account-btn").addEventListener("click", openAccount);
  dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); }); // tap outside closes
  window.addEventListener("dalil:documents-changed", updateButton);
  updateButton();
}

function updateButton() {
  const btn = document.getElementById("account-btn");
  const email = currentAccount();
  btn.innerHTML = email ? `<span class="avatar">${esc(email[0].toUpperCase())}</span>` : ICON_PERSON;
  btn.setAttribute("aria-label", email ? `${t("acc_signed_in_as")} ${email}` : t("acc_sign_in"));
}

export function openAccount() {
  draw();
  if (!dialog.open) dialog.showModal();
}

function privacyNote() {
  return `<p class="privacy-note left">${ICON_LOCK}<span>${esc(t("acc_privacy"))}</span></p>`;
}

function draw() {
  const email = currentAccount();
  if (email) {
    dialog.innerHTML = `
      <div class="sheet-head"><h2>${esc(t("acc_title"))}</h2><button class="close" aria-label="${esc(t("acc_close"))}">✕</button></div>
      <div class="account-card"><span class="avatar big">${esc(email[0].toUpperCase())}</span>
        <div><p class="muted">${esc(t("acc_signed_in_as"))}</p><p class="acc-email">${esc(email)}</p></div></div>
      <p>${esc(t("acc_synced"))}</p>
      ${privacyNote()}
      <button class="btn btn-quiet" id="acc-signout">${esc(t("acc_sign_out"))}</button>
      <button class="link-btn danger" id="acc-delete">${esc(t("acc_delete"))}</button>
      <p class="form-error" id="acc-error" role="alert"></p>`;
    dialog.querySelector("#acc-signout").addEventListener("click", async () => {
      await signOut().catch(() => {});
      dialog.close();
    });
    const del = dialog.querySelector("#acc-delete");
    del.addEventListener("click", async () => {
      if (!del.dataset.confirm) { // ask twice instead of a browser pop-up
        del.dataset.confirm = "1";
        del.textContent = t("acc_delete_confirm");
        return;
      }
      try { await deleteAccount(); dialog.close(); } catch (err) { dialog.querySelector("#acc-error").textContent = err.message; }
    });
  } else {
    dialog.innerHTML = `
      <div class="sheet-head"><h2>${esc(t(mode === "signup" ? "acc_create" : "acc_sign_in"))}</h2><button class="close" aria-label="${esc(t("acc_close"))}">✕</button></div>
      <p class="muted">${esc(t("acc_why"))}</p>
      <div class="segmented" role="tablist">
        <button role="tab" data-mode="login" aria-selected="${mode === "login"}">${esc(t("acc_sign_in"))}</button>
        <button role="tab" data-mode="signup" aria-selected="${mode === "signup"}">${esc(t("acc_create"))}</button>
      </div>
      <form id="acc-form" novalidate>
        <label class="field-label" for="acc-email">${esc(t("acc_email"))}</label>
        <input type="email" id="acc-email" autocomplete="email" required>
        <label class="field-label" for="acc-pass">${esc(t("acc_password"))}</label>
        <input type="password" id="acc-pass" minlength="8" required
               autocomplete="${mode === "signup" ? "new-password" : "current-password"}">
        ${mode === "signup" ? `<p class="muted hint">${esc(t("acc_password_hint"))}</p>` : ""}
        <p class="form-error" id="acc-error" role="alert"></p>
        <button class="btn" type="submit" id="acc-submit">${esc(t(mode === "signup" ? "acc_create" : "acc_sign_in"))}</button>
      </form>
      ${privacyNote()}`;
    dialog.querySelectorAll(".segmented button").forEach((b) => b.addEventListener("click", () => { mode = b.dataset.mode; draw(); }));
    dialog.querySelector("#acc-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const submit = dialog.querySelector("#acc-submit");
      submit.disabled = true;
      try {
        const moved = await signIn(mode, dialog.querySelector("#acc-email").value, dialog.querySelector("#acc-pass").value);
        draw();
        if (moved) dialog.querySelector("p:not(.muted)").insertAdjacentHTML("afterend", `<p class="ok-note">${esc(t("acc_moved").replace("{n}", moved))}</p>`);
      } catch (err) {
        dialog.querySelector("#acc-error").textContent = err.message;
        submit.disabled = false;
      }
    });
  }
  dialog.querySelector(".close").addEventListener("click", () => dialog.close());
}
