// Saved documents (My documents tab).
// Signed out: kept only in this browser (localStorage).
// Signed in: kept in the user's account on the server, so they appear on every device.
// Either way: never the photo, only a short summary. The server also drops any field
// that isn't on its allow-list (see app/accounts.py).

import { apiError } from "./errors.js";

const KEY = "dalil.deadlines"; // older versions saved here; kept so nothing is lost
let account = null;              // signed-in email, or null
let remote = [];                 // the account's documents, when signed in
let remoteProfile = {};          // the account's "About you" answers, when signed in
const PROFILE_KEY = "dalil.profile";

function emit() {
  window.dispatchEvent(new CustomEvent("dalil:documents-changed"));
}

function readLocal() {
  try {
    const list = JSON.parse(localStorage.getItem(KEY) || "[]");
    return Array.isArray(list) ? list : [];
  } catch {
    return [];
  }
}

function writeLocal(list) {
  try {
    localStorage.setItem(KEY, JSON.stringify(list));
    return true;
  } catch {
    return false;
  }
}

async function api(path, options = {}) {
  const r = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw apiError(data, r.status);
  return data;
}

const newId = () => (crypto.randomUUID && crypto.randomUUID()) || `${Date.now()}-${Math.random().toString(16).slice(2)}`;

// ---------------------------------------------------------------- account

export function currentAccount() {
  return account;
}

export async function initAccount() {
  try {
    account = (await api("/api/me")).email || null;
    if (account) {
      remote = await api("/api/documents");
      remoteProfile = await api("/api/profile").catch(() => ({}));
    }
  } catch {
    account = null;
  }
  emit();
}

// mode: "login" or "signup". Moves this phone's saved documents into the account.
export async function signIn(mode, email, password) {
  const res = await api(mode === "signup" ? "/api/signup" : "/api/login", { method: "POST", body: { email, password } });
  account = res.email;
  const local = readLocal();
  if (local.length) {
    await api("/api/documents", { method: "POST", body: local });
    writeLocal([]);
  }
  remote = await api("/api/documents");
  // move this phone's "About you" answers into the account, unless the account already has some
  remoteProfile = await api("/api/profile").catch(() => ({}));
  const localProfile = readLocalProfile();
  if (!Object.keys(remoteProfile).length && Object.keys(localProfile).length) {
    remoteProfile = await api("/api/profile", { method: "POST", body: localProfile }).catch(() => localProfile);
  }
  emit();
  return local.length;
}

export async function signOut() {
  await api("/api/logout", { method: "POST", body: {} });
  account = null;
  remote = [];
  remoteProfile = {};
  emit();
}

export async function deleteAccount() {
  await api("/api/account", { method: "DELETE" });
  account = null;
  remote = [];
  remoteProfile = {};
  emit();
}

// ---------------------------------------------------------------- "About you" (personalization)
// A few optional answers (emirate, residence type, expiry date, drives, home). Never names or
// ID numbers; the server keeps only allowed values (app/personal.py).

function readLocalProfile() {
  try {
    const p = JSON.parse(localStorage.getItem(PROFILE_KEY) || "{}");
    return p && typeof p === "object" && !Array.isArray(p) ? p : {};
  } catch {
    return {};
  }
}

export function getProfile() {
  return account ? { ...remoteProfile } : readLocalProfile();
}

export async function saveProfile(profile) {
  const clean = Object.fromEntries(Object.entries(profile).filter(([, v]) => v !== "" && v !== null && v !== undefined && v !== false));
  if (account) {
    try {
      remoteProfile = await api("/api/profile", { method: "POST", body: clean });
    } catch {
      return false;
    }
  } else {
    try { localStorage.setItem(PROFILE_KEY, JSON.stringify(clean)); } catch { return false; }
  }
  emit();
  return true;
}

// ---------------------------------------------------------------- documents

export function listDocuments() {
  return account ? [...remote] : readLocal();
}

// Returns the saved document (with its id), or null if nothing could be saved.
export async function addDocument(item) {
  const doc = { ...item, id: newId(), status: "open", saved_at: new Date().toISOString() };
  if (account) {
    try {
      const [saved] = await api("/api/documents", { method: "POST", body: doc });
      remote.push(saved);
      emit();
      return saved;
    } catch {
      return null;
    }
  }
  if (!writeLocal([...readLocal(), doc])) return null;
  emit();
  return doc;
}

export async function updateDocument(id, changes) {
  const current = listDocuments().find((d) => d.id === id);
  if (!current) return false;
  const doc = { ...current, ...changes };
  if (account) {
    try {
      const [saved] = await api("/api/documents", { method: "POST", body: doc });
      remote = remote.map((d) => (d.id === id ? saved : d));
    } catch {
      return false;
    }
  } else if (!writeLocal(readLocal().map((d) => (d.id === id ? doc : d)))) {
    return false;
  }
  emit();
  return true;
}

export async function removeDocument(id) {
  if (account) {
    try {
      await api(`/api/documents/${encodeURIComponent(id)}`, { method: "DELETE" });
    } catch {
      return false;
    }
    remote = remote.filter((d) => d.id !== id);
  } else {
    writeLocal(readLocal().filter((d) => d.id !== id));
  }
  emit();
  return true;
}

// Open documents with a date first (soonest first), then open without a date, then paid.
export function sortedDocuments() {
  const rank = (d) => (d.status === "paid" ? 2 : d.date ? 0 : 1);
  return listDocuments().sort((a, b) => rank(a) - rank(b) || String(a.date || a.saved_at).localeCompare(String(b.date || b.saved_at)));
}

export function openCount() {
  return listDocuments().filter((d) => d.status !== "paid").length;
}

// Whole days from today to an ISO date (negative = overdue), or null.
export function daysUntil(iso) {
  if (!iso) return null;
  const target = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(target.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((target - today) / 86400000);
}
