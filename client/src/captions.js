// SFX captions (Phase 4 extension "Phụ đề SFX", TICKET-04 §3). GUI only, never read by the headless sim.
// audio.sfx(name, arg, cap) calls caption(name, cap) BEFORE its mute check, so captions also show when muted.
// Shown when the setting is on (U toggles, saved in localStorage "chonoi.cc") or automatically while muted (M).
// Lines stack bottom-left above the key-hint bar; a repeat of the same text refreshes it and shows "×n".
const KEY = "chonoi.cc";
function readCC() { try { return localStorage.getItem(KEY) === "1"; } catch (e) { return false; } }
export let captionsOn = readCC();

// what each sound means to the player; UI clicks/blips are left out on purpose (they add noise, not information)
export const CAPTION = {
  hurt: "[tiếng đau / lỗi]",
  slam: "[va mạnh]",
  boom: "[tiếng nổ trầm]",
  coin: "[tiếng tiền rơi]",
  ding: "[chuông ding]",
  fanfare: "[kèn chiến thắng]",
  sting_win: "[nhạc thắng lớn]",
  whoosh: "[vút]",
  swish: "[gió lướt]",
  riser: "[nhạc dồn dập]",
  bubble: "[bọt nước ục ục]",
  splash: "[tiếng nhảy xuống nước]",
  splash_big: "[nước bắn tung tóe]",
  catch: "[lao móc trúng]",
  pick: "[hái / nhặt]",
  sizzle: "[chảo xèo xèo]",
  heartbeat: "[tim đập thình thịch]",
};

const MAX = 4, LIFE = 2.4;
const lines = [];
let _muted = () => false;
export function bindMuted(fn) { _muted = fn; }
export const captionsVisible = () => captionsOn || _muted();

export function setCaptions(on) {
  captionsOn = !!on;
  try { localStorage.setItem(KEY, captionsOn ? "1" : "0"); } catch (e) {}
  if (!captionsOn) lines.length = 0;
  return captionsOn;
}
export function toggleCaptions() { return setCaptions(!captionsOn); }
export const ccLabel = () => "Phụ đề âm thanh: " + (captionsOn ? "Bật" : _muted() ? "Tự bật (tắt tiếng)" : "Tắt");

// cap: optional caller-specific text (e.g. "[Cá Sấu cắn]") that overrides the generic one; false = no caption
export function caption(name, cap) {
  if (cap === false) return;
  const text = cap || CAPTION[name];
  if (!text || !captionsVisible()) return;
  const same = lines.find((l) => l.text === text);
  if (same) { same.n++; same.life = LIFE; return; }
  lines.push({ text, n: 1, life: LIFE });
  while (lines.length > MAX) lines.shift();
}

export function captionLines() { return lines; }
export function updateCaptions(dt) {
  for (const l of lines) l.life -= dt;
  for (let i = lines.length - 1; i >= 0; i--) if (lines[i].life <= 0) lines.splice(i, 1);
}

// draw with engine helpers passed in (keeps this module free of engine imports for unit checks)
export function drawCaptions({ txt, panel, measure, H, hc }) {
  if (!captionsVisible() || !lines.length) return;
  const x = 8, lh = 13;
  let y = H - 30 - lines.length * lh;
  for (const l of lines) {
    const s = l.n > 1 ? `${l.text} ×${l.n}` : l.text;
    const a = Math.min(1, l.life / 0.4);
    const w = (measure ? measure(s, 8, 800) : s.length * 4.4) + 10;
    panel(x, y, w, lh - 2, { fill: hc ? "rgba(0,0,0,.95)" : "rgba(6,12,24,.82)", border: hc ? "#fff" : "rgba(255,255,255,.35)", r: 3, bw: hc ? 1.5 : 1, alpha: a });
    txt(s, x + 5, y + 8, { size: 8, color: hc ? "#ffef00" : "#fff", weight: 800, alpha: a });
    y += lh;
  }
}
