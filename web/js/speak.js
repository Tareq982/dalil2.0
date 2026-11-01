// Read aloud (issue #17): a "Listen" button that reads the explanation in the answer language,
// using the voices built into the phone or computer (speechSynthesis). No server, no cost.
// The button only appears when the device has a voice for that language.

const synth = "speechSynthesis" in window ? window.speechSynthesis : null;

// Dalil language -> voice language codes to look for ("fil" is what phones call Tagalog)
const VOICE_CODES = { en: ["en"], ar: ["ar"], hi: ["hi"], ur: ["ur"], tl: ["fil", "tl"], bn: ["bn"], ml: ["ml"] };
// Preferred regional voices when there are several
const PREFER = { en: ["en-gb", "en-us"], ar: ["ar-ae", "ar-sa"], ur: ["ur-pk", "ur-in"], bn: ["bn-bd", "bn-in"] };

const ICON_SPEAKER = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M15.5 9a4 4 0 0 1 0 6M18 6.5a7.5 7.5 0 0 1 0 11"/></svg>';
const ICON_STOP = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="7" y="7" width="10" height="10" rx="2"/></svg>';

let current = null; // the button that is speaking right now

export function voiceFor(lang) {
  if (!synth) return null;
  const codes = VOICE_CODES[lang] || [lang];
  const voices = synth.getVoices().filter((v) => codes.some((c) => v.lang.toLowerCase().replace("_", "-").split("-")[0] === c));
  if (!voices.length) return null;
  const prefer = PREFER[lang] || [];
  return voices.find((v) => prefer.includes(v.lang.toLowerCase().replace("_", "-"))) || voices.find((v) => v.localService) || voices[0];
}

// Voices load a moment after the page opens on some browsers.
function whenVoicesReady(cb) {
  if (!synth) return;
  if (synth.getVoices().length) { cb(); return; }
  let done = false;
  const go = () => { if (!done) { done = true; cb(); } };
  synth.addEventListener?.("voiceschanged", go, { once: true });
  setTimeout(go, 1500);
}

export function stopSpeaking() {
  if (synth) synth.cancel();
  if (current) setState(current, false);
  current = null;
}

function setState(btn, speaking) {
  btn.classList.toggle("speaking", speaking);
  btn.setAttribute("aria-pressed", String(speaking));
  btn.innerHTML = `${speaking ? ICON_STOP : ICON_SPEAKER}<span>${btn.dataset[speaking ? "stop" : "listen"]}</span>`;
}

// Long text is read sentence by sentence: some browsers stop a single long utterance after ~15 s.
function chunks(text) {
  return String(text).split(/(?<=[.!?؟।۔])\s+|\n+/).map((s) => s.trim()).filter(Boolean);
}

/**
 * Adds a Listen button to `slot` (hidden until a voice for `lang` is found).
 * getText() returns what to read; labels = { listen, stop } in the answer language.
 */
export function listenButton(slot, lang, getText, labels) {
  if (!synth || !slot) return;
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "listen-btn";
  btn.hidden = true;
  btn.dataset.listen = labels.listen;
  btn.dataset.stop = labels.stop;
  setState(btn, false);
  slot.appendChild(btn);

  whenVoicesReady(() => { btn.hidden = !voiceFor(lang); });

  btn.addEventListener("click", () => {
    if (current === btn) { stopSpeaking(); return; }
    stopSpeaking();
    const voice = voiceFor(lang);
    if (!voice) { btn.hidden = true; return; }
    const parts = chunks(getText());
    if (!parts.length) return;
    current = btn;
    setState(btn, true);
    parts.forEach((part, i) => {
      const u = new SpeechSynthesisUtterance(part);
      u.voice = voice;
      u.lang = voice.lang;
      u.rate = 0.92; // a little slower: easier to follow
      if (i === parts.length - 1) u.onend = () => { if (current === btn) stopSpeaking(); };
      u.onerror = () => { if (current === btn) stopSpeaking(); };
      synth.speak(u);
    });
  });
}

// Stop when the person leaves the page or switches tab.
window.addEventListener("hashchange", stopSpeaking);
window.addEventListener("pagehide", stopSpeaking);
