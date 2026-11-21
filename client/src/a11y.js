// Accessibility (Phase 4): HIGH-CONTRAST mode + readable warnings. GUI only, never read by the headless sim.
// highContrast is a live ES binding (import { highContrast } stays current); persisted in localStorage "chonoi.hc".
// Toggle: H anywhere (main.js), the pause menu item "Tương phản cao: Bật/Tắt", hint on the title footer.
// HC effects: engine.panel() adds a black outer stroke + opaque border, engine.txt() drops low-alpha text tints and
// thickens text outlines, a base CSS filter contrast(1.25) saturate(1.2) on both canvases; scenes use hc(a, b) for colours
// and draw bigger warning icons with a white outline when highContrast is on.
const KEY = "chonoi.hc";
function readHC() { try { return localStorage.getItem(KEY) === "1"; } catch (e) { return false; } }
export let highContrast = readHC();
export const isHC = () => highContrast;
// palette helper: normal colour, or the high-contrast one when the mode is on
export const hc = (normal, strong) => (highContrast ? strong : normal);
export const HC = { warn: "#ffef00", danger: "#ff2a2a", outline: "#000", light: "#fff" };
const listeners = [];
export function onHighContrast(f) { listeners.push(f); }
export function applyFilter() {
  try {
    for (const id of ["px", "ui"]) { const el = document.getElementById(id); if (el && el.style) el.style.filter = highContrast ? "contrast(1.25) saturate(1.2)" : ""; }
  } catch (e) {}
}
export function setHighContrast(on) {
  highContrast = !!on;
  try { localStorage.setItem(KEY, highContrast ? "1" : "0"); } catch (e) {}
  applyFilter();
  for (const f of listeners) { try { f(highContrast); } catch (e) {} }
  return highContrast;
}
export function toggleHighContrast() { return setHighContrast(!highContrast); }
export const hcLabel = () => "Tương phản cao: " + (highContrast ? "Bật" : "Tắt");
