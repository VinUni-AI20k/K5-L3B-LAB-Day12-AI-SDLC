import { W, H, screen, input, fx, clamp, lerp, ease, txt, panel, measure, reduceMotion, setFont } from "./engine.js";
import { unlock, music, sfx, toggleMute, isMuted, registerAudio } from "./audio.js";
import { P, R, portrait, diver, fish, bands, godRays, WATER, kelp, hyacinth, lantern, ghe, chibiSide, KIND_NAME } from "./art.js";
import { riverWorld, introScript, duskScript, dayScript } from "./story.js";
import { Cutscene, slamText, speedLines, halftone } from "./cutscene.js";
import { GatherScene } from "./scene_gather.js";
import { QuanScene } from "./scene_quan.js";
import { ShopScene } from "./scene_shop.js";
import * as progress from "./progress.js";

let CONTRACT = null, MANIFEST = [];
// haul null = demo stock (title-menu shortcut), {} = empty basket (fainted).
// campaign = the saved day loop (day card → morning prep → gather → dusk → evening prep → quán → results);
// false = demo shortcuts (no prep screens, all dishes), never written to the save.
const state = { scene: null, mode: "boot", t: 0, haul: null, menu: null, campaign: false, dayPaid: false };

// ---------- title screen ----------
class Title {
  constructor() {
    this.t = 0; this.sel = 0; this.cam = { x: 0, y: 40 }; this.started = false;
    // [label, action, sub-label, demo?]
    this.items = [];
    this.saved = progress.hasSave() ? progress.load() : null;
    if (this.saved) this.items.push([`Chơi tiếp — Ngày ${this.saved.day}`, "continue", `Ví ${this.saved.money}k · Kỷ lục ${this.saved.best} điểm`]);
    this.items.push(["Chơi mới", "new", this.saved ? "Xoá sổ cũ, bắt đầu lại từ Ngày 1" : "Mở màn rồi vào Ngày 1"]);
    this.items.push(["Buổi sáng — Lặn", "gather", null, true], ["Buổi tối — Quán", "quan", null, true], ["Xem mở màn", "intro", null, true]);
    this.press = 0; this.confirmNew = 0;
    music("theme");
  }
  update(dt) {
    this.t += dt; this.cam.x += dt * 6;
    if (input.hit("up")) { this.sel = (this.sel + this.items.length - 1) % this.items.length; sfx("click"); this.confirmNew = 0; }
    if (input.hit("down")) { this.sel = (this.sel + 1) % this.items.length; sfx("click"); this.confirmNew = 0; }
    if (input.hit("mute")) toggleMute();
    if (this.confirmNew > 0) this.confirmNew -= dt;
    if (!this.leaving && (input.hit("confirm") || input.hit("interact") || input.hit("catch"))) {
      const act = this.items[this.sel][1];
      // overwriting an existing save needs a second press
      if (act === "new" && this.saved && this.confirmNew <= 0) { this.confirmNew = 3; sfx("hurt"); return; }
      sfx("select"); this.press = 0.2; this.leaving = true; go(act);
    }
    if (this.press > 0) this.press -= dt;
  }
  draw() {
    const c = screen.px, t = this.t;
    riverWorld(c, { t, cam: this.cam, v: { school: true, sunUp: 0.4 } }, "dusk");
    // dark gradient for legibility
    const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, "rgba(6,12,28,.2)"); g.addColorStop(1, "rgba(6,12,28,.75)"); c.fillStyle = g; c.fillRect(0, 0, W, H);
    // floating diver mascot
    diver(c, W / 2 + Math.sin(t) * 10, 92 + Math.cos(t * 1.3) * 5, 1, t, 0.4, { tilt: Math.sin(t) * 0.1 });
    for (let i = 0; i < 3; i++) fish(c, i % 2 ? "ca_linh" : "ca_loc", W / 2 - 40 + i * 50 + Math.sin(t + i) * 20, 130 + i * 8, Math.cos(t + i) > 0 ? 1 : -1, t + i);

    // title logo
    const u = screen.ui; const bob = Math.sin(t * 1.5) * 2;
    halftone(c, W / 2 - 120, 30, 240, 44, "rgba(255,180,80,.06)", 6);
    slamText("QUÁN ĂN", W / 2, 42 + bob, 34, { color: "#ffd23f", stroke: "#3a1410", sw: 7, rot: -0.04 });
    slamText("CHỢ NỔI", W / 2, 72 + bob, 38, { color: "#ff8a3d", stroke: "#3a1410", sw: 7, rot: -0.04 });
    txt("Lặn sông · Hái bông · Mở quán", W / 2, 92 + bob, { size: 9, align: "center", color: "#dff4ff", weight: 800, shadow: "rgba(0,0,0,.6)" });

    // menu: main entries (campaign) first, then the demo shortcuts in a smaller, dimmer style
    const main = this.items.filter((it) => !it[3]).length;
    let y = 152 - (main - 1) * 4;
    this.items.forEach(([label0, act, sub, demo], i) => {
      const sel = i === this.sel, size = demo ? 10 : 12;
      if (demo && i === main) { txt("— CHƠI THỬ (không lưu) —", W / 2, y - 1, { size: 7, align: "center", color: "rgba(255,255,255,.42)", weight: 800 }); y += 9; }
      const label = act === "new" && this.confirmNew > 0 && sel ? "Nhấn lần nữa để xoá sổ cũ!" : label0;
      const pulse = sel ? Math.sin(t * 6) * 0.08 + 1 : 1;
      const pw = Math.max(150, measure(label, size, 900) + 50), bh = demo ? 15 : 18;
      if (sel) { panel(W / 2 - pw / 2, y - bh / 2 - 1, pw, bh, { fill: "rgba(255,160,60,.22)", border: act === "new" && this.confirmNew > 0 ? "#ff6b5a" : "#ffd23f", bw: 1.5, r: 8 }); txt("▶", W / 2 - pw / 2 + 12, y + 3, { size: 9, color: "#ffd23f", weight: 900 }); }
      txt(label, W / 2, y + size * 0.35, { size: size * pulse, align: "center", color: sel ? (act === "new" && this.confirmNew > 0 ? "#ffb0a0" : "#fff") : demo ? "rgba(255,255,255,.5)" : "rgba(255,255,255,.75)", weight: 900, shadow: "rgba(0,0,0,.6)" });
      y += demo ? 16 : 20;
    });
    // footer: sub-label of the selected entry, then key hints
    const cur = this.items[this.sel];
    const note = cur[3] ? "Chơi thử: dùng đồ nghề hiện có, không tính ngày, không lưu tiến trình" : cur[2] || "";
    if (note) txt(note, W / 2, H - 26, { size: 7.5, align: "center", color: cur[3] ? "rgba(255,255,255,.55)" : "#ffe2a8", weight: 700, shadow: "rgba(0,0,0,.6)" });
    txt("↑↓ chọn · Enter/Space chơi · M tắt tiếng", W / 2, H - 15, { size: 8, align: "center", color: "rgba(255,255,255,.6)", weight: 700 });
    txt(isMuted() ? "🔇" : "🔊", W - 12, 14, { size: 10, align: "right" });
    txt("Nhóm 001 · Day 12 AI-SDLC · GUI dựng trước, luật ráp sau", W / 2, H - 5, { size: 6.5, align: "center", color: "rgba(255,255,255,.4)", weight: 700 });
    if (this.press > 0) { c.fillStyle = `rgba(255,255,255,${this.press})`; c.fillRect(0, 0, W, H); }
  }
}

// ---------- scene transitions ----------
let wipe = null;
function transition(next, kind = "iris") { wipe = { k: 0, phase: "in", next, kind }; }

// where: "continue" | "new" ("play" = old alias) | "gather" | "quan" | "intro"
//        debug only: "shop" (reopen last results) | "morning" | "evening" (prep screens on the real save)
function go(where) {
  if (where === "continue") { campaign(); progress.resume(); transition(startDay); }
  else if (where === "new" || where === "play") {
    campaign(); progress.newGame();
    transition(() => { state.mode = "cut"; state.scene = new Cutscene(introScript(), startDay); });
  } else if (where === "intro") {
    demo(); transition(() => { state.mode = "cut"; state.scene = new Cutscene(introScript(), toTitle); });
  } else if (where === "gather") { demo(); transition(startGather); }
  else if (where === "quan") { demo(); state.haul = null; state.menu = null; transition(() => startQuan(null)); }
  else if (where === "morning") { campaign(); transition(startMorning); }
  else if (where === "evening") { campaign(); state.haul = state.haul || {}; transition(startEvening); }
  else if (where === "shop") {
    campaign(); const h = progress.save.history.at(-1);
    transition(() => startShop(h ? { ...h, prevBest: progress.save.best, newBest: false } : { day: progress.save.day - 1, haulCount: 0, earned: 0, rep: 0, served: 0, left: 0, score: 0 }));
  }
}
function campaign() { progress.setDemo(false); state.campaign = true; }
function demo() { progress.setDemo(true); state.campaign = false; }

// one campaign day: NGÀY N card → Chuẩn bị lặn → gather → dusk → Chuẩn bị mở quán → quán → finishDay → Kết sổ → next day
function startDay() {
  const s = progress.save, ups = Object.values(s.up).reduce((a, b) => a + b, 0);
  state.mode = "cut"; state.haul = {}; state.menu = null; state.dayPaid = false;
  const sub = s.day === 1 && !s.history.length ? "Ngày đầu mở lại quán · lặn kiếm nguyên liệu" : `Ví ${s.money}k · ${ups} nâng cấp · lặn kiếm nguyên liệu`;
  state.scene = new Cutscene(dayScript(s.day, sub), startMorning);
}
function startMorning() { state.mode = "prep"; state.scene = new ShopScene(CONTRACT, null, () => transition(startGather), { mode: "morning" }); }
function startEvening() {
  state.mode = "prep";
  state.scene = new ShopScene(CONTRACT, null, (sel) => { state.menu = sel?.menu || null; transition(() => startQuan(state.haul, state.menu)); }, { mode: "evening", stock: state.haul || {} });
}
function startGather() { state.mode = "gather"; state.scene = new GatherScene(CONTRACT, onGatherEnd); }
function onGatherEnd(res) {
  if (res.restart) return transition(startGather);
  state.haul = res.by || {};
  // campaign: dusk → evening prep (menu + restaurant shop); demo: dusk → quán with every dish
  transition(() => { state.mode = "cut"; state.scene = new Cutscene(duskScript(flat(state.haul)), () => state.campaign ? startEvening() : startQuan(state.haul)); });
}
// opts.menu = dish ids allowed tonight (scene_quan.js 4th arg; omitted = all dishes)
function startQuan(stock, menu = null) { state.mode = "quan"; state.scene = new QuanScene(CONTRACT, stock, onQuanEnd, menu ? { menu } : undefined); }
function onQuanEnd(res) {
  // R on the result screen replays the evening with the same stock; the day is only paid once, below
  if (res.restart) return transition(() => startQuan(state.haul, state.menu));
  if (!state.campaign || state.dayPaid) return transition(toTitle);
  state.dayPaid = true;
  const day = progress.save.day, prevBest = progress.save.best;
  const summary = { haulCount: flat(state.haul || {}).length, earned: res.money ?? 0, rep: res.rep, served: res.served ?? 0, left: res.left ?? 0, score: res.score };
  progress.finishDay(summary);
  transition(() => startShop({ ...summary, day, prevBest, newBest: (res.score || 0) > prevBest }));
}
function startShop(summary) { state.mode = "results"; state.scene = new ShopScene(CONTRACT, summary, () => transition(startDay), { mode: "results" }); }
function toTitle() { progress.setDemo(false); state.campaign = false; state.mode = "title"; state.scene = new Title(); }
function flat(by) { const a = []; for (const k in by) for (let i = 0; i < by[k]; i++) a.push(k); return a; }

// ---------- transition draw ----------
function drawWipe(dt) {
  if (!wipe) return;
  const c = screen.px;
  wipe.k += dt * 2.6;
  if (wipe.phase === "in" && wipe.k >= 1) { wipe.next(); wipe.phase = "out"; wipe.k = 0; }
  if (wipe.phase === "out" && wipe.k >= 1) { wipe = null; return; }
  const closing = wipe.phase === "in";
  const k = closing ? wipe.k : 1 - wipe.k;
  c.save();
  if (wipe.kind === "iris") {
    const r = (1 - ease.inOut(k)) * Math.hypot(W, H) * 0.6;
    c.fillStyle = "#070b1a"; c.beginPath(); c.rect(0, 0, W, H); c.arc(W / 2, H / 2, r, 0, Math.PI * 2, true); c.fill("evenodd");
  } else { c.fillStyle = "#070b1a"; c.globalAlpha = ease.inOut(k); c.fillRect(0, 0, W, H); }
  c.restore();
}

// ---------- boot + loop ----------
const FALLBACK_CONTRACT = { tuning: {
  tick_hz: 60,
  gather: { duration_s: 180, bounds: { x: [0, 100], d: [0, 30] }, dock_pos: [2, 0], dock_radius: 3, start_pos: [2, 0], swim_speed: 4, surface_depth: 0.5, oxygen_max_s: 30, oxygen_refill_per_tick: 6, choke_interval_ticks: 60, hp_max: 3, hold_capacity: 12, interact_radius: 2, node_yield: 1, regrow_s: 20, catch_radius: 2, catch_cooldown_s: 0.5, fish_yield: { ca_linh: 3, ca_loc: 1 },
    nodes: [{ id: "N1", kind: "bong_dien_dien", pos: [12, 0] }, { id: "N2", kind: "bong_dien_dien", pos: [28, 0] }, { id: "N3", kind: "bong_sung", pos: [44, 0] }, { id: "N4", kind: "bong_sung", pos: [60, 0] }],
    fish_initial: [{ id: "F1", kind: "ca_linh", pos: [15, 5] }, { id: "F2", kind: "ca_loc", pos: [30, 10] }, { id: "F3", kind: "ca_linh", pos: [45, 10] }, { id: "F4", kind: "ca_loc", pos: [60, 16] }, { id: "F5", kind: "ca_linh", pos: [75, 5] }, { id: "F6", kind: "ca_loc", pos: [90, 16] }] },
  quan: { duration_s: 180, bounds: { x: [0, 16], z: [0, 10] }, start_pos: [8, 5], walk_speed: 4, interact_radius: 1.5, stoves: [{ id: "B1", pos: [2, 8] }], tables: [{ id: "T1", pos: [9, 2] }], first_customer_tick: 120, customer_interval_s: 15, patience_s: 60, eat_s: 10, carry_limit: 1, tip_rate: 0.2, tip_min_patience_ratio: 0.5, tip_reputation: 0.2, left_reputation_delta: -0.5, reputation_initial: 3, reputation_min: 0, reputation_max: 5 },
  menu: { ca_loc_nuong_trui: { recipe: { ca_loc: 1 }, cook_s: 6, price: 60 }, goi_bong_sung: { recipe: { bong_sung: 2 }, cook_s: 4, price: 40 }, lau_ca_linh_dien_dien: { recipe: { ca_linh: 3, bong_dien_dien: 1 }, cook_s: 10, price: 120 } },
  score: { reputation_multiplier: 100 },
} };

async function boot() {
  screen.init();
  try {
    const r = await fetch("../game.contract.json", { cache: "no-store" });
    CONTRACT = r.ok ? await r.json() : FALLBACK_CONTRACT;
  } catch (e) { CONTRACT = FALLBACK_CONTRACT; }
  if (!CONTRACT.tuning) CONTRACT = FALLBACK_CONTRACT;
  try {
    const r = await fetch("assets/manifest.json", { cache: "no-store" });
    if (r.ok) { MANIFEST = normalizeManifest(await r.json()); registerAudio(MANIFEST); const f = MANIFEST.find((a) => a.kind === "font"); if (f && f.family) await loadFont(f); }
  } catch (e) { /* no assets yet: procedural art + synth sfx still work */ }
  state.mode = "title"; state.scene = new Title();
  if (/[?&]debug\b/.test(location.search)) window.__chonoi = { state, manifest: MANIFEST, go, step, input, progress };
  // first input unlocks audio
  const kick = () => { unlock(); removeEventListener("keydown", kick); removeEventListener("pointerdown", kick); };
  addEventListener("keydown", kick); addEventListener("pointerdown", kick);
  document.getElementById("loading")?.remove();
  requestAnimationFrame(loop);
}
// manifest.json is { note, assets:[{path, kind, ...}] } without ids: id = file name, plus aliases for the
// names the game asks for (music "theme", synth-only sfx) so the sourced files actually play.
const ALIAS = { title: "theme", jingle_success: "fanfare", pop: "pick", stove_on: "sizzle", impact: "slam" };
function normalizeManifest(raw) {
  const list = (Array.isArray(raw) ? raw : raw?.assets || []).filter((a) => a && a.path);
  const out = list.map((a) => ({ ...a, id: a.id || a.path.split("/").pop().replace(/\.[^.]+$/, "") }));
  for (const a of [...out]) if (ALIAS[a.id] && !out.some((b) => b.kind === a.kind && b.id === ALIAS[a.id])) out.push({ ...a, id: ALIAS[a.id] });
  return out;
}
async function loadFont(f) {
  try { const face = new FontFace(f.family, `url(assets/${f.path})`); await face.load(); document.fonts.add(face); setFont(f.family); } catch (e) {}
}

let last = 0;
function loop(ts) {
  requestAnimationFrame(loop);
  const now = ts / 1000; const dt = now - (last || now); last = now;
  frame(Math.min(dt, 0.05));
}
// ?debug only: advance n frames synchronously (tests don't depend on rAF, which stalls in hidden tabs)
function step(n = 1, dt = 1 / 60) { for (let i = 0; i < n; i++) frame(dt); }
function frame(dt) {
  if (fx.stop > 0) { fx.stop -= dt; dt *= 0.08; }
  fx.update(dt);

  // update: scene runs except while the wipe is closing over it
  if (!wipe || wipe.phase === "out") state.scene?.update(dt);

  // draw with screen shake
  const px = screen.px;
  px.setTransform(1, 0, 0, 1, 0, 0);
  px.imageSmoothingEnabled = false;
  const [sx, sy] = fx.offset();
  px.save(); px.translate(sx, sy);
  screen.beginUI();
  state.scene?.draw();
  if (fx.flashT > 0) { px.globalAlpha = (fx.flashT / 0.2) * 0.6; px.fillStyle = fx.flashCol; px.fillRect(-8, -8, W + 16, H + 16); px.globalAlpha = 1; }
  drawWipe(dt);
  px.restore();

  input.endFrame();
}

boot();
