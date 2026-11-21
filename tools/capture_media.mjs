#!/usr/bin/env node
// Marketing media capture for Quán Ăn Chợ Nổi — screenshots + a fast demo video, by scripting headless Chrome
// over the DevTools Protocol (Node ≥ 21: global fetch + WebSocket, no npm deps). Game code is NOT touched: the page
// is driven only through the ?debug hook (window.__chonoi: go / step / input) and synthetic KeyboardEvents.
// Capture-side shims injected before the game loads: seeded Math.random (deterministic runs) and a holdable
// requestAnimationFrame, so every captured frame is produced by __chonoi.step(n) (in-game time = n/60 s).
//
//   node tools/capture_media.mjs                 # stills + video → docs/media/
//   node tools/capture_media.mjs --stills        # screenshots only
//   node tools/capture_media.mjs --video         # demo.mp4 only
//   node tools/capture_media.mjs --base http://127.0.0.1:8096   # reuse a running static server (else one is started)
//
// Needs: Google Chrome (CHROME env to override), python3 (static server), ffmpeg (FFMPEG env; video only).
import { spawn, spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import net from "node:net";
import os from "node:os";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(ROOT, "docs/media"), SHOTS = path.join(OUT, "screenshots");
const CHROME = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const FFMPEG = process.env.FFMPEG || "/opt/homebrew/bin/ffmpeg";
const FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf";
const args = process.argv.slice(2);
const want = { stills: !args.includes("--video"), video: !args.includes("--stills") };
const baseArg = args.includes("--base") ? args[args.indexOf("--base") + 1] : null;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);

const freePort = () => new Promise((r) => { const s = net.createServer(); s.listen(0, "127.0.0.1", () => { const p = s.address().port; s.close(() => r(p)); }); });

// ---------------------------------------------------------------- page-side helpers (strings evaluated in the page)
const INJECT = `(() => {
  let s = 42; Math.random = function () { s = (s + 0x6d2b79f5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  const raf = window.requestAnimationFrame.bind(window); const q = [];
  window.__hold = false;
  window.requestAnimationFrame = (cb) => { if (window.__hold) { q.push(cb); return 0; } return raf(cb); };
  window.__key = (key, type = "keydown") => window.dispatchEvent(new KeyboardEvent(type, { key, bubbles: true }));
  window.__tap = (key) => { window.__key(key, "keydown"); window.__key(key, "keyup"); };
})();`;

const HELPERS = `(() => {
  const G = () => window.__chonoi, sc = () => G().state.scene;
  window.__run = (n, o = {}) => {
    const sayHold = o.sayHold ?? 70;
    for (let i = 0; i < n; i++) {
      const s = sc();
      if (G().state.mode === "cut" && s && s.say && s.say.text && s.say.shown >= s.say.text.length) { s.__sh = (s.__sh || 0) + 1; if (s.__sh > sayHold) { s.__sh = 0; G().input.press("confirm"); } }
      if (window.__bot) window.__bot();
      G().step(1);
    }
    return G().state.mode;
  };
  window.__until = (pred, max = 3000, o = {}) => { for (let i = 0; i < max; i++) { try { if (pred(sc(), G().state)) return i; } catch (e) {} __run(1, o); } return -1; };
  window.__press = (k, n = 1) => { G().input.press(k); __run(n); };
  const held = new Set();
  const setKey = (k, on) => { if (on && !held.has(k)) { held.add(k); __key(k, "keydown"); } else if (!on && held.has(k)) { held.delete(k); __key(k, "keyup"); } };
  window.__releaseAll = () => { for (const k of [...held]) setKey(k, false); };
  // steer toward a target; vertical key sense: gather +d = down, quán/hub +z = up
  const steer = (dx, dy, tol, up) => { setKey("ArrowRight", dx > tol); setKey("ArrowLeft", dx < -tol); setKey(up ? "ArrowUp" : "ArrowDown", dy > tol); setKey(up ? "ArrowDown" : "ArrowUp", dy < -tol); };
  window.__swim = (x, d, max = 600, tol = 0.8, sprint = false) => {
    let i = 0;
    for (; i < max; i++) { const p = sc().p; const dx = x - p.x, dd = d - p.d; if (Math.abs(dx) < tol && Math.abs(dd) < tol) break; steer(dx, dd, tol * 0.5, false); setKey("Shift", sprint); __run(1); }
    __releaseAll(); return i;
  };
  window.__walk = (x, z, max = 400, tol = 0.35) => {
    let i = 0;
    for (; i < max; i++) { const p = sc().p; const dx = x - p.x, dz = z - (p.z ?? z); if (Math.abs(dx) < tol && Math.abs(dz) < tol) break; steer(dx, dz, tol * 0.5, true); __run(1); }
    __releaseAll(); return i;
  };
  window.__fish = (kind, maxD = 99, minD = 1.5) => { const s = sc(), p = s.p; return s.fish.filter((f) => !f.caught && !f.hooked && (!kind || f.kind === kind) && f.d < maxD && f.d > minD).sort((a, b) => Math.hypot(a.x - p.x, a.d - p.d) - Math.hypot(b.x - p.x, b.d - p.d))[0]; };
  // line up level with a fish at gap m, face it, fire (Space); returns true when the spear is out
  window.__hunt = (f, gap = 4, max = 500) => {
    for (let i = 0; i < max; i++) { const p = sc().p; const side = p.x <= f.x ? -1 : 1; const dx = f.x + side * gap - p.x, dd = f.d - p.d; if (Math.abs(dx) < 0.7 && Math.abs(dd) < 0.5) break; steer(dx, dd, 0.3, false); __run(1); }
    __releaseAll();
    const p = sc().p, k = f.x > p.x ? "ArrowRight" : "ArrowLeft"; __key(k, "keydown"); __run(2); __key(k, "keyup");
    G().input.press("catch"); __run(1); return !!sc().harp;
  };
  window.__reel = (max = 120) => __until((s) => !s.harp, max);
  window.__flowers = (n = 3, kind = "bong_sung") => { const s = sc(); let got = 0; for (const nd of s.nodes.filter((x) => x.ready && x.kind === kind).sort((a, b) => Math.abs(a.pos[0] - s.p.x) - Math.abs(b.pos[0] - s.p.x))) { if (got >= n) break; __swim(nd.pos[0], 0, 500, 0.6, true); __run(4); G().input.press("interact"); __run(20); got++; } return got; };
  // ---- Bà Tư dialog (phone.js Nav): one key per call toward the item whose label contains the given text; "done" after E
  window.__navGo = (label) => {
    const ov = sc().overlay; if (!ov || !ov.nav) return "none";
    const nav = ov.nav, pg = nav.page(), i = pg.items.findIndex((it) => String(it.label || "").includes(label));
    if (i < 0) return "missing";
    if (nav.cur.sel !== i) { G().input.press(nav.cur.sel < i ? "down" : "up"); return "move"; }
    G().input.press("interact"); return "done";
  };
  // ---- shop pop-up (shop_popup.js): Tab to "Nâng cấp", arrows to the card with this id, E = OK (one level)
  window.__shopGo = (id) => {
    const ov = sc().overlay; if (!ov || !ov.cards) return "none";
    if (ov.tab !== 2) { G().input.press("tab"); return "move"; }
    const i = ov.cards().findIndex((cd) => cd.id === id); if (i < 0) return "missing";
    if (ov.sel !== i) { G().input.press(ov.sel < i ? "right" : "left"); return "move"; }
    G().input.press("interact"); return "done";
  };
  // ---- quán service bot: one decision per step from live state — cook what a seated guest ordered at a free stove
  // (cook menu: E, arrows to the dish's index in Object.keys(menu), E), wait, pick it up (E), carry it to that guest's
  // table, serve (E). Never presses Esc outside a menu (Esc = pause in the quán, which froze the old bot).
  window.__serveBot = () => {
    const s = sc(), st = G().state;
    if (!s || st.mode !== "quan" || s.phase !== "open" || s.result || st.paused) { __releaseAll(); return; }
    const b = s.__b || (s.__b = { cool: 0, dish: null, serves: 0 });
    if (b.cool > 0) { b.cool--; return; }
    if (s.overlay) { __releaseAll(); G().input.press("back"); b.cool = 8; return; }
    if (s._menuOpen) {
      __releaseAll();
      const keys = Object.keys(s.menu), idx = keys.indexOf(b.dish);
      if (idx < 0) { G().input.press("back"); b.cool = 6; return; }
      if ((s.menuSel | 0) !== idx) { const n = keys.length, dn = (idx - s.menuSel + n) % n; G().input.press(dn <= n / 2 ? "down" : "up"); b.cool = 3; return; }
      G().input.press("interact"); b.cool = 6; b.dish = null; return;
    }
    const R = 0.3;
    const go = (x, z) => { const dx = x - s.p.x, dz = z - s.p.z; if (Math.abs(dx) < R && Math.abs(dz) < R) { __releaseAll(); return true; } steer(dx, dz, R * 0.5, true); return false; };
    const waiting = s.customers.filter((c) => c.state === "waiting" && c.table && !c.unfulfillable).sort((a, b) => a.patience - b.patience);
    const tablePos = (c) => s.tables.find((t) => t.id === c.table).pos;
    const atStove = (sv) => go(sv.pos[0], sv.pos[1] - 1);
    if (s.hand) {
      const c = waiting.find((c) => c.want === s.hand.key);
      if (c) { const tp = tablePos(c); if (go(tp[0] - 1, tp[1])) { G().input.press("interact"); b.cool = 4; b.serves++; } return; }
      if (atStove(s.stoves[0])) { G().input.press("interact"); b.cool = 4; } return; // nobody wants it any more: dump it
    }
    const inPot = s.stoves.filter((sv) => sv.state !== "idle").map((sv) => sv.dish);
    const wanted = waiting.map((c) => c.want);
    const ready = s.stoves.find((sv) => sv.state === "ready" && wanted.includes(sv.dish));
    if (ready) { if (atStove(ready)) { G().input.press("interact"); b.cool = 4; } return; }
    const need = wanted.filter((k) => { const i = inPot.indexOf(k); if (i >= 0) { inPot.splice(i, 1); return false; } return s.menu[k] && s.canCook(k); });
    const idle = s.stoves.find((sv) => sv.state === "idle");
    if (need.length && idle) { b.dish = need[0]; if (atStove(idle)) { G().input.press("interact"); b.cool = 3; } return; }
    const any = s.stoves.find((sv) => sv.state === "ready") || s.stoves.find((sv) => sv.state === "cooking");
    if (any) { atStove(any); return; }   // wait by the pot
    go(6.5, 4.5);
  };
})();`;

// ---------------------------------------------------------------- Chrome + CDP
async function launch() {
  const port = await freePort();
  const prof = fs.mkdtempSync(path.join(os.tmpdir(), "chonoi-cap-"));
  const ch = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${port}`, "--window-size=1280,720", "--force-device-scale-factor=1",
    "--autoplay-policy=no-user-gesture-required", `--user-data-dir=${prof}`, "--no-first-run", "--no-default-browser-check", "--mute-audio", "--hide-scrollbars", "about:blank"], { stdio: "ignore" });
  let tabs;
  for (let i = 0; i < 100; i++) { try { tabs = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); if (tabs.length) break; } catch { } await sleep(150); }
  const pg = tabs.find((t) => t.type === "page");
  const ws = new WebSocket(pg.webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  let id = 0; const pend = new Map();
  ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { const [r, j] = pend.get(d.id); pend.delete(d.id); d.error ? j(new Error(d.error.message)) : r(d.result); } };
  const send = (method, params = {}) => new Promise((r, j) => { const i = ++id; pend.set(i, [r, j]); ws.send(JSON.stringify({ id: i, method, params })); });
  await send("Page.enable"); await send("Runtime.enable");
  // CSS viewport 1200×675 at DPR 1.0667 → the game's integer-ish 2.5× fit fills the frame; screenshots are exactly 1280×720
  await send("Emulation.setDeviceMetricsOverride", { width: 1200, height: 675, deviceScaleFactor: 1280 / 1200, mobile: false });
  await send("Page.addScriptToEvaluateOnNewDocument", { source: INJECT });
  const ev = async (expr) => { const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true }); if (r.exceptionDetails) throw new Error(expr.slice(0, 80) + " → " + (r.exceptionDetails.exception?.description || r.exceptionDetails.text)); return r.result.value; };
  const shot = async (file, fmt = "png", q = 90) => { const r = await send("Page.captureScreenshot", fmt === "png" ? { format: "png" } : { format: "jpeg", quality: q }); fs.writeFileSync(file, Buffer.from(r.data, "base64")); };
  const nav = async (url, ready = "!!window.__chonoi") => { await send("Page.navigate", { url }); for (let i = 0; i < 200; i++) { await sleep(100); try { if (await ev(ready)) break; } catch { } } };
  const close = async () => { try { ws.close(); } catch { } ch.kill(); await new Promise((r) => { ch.once("exit", r); setTimeout(r, 3000); }); try { fs.rmSync(prof, { recursive: true, force: true, maxRetries: 3 }); } catch { } };
  return { send, ev, shot, nav, close };
}

// ---------------------------------------------------------------- shared playthrough steps
const paint = (c) => c.ev("new Promise((r) => setTimeout(r, 80))");
async function bootDebug(c, base) {
  await c.nav(`${base}/client/index.html?debug`, "!!(window.__chonoi && __chonoi.state.mode === 'title')");
  await c.ev(HELPERS);
}

// ---------------------------------------------------------------- stills
async function stills(base) {
  fs.mkdirSync(SHOTS, { recursive: true });
  const c = await launch(); const saved = [];
  const snap = async (name) => { await paint(c); const f = path.join(SHOTS, name + ".png"); await c.shot(f); saved.push(f); log("shot", name); };
  try {
    // 02 splash video (normal URL: no ?debug / ?novideo)
    await c.nav(`${base}/client/index.html`, "!!document.querySelector('video') && document.querySelector('video').currentTime > 0");
    await c.ev(`new Promise((r) => { const v = document.querySelector('video'); const t0 = performance.now(); const k = () => (v.currentTime >= 4 || performance.now() - t0 > 6000) ? r() : setTimeout(k, 50); k(); })`);
    await snap("02-splash-video");

    // 01 title key art (real rAF for a second so the menu pulse settles)
    await bootDebug(c, base); await sleep(1200);
    await c.ev("__hold = true; __run(1)"); await snap("01-title-key-art");

    // intro cutscene (new campaign)
    await c.ev(`__chonoi.go("new"); __until((s) => s.say && s.say.say === "Bà Tư" && s.say.shown >= s.say.text.length, 3000); __run(20)`);
    await snap("03-intro-cutscene-dialogue");
    await c.ev(`__until((s) => s.card && s.card.type === "intro", 3000); __run(75)`);
    await snap("04-character-intro-ut-sen");
    await c.ev(`__until((s, st) => st.mode === "intro", 5000); __run(100)`);
    await snap("05-day-intro-ma-tu-list");

    // dive
    await c.ev(`__until((s, st) => st.mode === "gather", 2000); __run(240)`); // past the opening hint
    await c.ev(`__swim(11, 5.5, 400); __run(30)`);
    await snap("06-dive-surface-fish-hud");
    await c.ev(`(() => { const f = __fish("ca_linh") || __fish(); __hunt(f, 5); __until((s) => !s.harp || s.harp.hit || s.harp.dist > 3.6, 30); })()`);
    await snap("07-harpoon-in-flight");
    // a few more catches (cá lóc for tonight's menu) + bông súng from the surface
    await c.ev(`__reel(); for (let i = 0; i < 6; i++) { const f = __fish(i < 4 ? "ca_loc" : null, 20) || __fish(null, 20); if (!f) break; __hunt(f, 4); __reel(); __run(10); if (__chonoi.state.scene.oxy < 12) { __swim(__chonoi.state.scene.p.x, 0, 400, 0.6, true); __run(150); } }`);
    await c.ev(`__key("i"); __run(2); __key("i", "keyup"); __run(30); const s = __chonoi.state.scene; if (s.tutTip) { __key("i"); __run(30); }`);
    await snap("10-inventory-overlay");
    await c.ev(`(() => { const s = __chonoi.state.scene; let n = 0; while ((s.inv || s.tutTip) && n++ < 6) { __press("back", 20); } })()`);
    await c.ev(`__swim(__chonoi.state.scene.p.x, 0, 400, 0.6, true); __run(30); __flowers(4)`);
    // dock, dusk cutscene
    await c.ev(`__swim(2, 0, 1500, 1, true); __run(10); __press("interact", 60); __until((s) => s.result && s.result.t > 0.8, 400); __press("confirm", 10)`);
    await c.ev(`__until((s, st) => st.mode === "cut" && s.v && s.t > 2.2, 1500); __run(10)`);
    await snap("11-dusk-cutscene-lanterns");

    // pre-open raft
    await c.ev(`__until((s, st) => st.mode === "quan" && s.phase === "preopen", 6000); __run(90)`);
    await c.ev(`__walk(13.2, 4.4, 300); __run(30)`);
    await snap("12-preopen-raft-mo-quan");
    await c.ev(`__walk(5.8, 8.2, 400); __press("interact", 45)`);
    await snap("13-menu-board-dac-san");
    await c.ev(`__press("back", 30); __walk(1.1, 8.7, 300, 0.2); __press("interact", 45)`);
    await snap("15-ba-tu-dialog");
    await c.ev(`(() => { const s = __chonoi.state.scene; let n = 0; while (s.overlay && n++ < 12) __press(n < 8 ? "back" : "confirm", 15); })()`);

    // service: open, play ~50 s with the bot
    await c.ev(`__walk(13.6, 4.2, 400); __press("open", 6); __press("confirm", 40)`);
    // 14-busy-service is taken by the video run (demo quán with demo stock + the service bot)
    await c.ev(`__chonoi.phone(); __run(40)`);
    await snap("16-phone-overlay");
    await c.ev(`__tap("t"); __run(30)`);

    // night dock hub (debug shortcut "night" on the same save) → Chú Sáu's shop
    await c.ev(`window.__bot = null; __releaseAll(); __chonoi.go("night"); __until((s, st) => st.mode === "hub", 600); __run(60)`);
    await c.ev(`__walk(14.6, 1.2, 600); __press("interact", 50)`);
    await snap("17-shop-popup-dock");
    await c.ev(`(() => { const s = __chonoi.state.scene; let n = 0; while (s.menuOpen && n++ < 6) __press("back", 15); })()`);
    // demo dive (no save): Cá Sấu chase + high contrast, then the deep zone
    await c.ev(`__chonoi.go("gather"); __until((s, st) => st.mode === "gather" && s.p, 600); __run(200)`);
    await c.ev(`(() => { const s = __chonoi.state.scene, cr = s.crocs[0]; __swim(cr.x - 10, 0.3, 900, 1, true); for (let i = 0; i < 120 && s.crocWarn < 0.95; i++) { __swim(cr.x - 5, cr.d, 6, 0.6, true); } __run(8); })()`);
    // 09-ca-sau-chase-warning is taken by the video run
    await c.ev(`__press("contrast", 6); __run(10)`);
    await snap("18-high-contrast-dive-warning");
    await c.ev(`__press("contrast", 6)`);
    await c.ev(`(() => { const s = __chonoi.state.scene; __swim(s.p.x, 0, 600, 0.6, true); __run(200); __swim(30, 0.3, 900, 1, true); __run(120); __swim(30, 36, 900, 1.2, true); __run(20); })()`);
    await snap("08-deep-zone-40m");
  } finally { await c.close(); }
  return saved;
}

// ---------------------------------------------------------------- video
// Recording order ≠ edit order: the demo dive (deep zone + Cá Sấu) is recorded BEFORE go("new") (newGame resets the save),
// the demo quán service (demo stock, so the rush never runs dry) AFTER the campaign night; ORDER below places them.
// Speed: most segments advance 6 game frames per 30-fps video frame (≈3×); dialogue / pop-ups run slower to stay readable.
// Also writes screenshots 09 (Cá Sấu warning, empty basket) and 14 (busy service) from the same runs.
const ORDER = ["c-title", "title", "intro", "day", "c-dive", "dive", "c-deep", "deep", "croc", "dock", "dusk", "c-quan", "preopen",
  "c-manage", "hire", "decor", "decorated", "service", "close", "c-night", "night", "train", "c-day2", "day2", "dawn", "c-dive2", "dive2",
  "croc2", "dock2", "c-prem", "eve2", "c-end"];
async function video(base) {
  const TMP = fs.mkdtempSync(path.join(os.tmpdir(), "chonoi-vid-"));
  fs.mkdirSync(SHOTS, { recursive: true });
  const c = await launch(); const segs = [];
  let seg = null, n = 0;
  const begin = (name) => { seg = path.join(TMP, name); fs.mkdirSync(seg, { recursive: true }); n = 0; segs.push({ kind: "seg", dir: seg, name }); log("rec", name); };
  // rec(frames, k, js): capture `frames` video frames, advancing k game frames (k/60 s) between them; js runs before each step
  const rec = async (frames, k = 6, js = "") => { for (let i = 0; i < frames; i++) { if (js) await c.ev(js); await c.ev(`__run(${k})`); await c.shot(path.join(seg, String(n++).padStart(5, "0") + ".jpg"), "jpeg", 88); } };
  const card = (name, title, sub) => segs.push({ kind: "card", name, title, sub });
  const still = async (name) => { await c.shot(path.join(SHOTS, name + ".png")); log("shot", name); };
  const keysUp = `["ArrowRight","ArrowLeft","ArrowDown","ArrowUp","Shift"].forEach((k) => __key(k, "keyup"))`;
  const steerJs = (x, d, sprint) => `(() => { const s = __chonoi.state.scene, p = s.p; const dx = ${x} - p.x, dd = ${d} - p.d;
        const set = (key, on) => __key(key, on ? "keydown" : "keyup");
        set("ArrowRight", dx > 0.5); set("ArrowLeft", dx < -0.5); set("ArrowDown", dd > 0.5); set("ArrowUp", dd < -0.5); set("Shift", ${sprint}); })()`;
  const swimRec = async (x, d, frames, k = 6, sprint = false) => { await rec(frames, k, steerJs(x, d, sprint)); await c.ev(keysUp); };
  try {
    await bootDebug(c, base); await sleep(800); await c.ev("__hold = true; __run(1)");
    card("c-title", "Quán Ăn Chợ Nổi", "Sáng lặn sông · Tối mở quán");
    begin("title"); await rec(75, 1);

    // ---- demo dive first: deep zone (rocks, big fish) and the Cá Sấu chase + spear stun
    card("c-deep", "Vùng sâu 40 m", "Hang đá, cá lớn — và Cá Sấu Năm Chèo");
    // demo dive only: a capture-side guard keeps HP / O₂ topped up so the croc shot never ends in "Ngất xỉu" (no save)
    await c.ev(`window.__bot = () => { const s = __chonoi.state.scene; if (__chonoi.state.mode === "gather" && s && s.hpMax) { s.hp = s.hpMax; s.oxy = Math.max(s.oxy, s.oxyMax * 0.7); } }`);
    await c.ev(`__chonoi.go("gather"); __until((s, st) => st.mode === "gather" && s.p, 600); __run(200); __swim(30, 0.3, 900, 1, true); __run(30)`);
    begin("deep");
    await swimRec(30, 40, 70, 6, true);
    await swimRec(36, 38, 70, 4, false);
    await c.ev(`window.__cr = __chonoi.state.scene.crocs[0]; __swim(__chonoi.state.scene.p.x, 0, 600, 0.6, true); __run(150); __swim(window.__cr.x - 12, Math.max(0.3, window.__cr.d - 1), 1200, 1, true)`);
    begin("croc");
    let warnShot = false;
    for (let i = 0; i < 140; i++) {
      await rec(1, 3, `(() => { const s = __chonoi.state.scene, p = s.p, cr = window.__cr; const dx = cr.x - 5 - p.x, dd = cr.d - p.d;
        const set = (key, on) => __key(key, on ? "keydown" : "keyup");
        if (cr.state === "stunned") { ["ArrowRight","ArrowLeft","ArrowUp","ArrowDown"].forEach((k) => set(k, false)); set("ArrowLeft", true); return; }
        if (s.crocWarn > 0.9 && Math.abs(dd) < 1.5 && Math.abs(dx) < 2.5) { set("ArrowRight", cr.x > p.x); set("ArrowLeft", cr.x < p.x); set("ArrowUp", false); set("ArrowDown", false); if (!s.harp) __chonoi.input.press("catch"); return; }
        set("ArrowRight", dx > 0.5); set("ArrowLeft", dx < -0.5); set("ArrowDown", dd > 0.5); set("ArrowUp", dd < -0.5); set("Shift", true); })()`);
      const st = await c.ev(`({ w: __chonoi.state.scene.crocWarn, cs: window.__cr.state })`);
      if (!warnShot && st.w > 0.9) { warnShot = true; await still("09-ca-sau-chase-warning"); }
      if (st.cs === "stunned" && i > 20) { await rec(70, 3); break; }
    }
    await c.ev(`${keysUp}; window.__bot = null`);

    // ---- campaign: intro → Ngày 1 → dive → dock → dusk → pre-open → Mở quán
    await c.ev(`__chonoi.go("new")`);
    begin("intro"); await rec(70, 3);
    await c.ev(`__until((s) => s.say && s.say.say === "Bà Tư", 3000)`); await rec(70, 2);
    await c.ev(`__until((s) => s.card && s.card.type === "intro", 3000)`); await rec(70, 2);
    await c.ev(`__until((s, st) => st.mode === "intro", 5000)`);
    begin("day"); await rec(70, 2);
    card("c-dive", "Buổi sáng · Lặn sông", "Bắn lao bắt cá, hái bông, canh O₂");
    await c.ev(`__until((s, st) => st.mode === "gather", 2000); __run(150)`);
    // capture-side safety only (both campaign dives): the diver never faints (HP ≥ 2, O₂ ≥ 3 s), so the basket is kept
    await c.ev(`window.__bot = () => { const s = __chonoi.state.scene; if (__chonoi.state.mode === "gather" && s && s.hpMax && !s.result) { s.hp = Math.max(s.hp, 2); s.oxy = Math.max(s.oxy, 3); } }`);
    begin("dive");
    await swimRec(10, 5, 20, 6);
    for (let i = 0; i < 4; i++) {
      const ok = await c.ev(`(() => { const f = __fish("ca_loc", 20) || __fish(null, 20); if (!f) return false; window.__tf = f; return true; })()`);
      if (!ok) break;
      await rec(30, 4, `(() => { const s = __chonoi.state.scene, p = s.p, f = window.__tf; if (s.harp) return; const side = p.x <= f.x ? -1 : 1; const dx = f.x + side * 4 - p.x, dd = f.d - p.d;
        const set = (key, on) => __key(key, on ? "keydown" : "keyup");
        if (Math.abs(dx) < 0.8 && Math.abs(dd) < 0.6) { ["ArrowUp","ArrowDown"].forEach((k) => set(k, false)); set("ArrowRight", f.x > p.x); set("ArrowLeft", f.x < p.x); __chonoi.input.press("catch"); return; }
        set("ArrowRight", dx > 0.3); set("ArrowLeft", dx < -0.3); set("ArrowDown", dd > 0.25); set("ArrowUp", dd < -0.25); })()`);
      await c.ev(keysUp); await rec(8, 3);
      await c.ev(`(() => { const s = __chonoi.state.scene; if (s.oxy < 12) { __swim(s.p.x, 0, 400, 0.6, true); __run(150); } })()`);
    }
    // off camera: fill the basket for a long Day-1 evening — 7 cá lóc, 4 cá linh, bông súng twice (nodes regrow), bông điên điển
    await c.ev(`(() => { const cnt = (k) => (__chonoi.state.scene.hold || []).filter((x) => x === k).length;
      const live = () => { const s = __chonoi.state.scene; return __chonoi.state.mode === "gather" && s && s.p && !s.result && !s.ended && s.time > 45; };
      try {
        for (const [kind, want] of [["ca_loc", 7], ["ca_linh", 4]]) for (let i = 0; i < 12 && cnt(kind) < want && live(); i++) { const s = __chonoi.state.scene; if (s.oxy < 14) { __swim(s.p.x, 0, 400, 0.6, true); __run(200); } const f = __fish(kind, 20); if (!f) break; __hunt(f, 4); __reel(); __run(10); }
        if (live()) { const s = __chonoi.state.scene; __swim(s.p.x, 0, 400, 0.6, true); __run(100); __flowers(2, "bong_dien_dien"); __flowers(2, "bong_sung"); }
      } catch (e) { console.warn("haul", e); } })()`);
    log("haul state", JSON.stringify(await c.ev(`({ mode: __chonoi.state.mode, t: __chonoi.state.scene.time | 0, oxy: __chonoi.state.scene.oxy | 0, hold: (__chonoi.state.scene.hold || []).join(",") })`)));
    await c.ev(`__swim(__chonoi.state.scene.p.x, 0, 400, 0.6, true); __swim(42, 0, 800, 0.6, true); __run(10)`);
    await rec(12, 3); await c.ev(`__flowers(2)`); await rec(15, 3);
    log("day-1 haul", JSON.stringify(await c.ev(`(__chonoi.state.scene.hold || []).join(",")`)), "time", await c.ev(`__chonoi.state.scene.time | 0`));
    await swimRec(2, 0, 45, 6, true);
    await c.ev(`__swim(2, 0, 3000, 1, true)`);
    begin("dock"); await c.ev(`__press("interact", 2)`); await rec(45, 3); await c.ev(`window.__bot = null`);
    await c.ev(`__until((s) => s.result && s.result.t > 0.8, 400); __press("confirm", 2)`);
    begin("dusk"); await rec(120, 4);
    card("c-quan", "Ngày 1 · Mở quán", "Chọn món, nấu, bưng ra bàn");
    await c.ev(`__until((s, st) => st.mode === "quan" && s.phase === "preopen", 6000); __run(60)`);
    begin("preopen");
    await rec(20, 4, `(() => { const s = __chonoi.state.scene, p = s.p; __key("ArrowUp", p.z < 8.1 ? "keydown" : "keyup"); __key("ArrowLeft", p.x > 6.0 ? "keydown" : "keyup"); __key("ArrowRight", p.x < 5.6 ? "keydown" : "keyup"); })()`);
    await c.ev(`${keysUp}; __walk(5.8, 8.2, 300); __press("interact", 2)`);
    await rec(60, 2);                                                        // menu board pop-up (Đặc sản)
    await c.ev(`__press("back", 10)`);

    // ---- management (real Bà Tư dialog, arrows + E): hire Bé Tí + Chú Bảy, buy & hang new decor. Setup only: wallet 2000k
    card("c-manage", "Thuê người · Trang trí quán", "Bà Tư lo giùm: người phụ, đèn lồng, khăn bàn, giàn bông");
    await c.ev(`__chonoi.progress.save.money = 2000; __chonoi.progress.persist()`);
    const navRec = async (label, hold = 0) => {
      for (let t = 0; t < 30; t++) { const r = await c.ev(`__navGo(${JSON.stringify(label)})`); await rec(3, 2); if (r === "done") break; if (r !== "move") { log("WARN nav", label, r); break; } }
      if (hold) await rec(hold, 2);
    };
    const navBack = async () => { await c.ev(`__chonoi.input.press("back")`); await rec(4, 2); };
    begin("hire");
    await rec(16, 4, `(() => { const s = __chonoi.state.scene, p = s.p; __key("ArrowLeft", p.x > 1.4 ? "keydown" : "keyup"); __key("ArrowUp", p.z < 8.5 ? "keydown" : "keyup"); })()`);
    await c.ev(`${keysUp}; __walk(1.1, 8.7, 300, 0.2); __press("interact", 2)`);
    await rec(24, 2);
    if (!(await c.ev(`!!(__chonoi.state.scene.overlay && __chonoi.state.scene.overlay.nav)`))) log("WARN Bà Tư dialog not open");
    await navRec("Thuê người", 12);
    await navRec("Bé Tí"); await navRec("Thuê", 30);
    await navRec("Chú Bảy"); await navRec("Thuê", 24);
    await still("19-hire-staff-dialog");
    await rec(12, 2);
    log("staff", JSON.stringify(await c.ev(`__chonoi.meta.getStaff()`)));
    await navBack();
    begin("decor");
    await navRec("Trang trí quán", 10);
    for (const [slot, item] of [["Đèn lồng", "Đèn lồng bảy màu"], ["Khăn bàn", "Khăn hoa sen"], ["Bông hoa", "Giàn bông"], ["Bảng hiệu", "Bảng sơn mài"]]) {
      await navRec(slot, 4); await navRec(item, 22); await navBack();
    }
    log("decor", JSON.stringify(await c.ev(`__chonoi.meta.getDecor()`)));
    await navBack(); await navRec("Thôi", 10);
    begin("decorated");
    await rec(20, 3); await still("20-decorated-raft");
    await rec(25, 4, `(() => { const s = __chonoi.state.scene, p = s.p; __key("ArrowDown", p.z > 4.5 ? "keydown" : "keyup"); __key("ArrowRight", p.x < 13.4 ? "keydown" : "keyup"); })()`);
    await c.ev(`["ArrowRight","ArrowDown"].forEach((k) => __key(k, "keyup")); __walk(13.6, 4.2, 300); __press("open", 2)`);
    await rec(12, 2); await c.ev(`__press("confirm", 2)`); await rec(20, 3);  // "Mở quán" confirm → bell
    // ---- the real Day-1 evening on camera: Út Sen + Bé Tí + Chú Bảy, many serves, coins, tips, queue
    await c.ev(`window.__bot = __serveBot; __until((s) => s.customers.some((c) => c.state === "waiting"), 1800)`);
    begin("service");
    let busyShot = false, staffShot = false;
    for (let i = 0; i < 690; i++) {
      if (i > 240 && await c.ev(`!!__chonoi.state.scene.noDish`)) break;    // stop before the "Hết nguyên liệu" banner
      await rec(1, 6);
      if (!staffShot && i % 2 === 0 && await c.ev(`(() => { const s = __chonoi.state.scene, w = s.staff.waiter, k = s.staff.cook; return !!(w && w.carry && k && s.stoves.some((v) => v.state === "cooking") && s.hand); })()`)) { staffShot = true; await still("21-staff-working"); }
      if (!busyShot && i % 3 === 0 && await c.ev(`(() => { const s = __chonoi.state.scene; return s.served >= 4 && s.coins.length > 0 && !s.noDish && s.customers.filter((c) => c.state === "waiting" || c.state === "eating" || c.state === "queue").length >= 4; })()`)) { busyShot = true; await still("14-busy-service"); }
    }
    if (!busyShot) log("WARN 14-busy-service not taken");
    if (!staffShot) log("WARN 21-staff-working not taken");
    await c.ev(`__run(60 * 20); window.__bot = null; __releaseAll(); __run(20)`);
    log("day-1 quán", JSON.stringify(await c.ev(`(() => { const s = __chonoi.state.scene; return { served: s.served, money: s.money, tips: s.tips, noDish: s.noDish, t: s.time | 0 }; })()`)));
    begin("close");
    await rec(10, 3); await c.ev(`__press("close", 4)`); await rec(8, 3); await c.ev(`__press("close", 2)`);
    // the 2nd C ends the shift: the raft's own closing panel first, any key after 0.8 s → DayResult pop-up (mode "result")
    if (await c.ev(`__until((s) => s.result && s.result.t > 0.85, 300)`) < 0) throw new Error("close did not end the shift");
    await rec(25, 3); await c.ev(`__press("confirm", 2)`);
    if (await c.ev(`__until((s, st) => st.mode === "result", 600)`) < 0) throw new Error("DayResult not reached");
    await rec(110, 2);

    // ---- night market: Nâng cấp tab (setup: wallet 3000k so every purchase goes through), then train Chú Bảy, sleep
    card("c-night", "Mua nâng cấp ở chợ đêm", "Bình oxy, áo phao, mũi lao, chân vịt — có hiệu lực từ ngày mai");
    await c.ev(`__press("confirm", 2); __until((s, st) => st.mode === "hub" && s.p, 900); __chonoi.progress.save.money = 3000; __chonoi.progress.persist(); __run(30)`);
    begin("night");
    await rec(50, 4, `(() => { const s = __chonoi.state.scene, p = s.p; __key("ArrowRight", p.x < 14.2 ? "keydown" : "keyup"); })()`);
    await c.ev(`__key("ArrowRight", "keyup"); __walk(14.6, 1.2, 300); __press("interact", 2)`);
    await rec(30, 2);
    if (!(await c.ev(`!!__chonoi.state.scene.menuOpen`))) log("WARN shop pop-up not open");
    const shopRec = async (id, hold) => {
      for (let t = 0; t < 30; t++) { const r = await c.ev(`__shopGo(${JSON.stringify(id)})`); await rec(3, 2); if (r === "done") break; if (r !== "move") { log("WARN shop", id, r); break; } }
      await rec(hold, 2);
    };
    await shopRec("oxygen", 40); await still("22-upgrades-shop");
    await shopRec("hp", 30);
    await shopRec("spear", 26); await shopRec("spear", 14); await shopRec("spear", 26);
    await shopRec("fins", 30);
    log("upgrades", JSON.stringify(await c.ev(`({ cu: __chonoi.progress.save.cu, up: __chonoi.progress.save.up, money: __chonoi.progress.save.money })`)));
    await c.ev(`__chonoi.input.press("back")`); await rec(10, 2);
    begin("train");
    await rec(40, 4, `(() => { const s = __chonoi.state.scene, p = s.p; __key("ArrowLeft", p.x > 2.0 ? "keydown" : "keyup"); })()`);
    await c.ev(`__key("ArrowLeft", "keyup"); __walk(1.4, 1.2, 300, 0.25); __press("interact", 2)`);
    await rec(20, 2);
    await navRec("Thuê người", 8); await navRec("Chú Bảy", 4); await navRec("Đào tạo", 36);
    log("staff", JSON.stringify(await c.ev(`__chonoi.meta.getStaff()`)));
    await navBack(); await navBack(); await navRec("Thôi", 8);
    await rec(30, 4, `(() => { const s = __chonoi.state.scene, p = s.p; __key("ArrowRight", p.x < 6.0 ? "keydown" : "keyup"); })()`);
    await c.ev(`__key("ArrowRight", "keyup"); __walk(6.4, 1.2, 300, 0.25); __press("interact", 2)`);
    await rec(15, 2); await c.ev(`__press("interact", 2)`); await rec(30, 3);       // hammock: E twice

    // ---- Day 2: card (O₂ 45 s) → morning dock → ladder → deeper dive with the upgrades
    card("c-day2", "Ngày 2 · Lặn sâu hơn", "O₂ 45 giây, mũi lao mạnh — xuống 55 m săn cá khổng lồ");
    if (await c.ev(`__until((s, st) => st.mode === "intro", 900)`) < 0) log("WARN Day 2 card not reached");
    begin("day2"); await rec(70, 2);
    await c.ev(`__press("confirm", 2); __until((s, st) => st.mode === "hub" && s.p, 900); __run(20)`);
    begin("dawn");
    await rec(45, 4, `(() => { const s = __chonoi.state.scene, p = s.p; __key("ArrowRight", p.x < 7.8 ? "keydown" : "keyup"); __key("ArrowLeft", p.x > 8.6 ? "keydown" : "keyup"); })()`);
    await c.ev(`${keysUp}; __walk(8.2, 1.2, 300, 0.25); __press("interact", 2)`);
    if (await c.ev(`__until((s, st) => st.mode === "gather" && s.p, 900)`) < 0) log("WARN Day 2 dive not reached");
    // capture-side safety only: the diver never faints on camera (HP ≥ 2, O₂ ≥ 3 s); the 45 s bar and hits stay visible
    await c.ev(`window.__bot = () => { const s = __chonoi.state.scene; if (__chonoi.state.mode === "gather" && s && s.hpMax) { s.hp = Math.max(s.hp, 2); s.oxy = Math.max(s.oxy, 3); } }; __run(150)`);
    log("day-2 dive", JSON.stringify(await c.ev(`(() => { const s = __chonoi.state.scene; return { oxyMax: s.oxyMax, hpMax: s.hpMax, big: s.deep.filter((f) => f.sp.id === "ca_loc_khong_lo").map((f) => [f.x | 0, f.d | 0]), crocs: s.crocs.map((m) => [m.x | 0, m.d | 0, m.hp]) }; })()`)));
    const fight = async (pick, gap, maxF, k, done) => {
      await c.ev(`window.__tgt = (${pick})(__chonoi.state.scene)`);
      for (let i = 0; i < maxF; i++) {
        await rec(1, k, `(() => { const s = __chonoi.state.scene, p = s.p, f = window.__tgt; if (!f) return; const set = (key, on) => __key(key, on ? "keydown" : "keyup");
          const side = p.x <= f.x ? -1 : 1; const dx = f.x + side * ${gap} - p.x, dd = f.d - p.d;
          if (Math.abs(dx) < 1.6 && Math.abs(dd) < 0.9) { set("ArrowUp", false); set("ArrowDown", false); set("ArrowRight", f.x > p.x); set("ArrowLeft", f.x < p.x); set("Shift", false); if (!s.harp) __chonoi.input.press("catch"); return; }
          set("ArrowRight", dx > 0.4); set("ArrowLeft", dx < -0.4); set("ArrowDown", dd > 0.4); set("ArrowUp", dd < -0.4); set("Shift", Math.hypot(dx, dd) > 6); })()`);
        if (await c.ev(`(() => { const f = window.__tgt; return !f || (${done})(f); })()`)) { await c.ev(keysUp); return true; }
      }
      await c.ev(keysUp); return false;
    };
    card("c-dive2", "Vùng sâu 55 m", "Cá lóc khổng lồ ♥8 — và Cá Sấu Năm Chèo ♥24");
    // target: the shallowest big snakehead (cá lóc bông ~36 m or khổng lồ ~55 m) — open water, reachable from above
    await c.ev(`window.__big = __chonoi.state.scene.deep.filter((f) => !f.caught && (f.sp.id === "ca_loc_bong" || f.sp.id === "ca_loc_khong_lo")).sort((a, b) => a.d - b.d || a.x - b.x)[0]`);
    const bigX = await c.ev(`window.__big ? window.__big.x : 40`), bigD = await c.ev(`window.__big ? window.__big.d : 36`);
    await c.ev(`__swim(${bigX} - 6, 0.3, 1500, 1, true); __run(20)`);
    begin("dive2");
    await swimRec(bigX - 6, bigD, 50, 5, true);
    const bigDead = await fight(`() => window.__big`, 4.5, 260, 3,
      `(f) => f.caught || f.hooked`);
    log("big fish", bigDead);
    await rec(30, 3);
    await still("23-day2-deep-dive-upgraded");
    await c.ev(`__reel ? __reel(200) : 0; __swim(__chonoi.state.scene.p.x, 0, 900, 0.8, true); __run(120)`);
    const crX = await c.ev(`(() => { const m = __chonoi.state.scene.crocs.find((m) => m.state !== "dead"); return m ? [m.x, m.d] : null; })()`);
    if (crX) {
      await c.ev(`__swim(${crX[0]} + 10, 0.3, 1500, 1, true); __swim(${crX[0]} + 10, ${crX[1]} - 3, 900, 1, true)`);
      begin("croc2");
      const crocDead = await fight(`(s) => s.crocs.find((m) => m.state !== "dead")`, 5, 320, 3, `(m) => m.state === "dead"`);
      log("croc", crocDead, JSON.stringify(await c.ev(`__chonoi.state.scene.crocs.map((m) => [m.state, m.hp])`)));
      await rec(30, 3);
    }
    await c.ev(`${keysUp}; __swim(__chonoi.state.scene.p.x, 0, 900, 0.8, true); __run(60); __flowers(2, "bong_sung"); __swim(2, 0, 3000, 1, true); __press("interact", 2); __until((s) => s.result && s.result.t > 0.8, 400)`);
    begin("dock2"); await rec(40, 2);
    log("day-2 haul", JSON.stringify(await c.ev(`(__chonoi.state.scene.hold || []).join(",")`)));
    await c.ev(`window.__bot = null; __press("confirm", 2); __until((s, st) => st.mode === "quan" && s.phase === "preopen", 6000); __run(60)`);

    // ---- Day-2 evening: Đặc sản on the board, a sộp guest orders it, Chú Bảy (★★) cooks
    card("c-prem", "Đặc sản đêm nay", "Khách sộp gọi món đặc sản — Chú Bảy ★★ nấu nhanh");
    begin("eve2");
    await c.ev(`__walk(5.8, 8.2, 300); __press("interact", 2)`);
    await rec(55, 2);
    log("menu day 2", JSON.stringify(await c.ev(`Object.keys(__chonoi.state.scene.menu)`)), JSON.stringify(await c.ev(`__chonoi.state.scene.stock`)));
    await c.ev(`__press("back", 10); __walk(13.6, 4.2, 300); __press("open", 6); __press("confirm", 20); window.__bot = __serveBot`);
    const premNow = `(() => { const s = __chonoi.state.scene; return Object.keys(s.sold || {}).filter((k) => s.menu[k] && s.menu[k].premium).reduce((a, k) => a + s.sold[k], 0); })()`;
    let premShot = false;
    for (let i = 0; i < 420; i++) {
      if (i > 150 && await c.ev(`!!__chonoi.state.scene.noDish`)) break;
      await rec(1, 5);
      if (!premShot && await c.ev(`${premNow} > 0 && __chonoi.state.scene.coins.length > 0`)) { premShot = true; await still("24-premium-dish-served"); await rec(45, 3); break; }
    }
    if (!premShot) log("WARN 24-premium-dish-served not taken");
    log("day-2 quán", JSON.stringify(await c.ev(`(() => { const s = __chonoi.state.scene; return { served: s.served, money: s.money, sold: s.sold, cust: s.customers.map((c) => c.type + ":" + c.want + ":" + c.state).join(" ") }; })()`)));
    await c.ev(`window.__bot = null; __releaseAll()`);
    card("c-end", "Quán Ăn Chợ Nổi", "Nhóm 001 · Day 12 AI-SDLC");
  } finally { await c.close(); }
  segs.sort((a, b) => ORDER.indexOf(a.name) - ORDER.indexOf(b.name));
  for (const sg of segs) if (!ORDER.includes(sg.name)) log("WARN segment not in ORDER", sg.name);
  return encode(segs, TMP);
}

// cards are drawn by ffmpeg (drawtext) when available, else rendered as a still by Chrome-free PIL-less fallback: plain colour
function hasDrawtext() { const r = spawnSync(FFMPEG, ["-hide_banner", "-filters"], { encoding: "utf8" }); return /\bdrawtext\b/.test(r.stdout || ""); }
async function cardPng(cardSegs, TMP) {
  // render caption cards with headless Chrome (handles Vietnamese diacritics without ffmpeg drawtext)
  const c = await launch();
  try {
    await c.send("Page.navigate", { url: "about:blank" }); await sleep(300);
    for (const s of cardSegs) {
      s.png = path.join(TMP, `card-${cardSegs.indexOf(s)}.png`);
      await c.ev(`document.documentElement.innerHTML = ${JSON.stringify(`<body style="margin:0;width:100vw;height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;background:radial-gradient(ellipse at 50% 40%,#3a1d4a 0%,#170b22 60%,#0a0612 100%);font-family:'Trebuchet MS',Arial,sans-serif">
        <div style="font-size:64px;font-weight:900;color:#ffd23f;text-shadow:0 5px 0 #3a1410,0 0 30px rgba(255,160,60,.35);letter-spacing:1px">${s.title}</div>
        <div style="margin-top:22px;font-size:28px;font-weight:700;color:#ffe9c4;opacity:.92">${s.sub}</div>
        <div style="margin-top:34px;width:120px;height:4px;border-radius:2px;background:linear-gradient(90deg,#14a6a0,#ff8a3d)"></div></body>`)}; new Promise((r) => setTimeout(r, 150))`);
      await c.shot(s.png);
    }
  } finally { await c.close(); }
}
async function encode(segs, TMP) {
  log("encoding", segs.length, "segments");
  await cardPng(segs.filter((s) => s.kind === "card"), TMP);
  const FPS = 30, XF = 0.35, CARD_S = 1.6; const clips = [];
  for (const [i, s] of segs.entries()) {
    const out = path.join(TMP, `clip-${String(i).padStart(2, "0")}.mp4`);
    const common = ["-r", String(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-vf", "scale=1280:720,setsar=1,scale=out_range=tv,format=yuv420p"];
    if (s.kind === "card") spawnSync(FFMPEG, ["-y", "-loglevel", "error", "-loop", "1", "-t", String(CARD_S), "-i", s.png, ...common, out]);
    else spawnSync(FFMPEG, ["-y", "-loglevel", "error", "-framerate", String(FPS), "-i", path.join(s.dir, "%05d.jpg"), ...common, out]);
    const dur = parseFloat(spawnSync("/opt/homebrew/bin/ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out], { encoding: "utf8" }).stdout);
    if (dur > XF * 2) clips.push({ out, dur });
  }
  // chain xfade cross-fades
  const inputs = clips.flatMap((cl) => ["-i", cl.out]);
  let f = "", prev = "[0:v]", t = clips[0].dur;
  for (let i = 1; i < clips.length; i++) { const lab = `[x${i}]`; f += `${prev}[${i}:v]xfade=transition=fade:duration=${XF}:offset=${(t - XF).toFixed(3)}${lab};`; prev = lab; t += clips[i].dur - XF; }
  f += `${prev}scale=out_range=tv,format=yuv420p[v]`;
  const out = path.join(OUT, "demo.mp4");
  const r = spawnSync(FFMPEG, ["-y", "-loglevel", "error", ...inputs, "-filter_complex", f, "-map", "[v]", "-r", String(FPS), "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", out], { encoding: "utf8" });
  if (r.status !== 0) throw new Error("ffmpeg xfade failed: " + r.stderr);
  fs.rmSync(TMP, { recursive: true, force: true });
  log("video", out, t.toFixed(1) + " s");
  return out;
}

// ---------------------------------------------------------------- main
let server = null, base = baseArg;
if (!base) {
  const port = await freePort();
  server = spawn("python3", ["-m", "http.server", String(port), "--bind", "127.0.0.1"], { cwd: ROOT, stdio: "ignore" });
  base = `http://127.0.0.1:${port}`;
  for (let i = 0; i < 50; i++) { try { if ((await fetch(base + "/client/index.html")).ok) break; } catch { } await sleep(100); }
}
const hardCap = setTimeout(() => { console.error("capture: 30 min cap hit"); server?.kill(); process.exit(2); }, 30 * 60 * 1000);
try {
  fs.mkdirSync(OUT, { recursive: true });
  if (want.stills) await stills(base);
  if (want.video) await video(base);
} finally { clearTimeout(hardCap); server?.kill(); }
