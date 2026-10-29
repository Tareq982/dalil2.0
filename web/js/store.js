// Saved deadlines (issue #13). Kept ONLY in this browser (localStorage), never on our server,
// and never the photo: just the summary the user chose to save.
const KEY = "dalil.deadlines";

export function loadDeadlines() {
  try {
    const list = JSON.parse(localStorage.getItem(KEY) || "[]");
    return Array.isArray(list) ? list : [];
  } catch {
    return [];
  }
}

function write(list) {
  try {
    localStorage.setItem(KEY, JSON.stringify(list));
  } catch {
    return false;
  }
  window.dispatchEvent(new CustomEvent("dalil:deadlines-changed"));
  return true;
}

// Returns false if this browser can't store anything (private mode, blocked storage).
export function addDeadline(item) {
  const id = (crypto.randomUUID && crypto.randomUUID()) || String(Date.now());
  return write([...loadDeadlines(), { ...item, id, saved_at: new Date().toISOString() }]);
}

export function removeDeadline(id) {
  return write(loadDeadlines().filter((d) => d.id !== id));
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

export function sortedDeadlines() {
  return loadDeadlines().sort((a, b) => String(a.date).localeCompare(String(b.date)));
}
