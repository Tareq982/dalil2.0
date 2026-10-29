// "Add to calendar": builds a standard .ics file that Google Calendar, Apple Calendar
// and Outlook can all open. All-day event on the deadline, with a reminder the day before.

function icsText(value) {
  // Escape characters that have a meaning in .ics files.
  return String(value ?? "").replace(/\\/g, "\\\\").replace(/;/g, "\\;").replace(/,/g, "\\,").replace(/\r?\n/g, "\\n");
}

function fold(line) {
  // .ics lines should be at most 75 bytes; longer ones continue on the next line after a space.
  const out = [];
  let current = "";
  for (const ch of line) {
    if (new TextEncoder().encode(current + ch).length > 73) {
      out.push(current);
      current = " ";
    }
    current += ch;
  }
  out.push(current);
  return out.join("\r\n");
}

const compact = (iso) => iso.replace(/-/g, "");

function nextDay(iso) {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + 1);
  return d.toISOString().slice(0, 10);
}

export function buildICS({ id, title, date, description, url }) {
  const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d+Z$/, "Z");
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Dalil//Deadline reminder//EN",
    "CALSCALE:GREGORIAN",
    "BEGIN:VEVENT",
    `UID:${icsText(id)}@dalil`,
    `DTSTAMP:${stamp}`,
    `DTSTART;VALUE=DATE:${compact(date)}`,
    `DTEND;VALUE=DATE:${compact(nextDay(date))}`,
    `SUMMARY:${icsText(title)}`,
    `DESCRIPTION:${icsText(description)}`,
    ...(url ? [`URL:${String(url).replace(/[\r\n]/g, "")}`] : []), // a URL value is not escaped
    "BEGIN:VALARM",
    "ACTION:DISPLAY",
    `DESCRIPTION:${icsText(title)}`,
    "TRIGGER:-P1D",
    "END:VALARM",
    "END:VEVENT",
    "END:VCALENDAR",
  ];
  return lines.map(fold).join("\r\n") + "\r\n";
}

export function downloadICS(event, filename = "dalil-deadline.ics") {
  const blob = new Blob([buildICS(event)], { type: "text/calendar;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
