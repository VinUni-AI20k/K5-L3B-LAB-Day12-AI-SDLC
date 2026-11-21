// QUÁN scene — GUI ONLY. Local mock; swap `st` for the server snapshot later.
// Side view of a floating restaurant raft (nhà bè) at night, seen from the river.
// Gameplay still lives in contract units: x in [0,16] runs left→right along the deck, z in [0,10] is depth
// (z = 0 front edge, z = 10 back rail). Screen: sx = X0 + x·XS, sy = Y0 − z·ZS (back rows higher and smaller).
import { W, H, screen, input, clamp, lerp, fx, Particles, txt, panel, measure } from "./engine.js";
import { sfx, music, voiceLine } from "./audio.js";
import { P, R, ripple, dishIcon, icon, DISH_NAME, KIND_NAME } from "./art.js";
import { speedLines } from "./cutscene.js";
const dishName = (k) => DISH_NAME[k] || k;
import { riverWorld } from "./story.js";
import { save, stats } from "./progress.js";
import { scaled, personSide, stool, sideTable, clayStove, passCounter, kitchenBack, roofAndPosts, lanternString, glow,
  nightWater, deck, backRail, landing, sampan, steam, smoke, coin, moon } from "./raft.js";

const TAU = Math.PI * 2;

// Customer types (GUI-only "Sáng tạo của nhóm"; the headless sim knows one customer kind).
// Multipliers apply on top of contract numbers (tuning.quan / tuning.menu), never replace them.
//   patMul   × patience_s            priceMul × menu price (floored)
//   tipMul   × floor(price×tip_rate) leaveMul × left_reputation_delta
export const CUST_TYPES = {
  quen: { name: "Khách quen", badge: "Quen", col: "#9fd8ff", bubble: "#ffffff", patMul: 1,   priceMul: 1,   tipMul: 1, leaveMul: 1, priciest: false },
  voi:  { name: "Khách vội",  badge: "Vội",  col: "#ff9a5a", bubble: "#ffe2cf", patMul: 0.6, priceMul: 1,   tipMul: 1, leaveMul: 1, priciest: false },
  sop:  { name: "Khách sộp",  badge: "Sộp",  col: "#ffd23a", bubble: "#fff1b8", patMul: 1,   priceMul: 1.5, tipMul: 2, leaveMul: 2, priciest: true },
};
// Spawn weights by day: day 1 = 60/25/15; each later day moves 3% to "vội" and 2% to "sộp", capped at day 7 (30/43/27).
export function customerWeights(day = 1) {
  const d = clamp((day | 0) - 1, 0, 6);
  const voi = 0.25 + 0.03 * d, sop = 0.15 + 0.02 * d;
  return { quen: 1 - voi - sop, voi, sop };
}
function pickType(day) {
  const w = customerWeights(day); let r = Math.random();
  for (const k of Object.keys(w)) { if ((r -= w[k]) < 0) return k; }
  return "quen";
}
const SHIRTS = { quen: ["#3a6fd8", "#2a8f5a", "#7a5aa8"], voi: ["#e8572a"], sop: ["#f3c454"] };
const HAIRS = { quen: "#2a1d2b", voi: "#3a2418", sop: "#5a2a1a" };
const fmtS = (s) => (Number.isInteger(s) ? s : s.toFixed(1)) + "s";

// screen mapping (see header) + set dressing positions, all in contract units
const X0 = 34, XS = 24, Y0 = 238, ZS = 6;
const DECK_L = 12, DECK_R = 436, Y_BACK = 172, Y_FRONT = 244, HORIZON = 118;
const DOCK = { x: 16.6, z: 4 }, BOAT_X = 17.6, SEAT_DX = 0.8, WALK = 4.5;
const BA_TU = { x: 1.1, z: 9.2 }, PASS = { x: 3.6, z: 8.4 };
const depthScale = (z) => Math.round((1 - clamp(z, 0, 10) * 0.02) * 16) / 16;
// warm-wood HUD palette
const HUD = { fill: "rgba(42,24,14,.88)", border: "#e8b04a", dim: "#7a5232", text: "#ffe9c4" };

// tiny pixel icons (drawn with R on either canvas layer; ~5×6 world px)
function pixIcon(c, kind, x, y) {
  if (kind === "voi") { // stopwatch
    R(c, x + 2, y, 1, 1, "#cfd8e0"); R(c, x + 1, y + 1, 3, 1, "#fff"); R(c, x, y + 2, 5, 3, "#fff"); R(c, x + 1, y + 5, 3, 1, "#fff");
    R(c, x + 2, y + 2, 1, 2, "#d94a3d"); R(c, x + 3, y + 3, 1, 1, "#d94a3d");
  } else if (kind === "sop") { // coin
    R(c, x + 1, y, 3, 1, "#e0a21a"); R(c, x, y + 1, 5, 4, "#ffd23a"); R(c, x + 1, y + 5, 3, 1, "#e0a21a"); R(c, x + 2, y + 1, 1, 4, "#e0a21a");
  } else { // heart
    R(c, x, y + 1, 2, 2, "#ff8fb1"); R(c, x + 3, y + 1, 2, 2, "#ff8fb1"); R(c, x + 1, y + 2, 3, 2, "#ff8fb1"); R(c, x + 2, y + 4, 1, 1, "#ff8fb1");
  }
}

export class QuanScene {
  // opts.menu: array of dish ids allowed tonight (default: every contract dish)
  constructor(contract, stock, onEnd, opts = {}) {
    this.t = contract.tuning.quan; this.onEnd = onEnd;
    const t = this.t, all = contract.tuning.menu;
    const allowed = Array.isArray(opts && opts.menu) ? opts.menu.filter((k) => all[k]) : Object.keys(all);
    this.menu = Object.fromEntries(allowed.map((k) => [k, all[k]]));
    this.p = { x: t.start_pos[0], z: t.start_pos[1], vx: 0, vz: 0, face: 1, walk: 0 };
    this.stock = stock ? { ...stock } : { ca_loc: 3, ca_linh: 6, bong_sung: 4, bong_dien_dien: 3, ca_keo: 4, keo_neo: 1 }; // null = demo stock; {} = empty basket
    this.stoves = t.stoves.map((s) => ({ ...s, state: "idle", dish: null, cook: 0, cookMax: 0, pop: 0 }));
    // meta progression: stove upgrade multiplies cook time, décor multiplies patience, extra tables; day shifts the customer mix
    let st = null; try { st = stats(contract); } catch (e) {}
    this.cookMul = st && st.cookMul > 0 ? st.cookMul : 1;
    this.basePatience = st && st.patienceS > 0 ? st.patienceS : t.patience_s;
    this.patMul = st && st.patienceMul > 0 ? st.patienceMul : 1;
    const base = t.tables.map((tb) => ({ ...tb, pos: [...tb.pos] }));
    const n = Math.max(1, st && st.tables > 0 ? st.tables | 0 : base.length);
    for (let i = base.length; i < n; i++) base.push({ id: "T" + (i + 1), pos: [clamp(9 + 3 * i, t.bounds.x[0] + 1, t.bounds.x[1] - 1), i % 2 ? 5 : 2] });
    this.tables = base.slice(0, n);
    this.hand = null; this.customers = []; this.time = t.duration_s;
    // opts.rep: reputation carried over from the previous day (v1.1 day loop); tips / sold feed DayResult + Summary
    this.money = 0; this.rep = typeof opts?.rep === "number" ? opts.rep : t.reputation_initial; this.score = 0; this.rep0 = this.rep;
    this.tips = 0; this.sold = {};
    // early close (C twice, the HUD button, or the pause menu); clickable HUD button via its own pointer listener
    this.confirmClose = 0; this.noDish = false; this.noDishSaid = false;
    this.closeBtn = { x: W - 92, y: H - 30, w: 86, h: 15 };
    this._onMove = (e) => {
      if (this.ended || this.menuOpen || !screen.pc?.getBoundingClientRect) return;
      const r = screen.pc.getBoundingClientRect(), mx = (e.clientX - r.left) / r.width * W, my = (e.clientY - r.top) / r.height * H, b = this.closeBtn;
      if (mx >= b.x && mx <= b.x + b.w && my >= b.y && my <= b.y + b.h) this.requestClose();
    };
    addEventListener("pointerdown", this._onMove);
    this.nextCust = t.first_customer_tick / 60; this.custSeq = 0; this.time0 = t.duration_s;
    this.cam = { x: t.bounds.x[1] / 2, z: t.bounds.z[1] / 2 };
    this.ps = new Particles(); this.toasts = []; this.ended = false; this.result = null;
    this.menuOpen = false; this.menuSel = 0; this.hintT = 4; this.started = false; this.repFlash = 0;
    this.day = (save && save.day) || 1;
    this.served = 0; this.left = 0;
    this.nextType = null; // ?debug: set to "quen" | "voi" | "sop" to force the next customer's type
    // visual-only actors (never read by gameplay): customers walking back to the boats, sampans leaving, coins flying
    this.walkers = []; this.boats = []; this.coins = []; this.sparkT = 0; this.bob = 0;
    this.cs = { t: 0, cam: { x: 0, y: -HORIZON }, v: {} };
    music("restaurant");
  }
  cookTime(key) { return this.menu[key].cook_s * this.cookMul; }
  toast(x, z, txt, col) { this.toasts.push({ x, z, txt, col, life: 1.5, oy: 0 }); }
  // Ingredient reservation (contract §1.3): `stock` holds AVAILABLE amounts; a guest's order moves its recipe into
  // cu.reserved. Cooking a dish uses the oldest waiting order's reservation for that dish, else free stock.
  freeOK(key) { const r = this.menu[key].recipe; return Object.entries(r).every(([k, n]) => (this.stock[k] || 0) >= n); }
  resFor(key) { return this.customers.filter((c) => c.state === "waiting" && c.want === key && c.reserved).sort((a, b) => a.orderT - b.orderT || (a.table < b.table ? -1 : 1))[0] || null; }
  canCook(key) { return !!this.resFor(key) || this.freeOK(key); }
  release(cu) { if (!cu.reserved) return; for (const [k, n] of Object.entries(cu.reserved)) this.stock[k] = (this.stock[k] || 0) + n; cu.reserved = null; }
  reservedTotals() { const o = {}; for (const c of this.customers) if (c.reserved) for (const [k, n] of Object.entries(c.reserved)) o[k] = (o[k] || 0) + n; return o; }

  spawnCustomer() {
    // rotate through the tables, skipping occupied ones (one table = the contract's behaviour)
    let tb = null;
    for (let k = 0; k < this.tables.length; k++) { const c = this.tables[(this.custSeq + k) % this.tables.length]; if (!this.customers.some((cu) => cu.table === c.id)) { tb = c; break; } }
    if (!tb) return;
    const keys = Object.keys(this.menu).filter((k) => this.freeOK(k));
    if (!keys.length) return; // no_dish: the HUD banner explains it (see update / drawHUD)
    // first customer of a shift is always a regular (gentle start); later ones follow the day's weights
    const type = this.nextType && CUST_TYPES[this.nextType] ? this.nextType : this.custSeq === 0 ? "quen" : pickType(this.day);
    this.nextType = null;
    const ty = CUST_TYPES[type];
    const want = ty.priciest
      ? keys.reduce((a, k) => (this.menu[k].price > this.menu[a].price ? k : a), keys[0])
      : keys[Math.floor(Math.random() * keys.length)];
    const patMax = this.basePatience * ty.patMul * this.patMul, seq = ++this.custSeq, shirts = SHIRTS[type];
    const reserved = { ...this.menu[want].recipe };
    for (const [k, n] of Object.entries(reserved)) this.stock[k] -= n;
    this.customers.push({ id: "C" + seq, table: tb.id, x: tb.pos[0], z: tb.pos[1], want, type, reserved, orderT: this.time0 - this.time, state: "waiting", patience: patMax, patienceMax: patMax, eat: 0, enter: 0, portrait: "khach",
      shirt: shirts[seq % shirts.length], hair: HAIRS[type], hat: type === "quen" && seq % 2 === 0,
      // visual: arrives by sampan at the right edge, hops onto the deck, walks to the stool and sits facing the kitchen
      vis: { phase: "boat", k: 0, x: BOAT_X + 4, z: DOCK.z, walk: 0, face: -1 } });
    sfx("ding"); this.toast(tb.pos[0], tb.pos[1] + 1, ty.name + " tới!", ty.col);
    if (type === "sop") sfx("coin");
  }
  payFor(cu) { return Math.floor(this.menu[cu.want].price * CUST_TYPES[cu.type || "quen"].priceMul); }

  nearStove() { return this.stoves.find((s) => Math.hypot(s.pos[0] - this.p.x, s.pos[1] - this.p.z) <= this.t.interact_radius); }
  nearTable() { const tb = this.tables.find((t) => Math.hypot(t.pos[0] - this.p.x, t.pos[1] - this.p.z) <= this.t.interact_radius); return tb ? this.customers.find((c) => c.table === tb.id) : null; }

  interact() {
    if (this.hand) { // serving
      // back at the stove with a dish nobody wants: throw it out, so the cook is never stuck (carry_limit 1)
      const st = this.nearStove();
      if (st) { this.toast(st.pos[0], st.pos[1] + 1, "Đổ " + dishName(this.hand.key), "#ff8a8a"); this.hand = null; sfx("whoosh"); return; }
      const cu = this.nearTable();
      if (cu && cu.state === "waiting" && cu.want === this.hand.key) this.serve(cu);
      else if (cu && cu.state === "waiting") { this.toast(cu.x, cu.z + 1, "Sai món! (E ở bếp để đổ)", "#ff6b6b"); sfx("hurt"); }
      else this.toast(this.p.x, this.p.z + 1, "Không có khách ở đây", "#ffd23a");
      return;
    }
    const s = this.nearStove();
    if (s) {
      if (s.state === "ready") { const dish = s.dish; this.hand = { key: dish }; s.state = "idle"; s.dish = null; sfx("pick"); this.toast(s.pos[0], s.pos[1] + 1, "Bưng " + dishName(dish), "#9fe"); }
      else if (s.state === "idle") { this.menuOpen = true; this.menuSel = 0; sfx("select"); }
      else this.toast(s.pos[0], s.pos[1] + 1, "Đang nấu...", "#ffd23a");
    }
  }
  cook(key) {
    const s = this.nearStove(); if (!s || s.state !== "idle" || !this.menu[key]) return;
    if (!this.canCook(key)) { this.toast(s.pos[0], s.pos[1] + 1, "Thiếu nguyên liệu", "#ff6b6b"); sfx("hurt"); return; }
    const owner = this.resFor(key);
    if (owner) owner.reserved = null; // the oldest order's reserved ingredients go into the pot
    else for (const [k, n] of Object.entries(this.menu[key].recipe)) this.stock[k] -= n;
    s.state = "cooking"; s.dish = key; s.cookMax = this.cookTime(key); s.cook = s.cookMax;
    sfx("sizzle"); this.menuOpen = false;
    this.toast(s.pos[0], s.pos[1] + 1, "Bắc bếp!", "#ff8a3d");
  }
  serve(cu) {
    const dish = this.menu[cu.want], ty = CUST_TYPES[cu.type || "quen"];
    const ratio = cu.patience / (cu.patienceMax || this.t.patience_s);
    const tip = ratio >= this.t.tip_min_patience_ratio ? Math.floor(dish.price * this.t.tip_rate) * ty.tipMul : 0;
    const gain = this.payFor(cu) + tip;
    this.release(cu);
    this.money += gain; this.tips += tip; this.sold[cu.want] = (this.sold[cu.want] || 0) + 1; this.hand = null; cu.state = "eating"; cu.eat = this.t.eat_s; this.served++;
    this.rep = clamp(this.rep + (tip ? this.t.tip_reputation : 0), this.t.reputation_min, this.t.reputation_max);
    this.repFlash = 0.5;
    sfx("coin"); if (tip) sfx("ding"); fx.flash("rgba(255,220,120,.2)", 0.12);
    this.toast(cu.x, cu.z + 1.2, `+${gain}k${tip ? " 🪙" : ""}`, "#ffe14d");
    const sx = this._sx(cu.x), sy = this._sy(cu.z) - 18;
    for (let i = 0; i < 10; i++) this.ps.add({ x: sx, y: sy, vx: (Math.random() - .5) * 40, vy: -20 - Math.random() * 30, g: 90, size: 1 + (i % 2), life: 0.7, color: i % 2 ? "#ffd23a" : "#fff0a8" });
    const nCoins = 3 + (tip ? 2 : 0) + (cu.type === "sop" ? 2 : 0);
    for (let i = 0; i < nCoins; i++) this.coins.push({ x0: sx + (i - nCoins / 2) * 4, y0: sy, vx: (i - nCoins / 2) * 14, t: -i * 0.05 });
  }
  leave(cu) {
    const delta = this.t.left_reputation_delta * CUST_TYPES[cu.type || "quen"].leaveMul;
    this.release(cu); cu.state = "gone"; this.left++; this.rep = clamp(this.rep + delta, this.t.reputation_min, this.t.reputation_max);
    this.repFlash = 0.5; sfx("hurt"); fx.shake(cu.type === "sop" ? 5 : 3, 0.3);
    this.toast(cu.x, cu.z + 1, "Bỏ đi 😠 " + delta + " uy tín", "#ff6b6b");
    this.depart(cu, true);
  }
  // visual only: the customer stands up and walks back to a sampan at the right edge
  depart(cu, angry) {
    const v = cu.vis || { x: cu.x + SEAT_DX, z: cu.z };
    if (v.phase === "boat") { this.boats.push({ x: v.x, z: DOCK.z, vx: 1, who: cu, angry }); return; }
    this.walkers.push({ x: v.x, z: v.z, who: cu, angry, walk: 0, leg: 0 });
  }

  // C / HUD button: the first press asks for confirmation, a second within 3 s closes
  requestClose() {
    if (this.ended) return;
    if (this.confirmClose > 0) return this.closeEarly();
    this.confirmClose = 3; sfx("click");
  }
  // contract closing rule: eating guests have already paid (payment happens at serve), waiting guests leave
  // without reputation loss (their reservations are released), dishes on stoves / in hand are cleared.
  closeShop() {
    for (const cu of this.customers) {
      if (cu.state === "waiting") { this.release(cu); cu.state = "gone"; this.depart(cu, false); }
      else if (cu.state === "eating") { cu.state = "done"; this.depart(cu, false); }
    }
    for (const st of this.stoves) { st.state = "idle"; st.dish = null; st.cook = 0; }
    this.hand = null; this.menuOpen = false;
  }
  closeEarly() { if (this.ended) return; this.closedEarly = true; sfx("whoosh"); this.endRun(); }
  endRun() {
    if (this.ended) return; this.ended = true;
    removeEventListener("pointerdown", this._onMove);
    this.closeShop();
    this.score = this.money + 100 * Math.floor(this.rep);
    this.result = { money: this.money, rep: this.rep, score: this.score, t: 0, stars: Math.floor(this.rep), served: this.served, left: this.left, day: this.day, tips: this.tips, sold: { ...this.sold }, rep0: this.rep0, closedEarly: !!this.closedEarly };
    music("theme"); sfx("fanfare");
  }

  update(dt) {
    this.ps.update(dt);
    this.toasts.forEach((t) => { t.life -= dt; t.oy -= dt * 16; }); this.toasts = this.toasts.filter((t) => t.life > 0);
    if (this.repFlash > 0) this.repFlash -= dt;
    this.updateActors(dt);
    if (this.result) { this.result.t += dt; if (input.hit("restart")) this.onEnd({ restart: true }); else if (this.result.t > 0.8 && input.any()) this.onEnd(this.result); return; }

    if (this.menuOpen) { this.updateMenu(); return; }
    const t = this.t, p = this.p;
    let [mx, mz] = input.axis(); mz = -mz; // up key = toward the back rail (+z)
    if (mx || mz) { const n = Math.hypot(mx, mz) || 1; mx /= n; mz /= n; this.started = true; this.hintT = 0; }
    p.vx = lerp(p.vx, mx * t.walk_speed, 0.25); p.vz = lerp(p.vz, mz * t.walk_speed, 0.25);
    p.x = clamp(p.x + p.vx * dt, 0.5, t.bounds.x[1] - 0.5);
    p.z = clamp(p.z + p.vz * dt, 0.5, t.bounds.z[1] - 0.5);
    if (Math.abs(mx) > 0.01) p.face = mx > 0 ? 1 : -1;
    p.walk = (mx || mz) ? p.walk + dt : 0;

    if (input.hit("interact")) this.interact();
    if (input.hit("restart")) this.onEnd({ restart: true });
    if (input.hit("close")) { this.requestClose(); if (this.ended) return; }
    if (this.confirmClose > 0) this.confirmClose -= dt;
    // no dish can be made for a NEW guest any more -> persistent banner + one short voice line
    this.noDish = !Object.keys(this.menu).some((k) => this.freeOK(k));
    if (this.noDish && !this.noDishSaid) { this.noDishSaid = true; try { voiceLine("sen", "Hết nguyên liệu rồi Má ơi! Đóng quán sớm nghen?"); } catch (e) {} }

    // stoves
    for (const s of this.stoves) { if (s.state === "cooking") { s.cook -= dt; if (s.cook <= 0) { s.state = "ready"; s.pop = 0.4; sfx("ding"); this.toast(s.pos[0], s.pos[1] + 1, "Chín rồi!", "#79c75a"); } } if (s.pop > 0) s.pop -= dt; }
    // customers
    this.nextCust -= dt;
    if (this.nextCust <= 0 && this.customers.filter((c) => c.state === "waiting").length < this.tables.length) { this.spawnCustomer(); this.nextCust = t.customer_interval_s; }
    for (const cu of this.customers) {
      if (cu.enter < 1) cu.enter = Math.min(1, cu.enter + dt * 2);
      if (cu.state === "waiting") { cu.patience -= dt; if (cu.patience <= 0) this.leave(cu); }
      else if (cu.state === "eating") { cu.eat -= dt; if (cu.eat <= 0) { cu.state = "done"; this.toast(cu.x, cu.z + 1, "Ngon! 😋", "#79c75a"); this.depart(cu, false); } }
    }
    this.customers = this.customers.filter((c) => (c.state !== "gone" && c.state !== "done") || (c.fade = (c.fade || 1) - dt) > 0);

    this.time -= dt;
    this.score = this.money + 100 * Math.floor(this.rep);
    if (this.time <= 0) { this.time = 0; this.endRun(); }
    if (this.hintT > 0) this.hintT -= dt;
  }
  // visual-only motion: arrivals, walkers, boats, coins, sizzle sparks (no gameplay state)
  updateActors(dt) {
    for (const cu of this.customers) {
      const v = cu.vis; if (!v || cu.state === "gone" || cu.state === "done") continue;
      if (v.phase === "boat") { v.k = Math.min(1, v.k + dt / 1.1); v.x = BOAT_X + 4 * (1 - v.k) ** 2; if (v.k >= 1) { v.phase = "walk"; v.x = DOCK.x; this.boats.push({ x: BOAT_X, z: DOCK.z, vx: 0, face: -1 }); } }
      else if (v.phase === "walk") {
        const tx = cu.x + SEAT_DX, tz = cu.z, dx = tx - v.x, dz = tz - v.z, d = Math.hypot(dx, dz), step = WALK * dt;
        v.walk += dt; v.face = dx < 0 ? -1 : 1;
        if (d <= step) { v.x = tx; v.z = tz; v.phase = "seat"; v.face = -1; } else { v.x += dx / d * step; v.z += dz / d * step; }
      }
    }
    for (const w of this.walkers) {
      const tx = w.leg ? BOAT_X : DOCK.x, tz = DOCK.z, dx = tx - w.x, dz = tz - w.z, d = Math.hypot(dx, dz), step = WALK * dt;
      w.walk += dt;
      if (d <= step) { w.x = tx; w.z = tz; if (w.leg) { w.done = true; this.boats.push({ x: BOAT_X, z: DOCK.z, vx: 1, who: w.who, angry: w.angry }); } else w.leg = 1; }
      else { w.x += dx / d * step; w.z += dz / d * step; }
    }
    this.walkers = this.walkers.filter((w) => !w.done);
    for (const b of this.boats) { b.vx = Math.min(5, b.vx + dt * 3); b.x += b.vx * dt; }
    this.boats = this.boats.filter((b) => b.x < BOAT_X + 6);
    for (const k of this.coins) k.t += dt;
    this.coins = this.coins.filter((k) => k.t < 0.95);
    for (const s of this.stoves) if (s.state === "cooking") {
      this.sparkT -= dt;
      if (this.sparkT <= 0) {
        this.sparkT = 0.07;
        const x = this._sx(s.pos[0]), y = this._sy(s.pos[1]) - 20;
        this.ps.add({ x: x + (Math.random() - 0.5) * 14, y, vx: (Math.random() - 0.5) * 50, vy: -40 - Math.random() * 40, g: 160, size: 1, life: 0.35 + Math.random() * 0.2, color: Math.random() < 0.5 ? "#ffd23a" : "#ff8a3d" });
      }
    }
  }
  updateMenu() {
    const keys = Object.keys(this.menu);
    if (!keys.length) { if (input.hit("back") || input.hit("interact") || input.hit("confirm")) this.menuOpen = false; return; }
    if (input.hit("up")) { this.menuSel = (this.menuSel + keys.length - 1) % keys.length; sfx("click"); }
    if (input.hit("down")) { this.menuSel = (this.menuSel + 1) % keys.length; sfx("click"); }
    if (input.hit("back")) { this.menuOpen = false; sfx("click"); }
    if (input.hit("interact") || input.hit("confirm")) this.cook(keys[this.menuSel]);
  }

  // transforms (contract → low-res screen)
  _sx(x) { return Math.round(X0 + x * XS); }
  _sy(z) { return Math.round(Y0 - z * ZS) + (this.bob || 0); }

  draw() {
    const c = screen.px, time = performance.now() / 1000;
    this.bob = Math.round(Math.sin(time * 1.2) * 0.7);
    const dusk = clamp(1 - (1 - this.time / this.t.duration_s) / 0.3, 0, 1); // sunset fades out over the first 30% of the shift
    c.imageSmoothingEnabled = false;
    // ---- river backdrop (no back wall: the whole Mekong night behind the raft) ----
    this.cs.t = time;
    riverWorld(c, this.cs, "night");
    if (dusk > 0) { c.save(); c.globalAlpha = dusk; riverWorld(c, this.cs, "dusk"); c.restore(); }
    c.save(); c.globalAlpha = 1 - dusk * 0.8; moon(c, 392, 70); c.restore();
    const lights = [];
    // far water (river surface between the far bank and our raft), with lantern + moon reflections
    const farBoats = [0, 1].map((i) => ({ x: ((i * 260 + time * (6 + i * 3)) % (W + 140)) - 70, y: 136 + i * 12, i }));
    nightWater(c, HORIZON + 2, H, time, [...[40, 190, 340].map((x) => [x - 4, HORIZON + 3, 22]), ...farBoats.map((b) => [b.x - 3, b.y + 2, 14])], 392);
    for (const b of farBoats) { sampan(c, b.x, b.y, 1, time + b.i, 0.45, { roof: b.i ? "#6b3d22" : null }); R(c, b.x - 3, b.y - 14, 1, 10, P.woodD); R(c, b.x - 5, b.y - 17, 5, 4, P.red); R(c, b.x - 4, b.y - 16, 3, 2, P.yellow); lights.push([b.x - 3, b.y - 15, 6, 0.08]); }
    // ---- the raft ----
    const yb = Y_BACK + this.bob, yf = Y_FRONT + this.bob;
    roofAndPosts(c, DECK_L, DECK_R + 4, yf, time);
    backRail(c, 150, DECK_R, yb);
    kitchenBack(c, DECK_L + 4, 146, yb, time);
    deck(c, DECK_L, DECK_R, yb, yf, time);
    // front water line under the floats: warm reflections of the lantern strings, ripples
    const frontRefl = []; for (let x = 60; x < DECK_R; x += 44) frontRefl.push([x, yf + 12, 14]);
    for (const [lx, , len] of frontRefl) for (let k = 0; k < len; k += 2) R(c, lx - 2 + Math.round(Math.sin(time * 3 + k + lx) * 1.5), yf + 14 + k, 3 + (k % 3), 1, `rgba(255,170,80,${0.32 - k * 0.02})`);
    R(c, 0, yf + 12, W, 1, "rgba(200,220,255,.35)");
    for (let i = 0; i < 5; i++) ripple(c, 40 + i * 92, yf + 18, time, i * 0.21);
    // gangway at the right edge where sampans dock
    const dockY = this._sy(DOCK.z);
    landing(c, DECK_R, dockY, time); lights.push([DECK_R + 13, dockY - 27, 18, 0.14]);
    // ---- depth-sorted actors ----
    const ents = [];
    for (const s of this.stoves) ents.push({ z: s.pos[1], draw: () => this.drawStove(c, s, time) });
    ents.push({ z: PASS.z, draw: () => this.drawPass(c, time) });
    ents.push({ z: BA_TU.z, draw: () => this.drawBaTu(c, time) });
    for (const tb of this.tables) ents.push({ z: tb.pos[1] + 0.05, draw: () => this.drawTable(c, tb, time) });
    for (const cu of this.customers) if (cu.state !== "gone" && cu.state !== "done" && cu.vis) ents.push({ z: cu.vis.z - 0.02, draw: () => this.drawCustomer(c, cu, time) });
    for (const w of this.walkers) ents.push({ z: w.z - 0.02, draw: () => this.drawWalker(c, w, time) });
    for (const b of this.boats) ents.push({ z: b.z + 0.5, draw: () => this.drawBoat(c, b, time) });
    ents.push({ z: this.p.z, draw: () => this.drawPlayer(c, time) });
    ents.sort((a, b) => b.z - a.z);
    ents.forEach((e) => e.draw());
    // smoke + steam over the kitchen
    this.drawReady(c, time);
    for (const s of this.stoves) if (s.state === "cooking") smoke(c, this._sx(s.pos[0]) + 2, this._sy(s.pos[1]) - 24, time);
    this.ps.draw(c, 0, 0);
    // ---- roof lanterns + light ----
    lanternString(c, 104, 232, 19, 14, 5, time, lights);
    lanternString(c, 248, 372, 19, 14, 5, time, lights);
    lanternString(c, DECK_L + 6, 98, 54, 6, 3, time, lights);
    lanternString(c, 380, DECK_R, 44, 8, 2, time, lights);
    for (const L of lights) glow(c, L[0], L[1], L[2] || 22, L[3] || 0.1);
    for (const s of this.stoves) if (s.state !== "idle") glow(c, this._sx(s.pos[0]), this._sy(s.pos[1]) - 8, 46, 0.16 + Math.sin(time * 18) * 0.02, "255,120,40");
    c.fillStyle = "rgba(255,150,70,.05)"; c.fillRect(DECK_L, 19, DECK_R - DECK_L, yb - 19);
    // ---- overlays: coins, order bubbles, badges, prompts, toasts ----
    this.drawCoins(c);
    for (const cu of this.customers) if (cu.state === "waiting" && cu.vis) this.drawOrder(c, cu, time);
    this.drawPrompts(time);
    this.toasts.forEach((t) => txt(t.txt, this._sx(t.x), this._sy(t.z) - 26 + t.oy, { size: 9, align: "center", color: t.col, weight: 900, stroke: "#1a1220", sw: 2.5, alpha: clamp(t.life, 0, 1) }));

    this.drawHUD(c, time);
    if (this.menuOpen) this.drawMenu(c, time);
    if (this.result) this.drawResult(c, time);
    else if (this.hintT > 0 && !this.started) this.drawHint(c);
  }
  drawStove(c, s, time) {
    const x = this._sx(s.pos[0]), y = this._sy(s.pos[1]), sc = depthScale(s.pos[1]) * (s.pop > 0 ? 1 + s.pop * 0.25 : 1);
    scaled(c, sc, x, y, (cc, ax, ay) => clayStove(cc, ax, ay, s.state, time));
    if (s.state === "cooking") { const fr = 1 - s.cook / s.cookMax; this.ring(c, x, y - 40, fr, "#ff8a3d"); txt(Math.ceil(s.cook) + "s", x, y - 37, { size: 7, align: "center", color: "#fff", weight: 900, stroke: "#1a1220", sw: 2 }); }
  }
  // where a stove's finished dish waits: the first two stoves use the left/right half of the pass, others sit on their own wok
  readySpot(i) {
    const s = this.stoves[i];
    if (i < 2) return [this._sx(PASS.x) + (i ? 4 : -12), this._sy(PASS.z) - 30];
    return [this._sx(s.pos[0]) - 8, this._sy(s.pos[1]) - 38];
  }
  drawPass(c, time) {
    const x = this._sx(PASS.x), y = this._sy(PASS.z);
    scaled(c, depthScale(PASS.z), x, y, (cc, ax, ay) => passCounter(cc, ax, ay));
    if (!this.stoves.some((s) => s.state === "ready")) { R(c, x - 9, y - 17, 7, 2, "#e8e2d0"); R(c, x - 9, y - 19, 7, 2, "#f2efe6"); } // stacked bowls
  }
  drawReady(c, time) {
    this.stoves.forEach((s, i) => {
      if (s.state !== "ready") return;
      const [x, y] = this.readySpot(i), dy = Math.round(Math.sin(time * 4 + i));
      c.drawImage(dishIcon(s.dish), x, y + dy, 16, 16);
      steam(c, x + 8, y + dy, time + i, 3, 12);
      txt("E", this._sx(s.pos[0]) + 14, this._sy(s.pos[1]) - 26, { size: 8, align: "center", color: "#79c75a", weight: 900, stroke: "#1a1220", sw: 2 });
    });
  }
  drawBaTu(c, time) {
    const busy = this.stoves.some((s) => s.state === "cooking");
    const x = this._sx(BA_TU.x), y = this._sy(BA_TU.z);
    scaled(c, depthScale(BA_TU.z), x, y, (cc, ax, ay) => personSide(cc, ax, ay, { face: 1, shirt: "#7a4fa0", pants: "#3a2a4a", hair: "#c9c2d4", bun: true, bunTie: P.red, apron: true, arm: busy ? "stir" : (Math.sin(time * 0.7) > 0.85 ? "wave" : null), t: time }));
  }
  drawTable(c, tb, time) {
    const x = this._sx(tb.pos[0]), y = this._sy(tb.pos[1]), cu = this.customers.find((k) => k.table === tb.id && k.state === "eating");
    scaled(c, depthScale(tb.pos[1]), x, y, (cc, ax, ay) => {
      stool(cc, ax - 19, ay); stool(cc, ax + 19, ay); sideTable(cc, ax, ay);
      if (cu) cc.drawImage(dishIcon(cu.want), ax + 2, ay - 24, 12, 12);
    });
    if (cu) steam(c, x + 8, y - 24, time, 3, 10);
  }
  custLook(cu) { return { shirt: cu.shirt || "#3a6fd8", hair: cu.hair || "#2a1d2b", hat: !!cu.hat }; }
  drawCustomer(c, cu, time) {
    const v = cu.vis, type = cu.type || "quen";
    const x = this._sx(v.x), y = this._sy(v.z);
    if (v.phase === "boat") { this.drawBoat(c, { x: v.x, z: DOCK.z, rider: cu }, time); return; }
    const seated = v.phase === "seat";
    // impatient customers fidget while waiting
    const jig = type === "voi" && cu.state === "waiting" && seated ? Math.round(Math.sin(time * 14) * 0.6) : 0;
    scaled(c, depthScale(v.z), x + jig, y, (cc, ax, ay) => {
      personSide(cc, ax, ay, { ...this.custLook(cu), face: seated ? -1 : v.face, sit: seated, walk: seated ? 0 : v.walk, arm: cu.state === "eating" ? "eat" : null, t: time });
      if (type === "sop") { cc.fillStyle = "#ffe9a0"; cc.fillRect(ax - 2, ay - 12, 4, 1); cc.fillStyle = "#e0a21a"; cc.fillRect(ax - 1, ay - 11, 2, 1); } // gold chain
    });
    if (cu.state === "eating") txt(Math.floor(time * 3) % 2 ? "😋" : "😊", x + 8, y - 26, { size: 9 });
  }
  drawWalker(c, w, time) {
    const x = this._sx(w.x), y = this._sy(w.z), cu = w.who;
    scaled(c, depthScale(w.z), x, y, (cc, ax, ay) => personSide(cc, ax, ay, { ...this.custLook(cu), face: 1, walk: w.walk, angry: w.angry, t: time }));
    if (w.angry && Math.floor(time * 4) % 2) txt("💢", x - 6, y - 26, { size: 8 });
  }
  drawBoat(c, b, time) {
    const x = this._sx(b.x), y = this._sy(DOCK.z) + 10 + Math.round(Math.sin(time * 2 + b.x) * 1);
    const f = b.face ?? (b.vx > 0 ? 1 : -1); // drop-off boats back out with the bow still pointing at the raft
    sampan(c, x, y, f, time, 0.72, { roof: "#6b3d22" });
    // ferryman at the stern
    personSide(c, x - 12 * f, y - 5, { face: f, shirt: "#3a4a6a", hat: true, t: time });
    const rider = b.rider || b.who;
    if (rider) personSide(c, x + 3 * f, y - 5, { ...this.custLook(rider), face: f, angry: b.angry, t: time });
  }
  drawPlayer(c, time) {
    const p = this.p, x = this._sx(p.x), y = this._sy(p.z), carry = this.hand ? this.hand.key : null;
    scaled(c, depthScale(p.z), x, y, (cc, ax, ay) => personSide(cc, ax, ay, { face: p.face, shirt: P.suit, hair: P.hair, bun: true, apron: true, walk: p.walk, carry, t: time }));
    if (carry) steam(c, x + 1, y - Math.round(36 * depthScale(p.z)), time, 3, 9);
  }
  drawCoins(c) {
    for (const k of this.coins) {
      if (k.t < 0) continue;
      let x, y;
      if (k.t < 0.4) { x = k.x0 + k.vx * k.t; y = k.y0 - 60 * k.t + 140 * k.t * k.t; }
      else { const u = clamp((k.t - 0.4) / 0.5, 0, 1), sx = k.x0 + k.vx * 0.4, sy = k.y0 - 24 + 22.4; x = lerp(sx, 40, u * u); y = lerp(sy, 12, u * u); }
      coin(c, Math.round(x), Math.round(y), k.t * 14);
    }
  }
  // order bubble above a waiting customer (wherever they are: boat, deck or stool)
  drawOrder(c, cu, time) {
    const v = cu.vis, type = cu.type || "quen", ty = CUST_TYPES[type];
    const x = this._sx(v.x), y = v.phase === "boat" ? this._sy(DOCK.z) + 5 : this._sy(v.z);
    const bx = x - 4, by = y - 44;
    c.fillStyle = ty.bubble; c.beginPath(); c.arc(bx, by, 10, 0, TAU); c.fill();
    R(c, x - 1, y - 32, 2, 2, ty.bubble); R(c, x - 3, y - 35, 3, 2, ty.bubble);
    c.imageSmoothingEnabled = false; c.drawImage(dishIcon(cu.want), bx - 8, by - 8, 16, 16);
    if (type !== "quen") pixIcon(c, type, bx - 12, by - 12);
    // patience ring: fraction of THIS customer's own max patience
    const fr = cu.patience / (cu.patienceMax || this.t.patience_s);
    this.ring(c, bx, by, fr, fr < 0.3 ? "#ff5a5a" : fr < 0.6 ? "#ffd23a" : "#79c75a", 11);
    if (fr < 0.3 && Math.floor(time * 6) % 2) txt("!", x + 8, y - 30, { size: 11, color: "#ff5a5a", weight: 900, stroke: "#1a1220", sw: 2 });
    if (this.menuOpen || this.result) return; // UI-layer labels would sit above the dimmed overlay
    txt(this.payFor(cu) + "k", bx + 13, by + 3, { size: 7, color: ty.col, weight: 900, stroke: "#1a1220", sw: 2 });
    this.drawBadge(cu, bx, by - 12);
  }
  // type badge above the order bubble (UI layer): pixel icon + short label
  drawBadge(cu, x, top) {
    const type = cu.type || "quen", ty = CUST_TYPES[type], u = screen.ui;
    const tw = measure(ty.badge, 7, 900), w = Math.ceil(tw) + 13, h = 10;
    const bx = Math.round(x - w / 2), by = Math.round(top - h - 1);
    panel(bx, by, w, h, { fill: "rgba(42,24,14,.9)", border: ty.col, bw: 1, r: 3 });
    pixIcon(u, type, bx + 3, by + 2);
    txt(ty.badge, bx + 10, by + 8, { size: 7, color: ty.col, weight: 900 });
  }
  drawPrompts(time) {
    if (this.menuOpen || this.result) return;
    const s = this.nearStove(), o = { size: 8, align: "center", weight: 900, stroke: "#1a1220", sw: 2.5 };
    if (s) {
      const x = this._sx(s.pos[0]), y = this._sy(s.pos[1]) + 10;
      if (this.hand) txt("E: Đổ món", x, y, { ...o, color: "#ff9a9a" });
      else if (s.state === "idle") txt("E: Nấu", x, y, { ...o, color: "#ffd23a" });
      else if (s.state === "ready") txt("E: Bưng", x, y, { ...o, color: "#79c75a" });
      return;
    }
    const cu = this.nearTable();
    if (cu && cu.state === "waiting" && this.hand) txt(cu.want === this.hand.key ? "E: Phục vụ" : "Sai món", this._sx(cu.x), this._sy(cu.z) + 10, { ...o, color: cu.want === this.hand.key ? "#79c75a" : "#ff9a9a" });
  }
  ring(c, x, y, fr, col, r = 9) { c.strokeStyle = "rgba(0,0,0,.4)"; c.lineWidth = 2; c.beginPath(); c.arc(x, y, r, 0, TAU); c.stroke(); c.strokeStyle = col; c.lineWidth = 1.5; c.beginPath(); c.arc(x, y, r, -Math.PI / 2, -Math.PI / 2 + TAU * fr); c.stroke(); }

  drawHUD(c, time) {
    const u = screen.ui, F = HUD.fill;
    const mm = Math.floor(Math.ceil(this.time) / 60), ss = Math.ceil(this.time) % 60, low = this.time < 20;
    panel(W / 2 - 24, 4, 48, 15, { fill: F, border: low ? "#ff6b6b" : HUD.border, r: 7 });
    txt(`${mm}:${String(ss).padStart(2, "0")}`, W / 2, 15, { size: 11, align: "center", color: low ? "#ff8a8a" : HUD.text, weight: 900 });
    panel(W / 2 - 22, 21, 44, 11, { fill: F, border: HUD.dim, r: 5 });
    txt("Ngày " + this.day, W / 2, 29.5, { size: 7.5, align: "center", color: "#ffd23a", weight: 900 });
    // shift tally: served / walked out
    panel(6, 40, 70, 13, { fill: F, border: HUD.dim, r: 5 });
    txt("Phục vụ " + this.served, 11, 49.5, { size: 7, color: "#9fe8a0", weight: 900 });
    txt("Bỏ " + this.left, 71, 49.5, { size: 7, align: "right", color: this.left ? "#ff8a8a" : "#c9a88a", weight: 900 });
    // money
    panel(6, 5, 70, 15, { fill: F, border: HUD.border, r: 6 });
    txt("🪙", 12, 16, { size: 9 }); txt(this.money + "k", 72, 16, { size: 11, align: "right", color: "#ffe14d", weight: 900 });
    // reputation stars
    const rx = 6, ry = 23;
    panel(rx, ry, 92, 14, { fill: F, border: this.repFlash > 0 ? "#fff" : HUD.dim, r: 6 });
    for (let i = 0; i < 5; i++) { const full = this.rep >= i + 0.75, half = this.rep >= i + 0.25 && !full; this.star(u, rx + 10 + i * 15, ry + 7, full ? 1 : half ? 0.5 : 0, time, i); }
    txt(this.rep.toFixed(1), rx + 88, ry + 11, { size: 8, align: "right", color: HUD.text, weight: 900 });
    // stock chips
    // stock chips: AVAILABLE amounts (reserved by waiting orders shown in grey as +n)
    const resv = this.reservedTotals();
    const keys = Object.keys({ ...this.stock, ...resv }).filter((k) => (this.stock[k] || 0) > 0 || (resv[k] || 0) > 0);
    const sw2 = keys.some((k) => resv[k]) ? 40 : 30, sx0 = W - 6 - keys.length * sw2;
    keys.forEach((k, i) => { const x = sx0 + i * sw2; panel(x, 5, sw2 - 2, 15, { fill: F, border: HUD.dim, r: 4 }); u.imageSmoothingEnabled = false; u.drawImage(icon(k), x + 2, 7, 10, 10);
      txt("×" + (this.stock[k] || 0), x + 13, 16, { size: 8, color: (this.stock[k] || 0) ? HUD.text : "#ff9a9a", weight: 900 });
      if (resv[k]) txt("+" + resv[k], x + sw2 - 4, 16, { size: 7, align: "right", color: "rgba(200,200,200,.6)", weight: 800 }); });
    // early-close button (wood style, clickable) + confirmation / no-dish banners
    if (!this.result) {
      const b = this.closeBtn, armed = this.confirmClose > 0;
      panel(b.x, b.y, b.w, b.h, { fill: armed ? "rgba(140,40,20,.95)" : "rgba(110,64,32,.95)", border: armed ? "#ffb36b" : "#3a2410", bw: 1.5, r: 4 });
      txt(armed ? "Nhấn lần nữa!" : "Đóng quán sớm (C)", b.x + b.w / 2, b.y + 10.5, { size: 7, align: "center", color: "#ffe9c4", weight: 900 });
      if (armed) { panel(W / 2 - 110, 52, 220, 16, { fill: "rgba(120,30,20,.92)", border: "#ffb36b", r: 6 }); txt("Nhấn C lần nữa để đóng quán", W / 2, 63, { size: 9, align: "center", color: "#fff", weight: 900 }); }
      else if (this.noDish) { const a = 0.75 + 0.25 * Math.sin(time * 4); panel(W / 2 - 150, 52, 300, 16, { fill: `rgba(80,20,20,${0.9 * a})`, border: "#ff8a8a", r: 6 }); txt("Hết nguyên liệu — không còn khách mới · C: Đóng quán sớm", W / 2, 63, { size: 8, align: "center", color: "#ffe0d0", weight: 900 }); }
    }
    // hand indicator
    if (this.hand) { const s = "Đang bưng: " + dishName(this.hand.key), hw = Math.max(86, Math.ceil(measure(s, 7, 800)) + 10); panel(W - 6 - hw, 23, hw, 14, { fill: "rgba(70,30,12,.9)", border: "#ff8a3d", r: 6 }); txt(s, W - 1 - hw, 33, { size: 7, color: "#ffd0a0", weight: 800 }); }
    txt("WASD đi · E nấu/bưng/phục vụ · C đóng quán sớm · Esc/P tạm dừng", W / 2, H - 4, { size: 7, align: "center", color: "rgba(255,233,196,.55)", weight: 700, stroke: "rgba(10,8,20,.6)", sw: 2 });
  }
  star(u, x, y, fill, time, i) {
    u.save(); u.translate(x, y);
    const pop = this.repFlash > 0 ? 1 + Math.sin(time * 20) * 0.1 : 1; u.scale(pop, pop);
    u.beginPath();
    for (let k = 0; k < 10; k++) { const r = k % 2 ? 2 : 5, a = -Math.PI / 2 + k * Math.PI / 5; u[k ? "lineTo" : "moveTo"](Math.cos(a) * r, Math.sin(a) * r); }
    u.closePath();
    u.fillStyle = fill >= 1 ? "#ffd23a" : fill > 0 ? "#ffd23a" : "rgba(255,255,255,.15)";
    if (fill === 0.5) { u.save(); u.fillStyle = "rgba(255,255,255,.15)"; u.fill(); u.clip(); u.fillStyle = "#ffd23a"; u.fillRect(-6, -6, 6, 12); u.restore(); } else u.fill();
    u.lineWidth = 0.6; u.strokeStyle = "rgba(0,0,0,.5)"; u.stroke();
    u.restore();
  }
  drawMenu(c, time) {
    c.fillStyle = "rgba(14,8,6,.55)"; c.fillRect(0, 0, W, H);
    const keys = Object.keys(this.menu), rowH = keys.length > 4 ? 28 : 34, pw = 240, ph = 26 + Math.max(1, keys.length) * rowH;
    const px = W / 2 - pw / 2, py = H / 2 - ph / 2;
    panel(px, py, pw, ph, { fill: "rgba(46,26,14,.97)", border: HUD.border, bw: 1.5, r: 6 });
    txt("CHỌN MÓN NẤU", W / 2, py + 15, { size: 11, align: "center", color: "#ffd23a", weight: 900 });
    if (this.cookMul !== 1) txt("Bếp ×" + this.cookMul, px + pw - 8, py + 14, { size: 7, align: "right", color: this.cookMul < 1 ? "#7ee87e" : "#ff9a9a", weight: 900 });
    if (!keys.length) txt("Tối nay chưa có món nào trong thực đơn", W / 2, py + 40, { size: 8, align: "center", color: "#ff9a9a", weight: 800 });
    keys.forEach((k, i) => {
      const y = py + 24 + i * rowH, m = this.menu[k], sel = i === this.menuSel, can = this.canCook(k);
      if (sel) panel(px + 5, y, pw - 10, rowH - 4, { fill: can ? "rgba(255,210,100,.18)" : "rgba(255,80,80,.14)", border: can ? "#ffd23a" : "#ff6b6b", r: 4 });
      screen.ui.imageSmoothingEnabled = false; screen.ui.drawImage(dishIcon(k), px + 12, y + 2, 18, 18);
      txt(dishName(k), px + 36, y + 11, { size: 9, color: can ? HUD.text : "#ff9a9a", weight: 800 });
      const rec = Object.entries(m.recipe).map(([ik, n]) => `${KIND_NAME[ik] || ik}×${n}`).join(" + ");
      txt(rec, px + 36, y + 22, { size: 7, color: can ? "#c9a88a" : "#d98", weight: 700 });
      txt(m.price + "k", px + pw - 12, y + 11, { size: 10, align: "right", color: "#ffe14d", weight: 900 });
      const eff = this.cookTime(k);
      if (eff !== m.cook_s) { // upgraded stove: effective time, base time dimmed beside it
        txt(fmtS(eff), px + pw - 12, y + 22, { size: 7, align: "right", color: "#7ee87e", weight: 900 });
        txt(fmtS(m.cook_s) + " →", px + pw - 12 - measure(fmtS(eff), 7, 900) - 3, y + 22, { size: 7, align: "right", color: "rgba(201,168,138,.6)", weight: 700 });
      } else txt(fmtS(m.cook_s), px + pw - 12, y + 22, { size: 7, align: "right", color: "#c9a88a", weight: 700 });
    });
    txt("↑↓ chọn · E nấu · Esc huỷ", W / 2, py + ph - 6, { size: 7, align: "center", color: "rgba(255,233,196,.6)", weight: 700 });
  }
  drawHint(c) {
    const a = clamp(this.hintT, 0, 1);
    panel(W / 2 - 96, H / 2 - 30, 192, 36, { fill: `rgba(42,24,14,${0.9 * a})`, border: HUD.border, r: 6, alpha: a });
    txt("Tới bếp (E) nấu món khách muốn, rồi bưng ra bàn", W / 2, H / 2 - 14, { size: 8.5, align: "center", color: HUD.text, weight: 800, alpha: a });
    txt("Khách bỏ đi = mất uy tín!", W / 2, H / 2 - 1, { size: 8, align: "center", color: "#ffd23a", weight: 700, alpha: a });
  }
  drawResult(c, time) {
    const r = this.result, k = clamp(r.t / 0.5, 0, 1);
    c.fillStyle = `rgba(14,8,6,${0.72 * k})`; c.fillRect(0, 0, W, H);
    if (r.t < 1.4) speedLines(c, W / 2, H / 2 - 20, time, "rgba(255,200,110,.12)");
    txt(r.closedEarly ? "ĐÓNG QUÁN SỚM" : "HẾT BUỔI TỐI!", W / 2, H / 2 - 44, { size: 24 * lerp(1.5, 1, k), align: "center", color: "#ffd23a", weight: 900, italic: true, stroke: "#1a1220", sw: 5, rot: -0.03 });
    panel(W / 2 - 90, H / 2 - 30, 180, 76, { fill: "rgba(42,24,14,.95)", border: HUD.border, r: 5 });
    panel(W / 2 - 22, H / 2 - 36, 44, 11, { fill: "rgba(42,24,14,1)", border: HUD.border, r: 5 }); // day tab on the panel's top edge
    txt("Ngày " + (r.day ?? this.day), W / 2, H / 2 - 27.5, { size: 7.5, align: "center", color: "#ffd23a", weight: 900 });
    txt("Doanh thu", W / 2 - 80, H / 2 - 16, { size: 9, color: HUD.text, weight: 700 });
    txt(Math.floor(r.money * clamp(r.t, 0, 1)) + "k", W / 2 + 80, H / 2 - 16, { size: 11, align: "right", color: "#ffe14d", weight: 900 });
    txt("Khách", W / 2 - 80, H / 2 - 2, { size: 9, color: HUD.text, weight: 700 });
    txt("phục vụ " + r.served, W / 2 + 20, H / 2 - 2, { size: 9, align: "right", color: "#9fe8a0", weight: 900 });
    txt("bỏ đi " + r.left, W / 2 + 80, H / 2 - 2, { size: 9, align: "right", color: r.left ? "#ff8a8a" : "#c9a88a", weight: 900 });
    txt("Uy tín", W / 2 - 80, H / 2 + 13, { size: 9, color: HUD.text, weight: 700 });
    const u = screen.ui; for (let i = 0; i < 5; i++) this.star(u, W / 2 - 6 + i * 13, H / 2 + 9, i < r.stars ? 1 : 0, time, i);
    R(c, W / 2 - 82, H / 2 + 22, 164, 1, "rgba(255,220,160,.2)");
    txt("ĐIỂM", W / 2 - 80, H / 2 + 37, { size: 10, color: HUD.text, weight: 900 });
    txt("" + Math.floor(r.score * clamp(r.t * 0.8, 0, 1)), W / 2 + 80, H / 2 + 37, { size: 14, align: "right", color: "#7ee87e", weight: 900 });
    if (r.t > 1) txt(Math.floor(r.t * 2) % 2 ? "Enter: chơi lại từ đầu   ·   R: làm lại buổi tối" : "", W / 2, H - 20, { size: 9, align: "center", color: "#fff", weight: 900 });
  }
}
