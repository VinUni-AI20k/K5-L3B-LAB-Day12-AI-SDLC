// QUÁN scene — GUI ONLY. Local mock; swap `st` for the server snapshot later.
// Top-down raft: x in [0,16], z in [0,10], z up = north. y on screen is flipped from z.
import { W, H, screen, input, clamp, lerp, fx, Particles, txt, panel, measure } from "./engine.js";
import { sfx, music } from "./audio.js";
import { P, R, planks, lantern, stove, table, chibi, ripple, dishIcon, icon, DISH_NAME, KIND_NAME, portrait } from "./art.js";
import { speedLines } from "./cutscene.js";
import { save, stats } from "./progress.js";

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
  constructor(contract, stock, onEnd) {
    this.t = contract.tuning.quan; this.menu = contract.tuning.menu; this.onEnd = onEnd;
    const t = this.t;
    this.p = { x: t.start_pos[0], z: t.start_pos[1], vx: 0, vz: 0, face: 1, walk: 0 };
    this.stock = stock ? { ...stock } : { ca_loc: 3, ca_linh: 6, bong_sung: 4, bong_dien_dien: 2 }; // null = demo stock; {} = empty basket
    this.stoves = t.stoves.map((s) => ({ ...s, state: "idle", dish: null, cook: 0, cookMax: 0, pop: 0 }));
    this.tables = t.tables.map((tb) => ({ ...tb }));
    this.hand = null; this.customers = []; this.time = t.duration_s;
    this.money = 0; this.rep = t.reputation_initial; this.score = 0;
    this.nextCust = t.first_customer_tick / 60; this.custSeq = 0;
    this.cam = { x: t.bounds.x[1] / 2, z: t.bounds.z[1] / 2 };
    this.ps = new Particles(); this.toasts = []; this.ended = false; this.result = null;
    this.menuOpen = false; this.menuSel = 0; this.hintT = 4; this.started = false; this.repFlash = 0;
    // meta progression: stove upgrade multiplies cook time; day shifts the customer mix
    let st = null; try { st = stats(contract); } catch (e) {}
    this.cookMul = st && st.cookMul > 0 ? st.cookMul : 1;
    this.basePatience = st && st.patienceS > 0 ? st.patienceS : t.patience_s;
    this.day = (save && save.day) || 1;
    this.served = 0; this.left = 0;
    this.nextType = null; // ?debug: set to "quen" | "voi" | "sop" to force the next customer's type
    music("restaurant");
  }
  cookTime(key) { return this.menu[key].cook_s * this.cookMul; }
  toast(x, z, txt, col) { this.toasts.push({ x, z, txt, col, life: 1.5, oy: 0 }); }
  canCook(key) { const r = this.menu[key].recipe; return Object.entries(r).every(([k, n]) => (this.stock[k] || 0) >= n); }

  spawnCustomer() {
    const tb = this.tables[this.custSeq % this.tables.length];
    if (this.customers.some((c) => c.table === tb.id)) return;
    const keys = Object.keys(this.menu).filter((k) => this.canCook(k));
    if (!keys.length) { if (!this.noDishShown) { this.noDishShown = true; this.toast(tb.pos[0], tb.pos[1] + 1, "Hết nguyên liệu — khách không gọi được món", "#ff8a8a"); } return; }
    // first customer of a shift is always a regular (gentle start); later ones follow the day's weights
    const type = this.nextType && CUST_TYPES[this.nextType] ? this.nextType : this.custSeq === 0 ? "quen" : pickType(this.day);
    this.nextType = null;
    const ty = CUST_TYPES[type];
    const want = ty.priciest
      ? keys.reduce((a, k) => (this.menu[k].price > this.menu[a].price ? k : a), keys[0])
      : keys[Math.floor(Math.random() * keys.length)];
    const patMax = this.basePatience * ty.patMul, seq = ++this.custSeq, shirts = SHIRTS[type];
    this.customers.push({ id: "C" + seq, table: tb.id, x: tb.pos[0], z: tb.pos[1], want, type, state: "waiting", patience: patMax, patienceMax: patMax, eat: 0, enter: 0, portrait: "khach",
      shirt: shirts[seq % shirts.length], hair: HAIRS[type], hat: type === "quen" && seq % 2 === 0 });
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
      if (st) { this.toast(st.pos[0], st.pos[1] + 1, "Đổ " + DISH_NAME[this.hand.key], "#ff8a8a"); this.hand = null; sfx("whoosh"); return; }
      const cu = this.nearTable();
      if (cu && cu.state === "waiting" && cu.want === this.hand.key) this.serve(cu);
      else if (cu && cu.state === "waiting") { this.toast(cu.x, cu.z + 1, "Sai món! (E ở bếp để đổ)", "#ff6b6b"); sfx("hurt"); }
      else this.toast(this.p.x, this.p.z + 1, "Không có khách ở đây", "#ffd23a");
      return;
    }
    const s = this.nearStove();
    if (s) {
      if (s.state === "ready") { const dish = s.dish; this.hand = { key: dish }; s.state = "idle"; s.dish = null; sfx("pick"); this.toast(s.pos[0], s.pos[1] + 1, "Bưng " + DISH_NAME[dish], "#9fe"); }
      else if (s.state === "idle") { this.menuOpen = true; this.menuSel = 0; sfx("select"); }
      else this.toast(s.pos[0], s.pos[1] + 1, "Đang nấu...", "#ffd23a");
    }
  }
  cook(key) {
    const s = this.nearStove(); if (!s || s.state !== "idle") return;
    if (!this.canCook(key)) { this.toast(s.pos[0], s.pos[1] + 1, "Thiếu nguyên liệu", "#ff6b6b"); sfx("hurt"); return; }
    for (const [k, n] of Object.entries(this.menu[key].recipe)) this.stock[k] -= n;
    s.state = "cooking"; s.dish = key; s.cookMax = this.cookTime(key); s.cook = s.cookMax;
    sfx("sizzle"); this.menuOpen = false;
    this.toast(s.pos[0], s.pos[1] + 1, "Bắc bếp!", "#ff8a3d");
  }
  serve(cu) {
    const dish = this.menu[cu.want], ty = CUST_TYPES[cu.type || "quen"];
    const ratio = cu.patience / (cu.patienceMax || this.t.patience_s);
    const tip = ratio >= this.t.tip_min_patience_ratio ? Math.floor(dish.price * this.t.tip_rate) * ty.tipMul : 0;
    const gain = this.payFor(cu) + tip;
    this.money += gain; this.hand = null; cu.state = "eating"; cu.eat = this.t.eat_s; this.served++;
    this.rep = clamp(this.rep + (tip ? this.t.tip_reputation : 0), this.t.reputation_min, this.t.reputation_max);
    this.repFlash = 0.5;
    sfx("coin"); if (tip) sfx("ding"); fx.flash("rgba(255,220,120,.2)", 0.12);
    this.toast(cu.x, cu.z + 1.2, `+${gain}k${tip ? " 🪙" : ""}`, "#ffe14d");
    const sx = this._sx(cu.x), sy = this._sy(cu.z);
    for (let i = 0; i < 10; i++) this.ps.add({ x: sx, y: sy - 6, vx: (Math.random() - .5) * 40, vy: -20 - Math.random() * 30, g: 90, size: 1 + (i % 2), life: 0.7, color: i % 2 ? "#ffd23a" : "#fff0a8" });
  }
  leave(cu) {
    const delta = this.t.left_reputation_delta * CUST_TYPES[cu.type || "quen"].leaveMul;
    cu.state = "gone"; this.left++; this.rep = clamp(this.rep + delta, this.t.reputation_min, this.t.reputation_max);
    this.repFlash = 0.5; sfx("hurt"); fx.shake(cu.type === "sop" ? 5 : 3, 0.3);
    this.toast(cu.x, cu.z + 1, "Bỏ đi 😠 " + delta + " uy tín", "#ff6b6b");
  }

  endRun() {
    if (this.ended) return; this.ended = true;
    this.score = this.money + 100 * Math.floor(this.rep);
    this.result = { money: this.money, rep: this.rep, score: this.score, t: 0, stars: Math.floor(this.rep), served: this.served, left: this.left, day: this.day };
    music("theme"); sfx("fanfare");
  }

  update(dt) {
    this.ps.update(dt);
    this.toasts.forEach((t) => { t.life -= dt; t.oy -= dt * 16; }); this.toasts = this.toasts.filter((t) => t.life > 0);
    if (this.repFlash > 0) this.repFlash -= dt;
    if (this.result) { this.result.t += dt; if (input.hit("restart")) this.onEnd({ restart: true }); else if (this.result.t > 0.8 && input.any()) this.onEnd(this.result); return; }

    if (this.menuOpen) { this.updateMenu(); return; }
    const t = this.t, p = this.p;
    let [mx, mz] = input.axis(); mz = -mz; // screen down = -z
    if (mx || mz) { const n = Math.hypot(mx, mz) || 1; mx /= n; mz /= n; this.started = true; this.hintT = 0; }
    p.vx = lerp(p.vx, mx * t.walk_speed, 0.25); p.vz = lerp(p.vz, mz * t.walk_speed, 0.25);
    p.x = clamp(p.x + p.vx * dt, 0.5, t.bounds.x[1] - 0.5);
    p.z = clamp(p.z + p.vz * dt, 0.5, t.bounds.z[1] - 0.5);
    if (Math.abs(mx) > 0.01) p.face = mx > 0 ? 1 : -1;
    p.walk = (mx || mz) ? p.walk + dt : 0;

    if (input.hit("interact")) this.interact();
    if (input.hit("restart")) this.onEnd({ restart: true });

    // stoves
    for (const s of this.stoves) { if (s.state === "cooking") { s.cook -= dt; if (s.cook <= 0) { s.state = "ready"; s.pop = 0.4; sfx("ding"); this.toast(s.pos[0], s.pos[1] + 1, "Chín rồi!", "#79c75a"); } } if (s.pop > 0) s.pop -= dt; }
    // customers
    this.nextCust -= dt;
    if (this.nextCust <= 0 && this.customers.filter((c) => c.state === "waiting").length < this.tables.length) { this.spawnCustomer(); this.nextCust = t.customer_interval_s; }
    for (const cu of this.customers) {
      if (cu.enter < 1) cu.enter = Math.min(1, cu.enter + dt * 2);
      if (cu.state === "waiting") { cu.patience -= dt; if (cu.patience <= 0) this.leave(cu); }
      else if (cu.state === "eating") { cu.eat -= dt; if (cu.eat <= 0) { cu.state = "done"; this.toast(cu.x, cu.z + 1, "Ngon! 😋", "#79c75a"); } }
    }
    this.customers = this.customers.filter((c) => (c.state !== "gone" && c.state !== "done") || (c.fade = (c.fade || 1) - dt) > 0);

    this.time -= dt;
    this.score = this.money + 100 * Math.floor(this.rep);
    if (this.time <= 0) { this.time = 0; this.endRun(); }
    if (this.hintT > 0) this.hintT -= dt;
  }
  updateMenu() {
    const keys = Object.keys(this.menu);
    if (input.hit("up")) { this.menuSel = (this.menuSel + keys.length - 1) % keys.length; sfx("click"); }
    if (input.hit("down")) { this.menuSel = (this.menuSel + 1) % keys.length; sfx("click"); }
    if (input.hit("back")) { this.menuOpen = false; sfx("click"); }
    if (input.hit("interact") || input.hit("confirm")) this.cook(keys[this.menuSel]);
  }

  // transforms
  _scale() { return Math.min((W - 40) / this.t.bounds.x[1], (H - 76) / this.t.bounds.z[1]); }
  _ox() { return (W - this.t.bounds.x[1] * this._scale()) / 2; }
  _oy() { return 46; }
  _sx(x) { return this._ox() + x * this._scale(); }
  _sy(z) { return this._oy() + (this.t.bounds.z[1] - z) * this._scale(); }

  draw() {
    const c = screen.px, time = performance.now() / 1000, sc = this._scale();
    const ox = this._ox(), oy = this._oy(), w = this.t.bounds.x[1] * sc, h = this.t.bounds.z[1] * sc;
    // night water around the raft
    c.fillStyle = "#0a1428"; c.fillRect(0, 0, W, H);
    for (let i = 0; i < 40; i++) { const x = (i * 53 + time * 6) % W, y = (i * 71) % H; R(c, x, y, 1, 1, "rgba(120,160,220,.15)"); }
    for (let i = 0; i < 6; i++) ripple(c, (i * 97 + 40) % W, (i * 61 + 30) % H, time, i);
    // raft shadow + deck
    c.fillStyle = "rgba(0,0,0,.35)"; c.fillRect(ox - 6, oy - 4, w + 12, h + 12);
    planks(c, ox, oy, w, h);
    c.strokeStyle = P.woodD; c.lineWidth = 3; c.strokeRect(ox, oy, w, h);
    // string of lanterns along the top
    R(c, ox, oy - 2, w, 1, "#2a1a12");
    for (let i = 0; i <= 6; i++) lantern(c, ox + 6 + i * (w - 12) / 6, oy + 1, time, i % 2 ? P.red : P.orange);
    c.fillStyle = "rgba(255,180,90,.06)"; c.fillRect(ox, oy, w, h);

    // depth-sorted entities
    const ents = [];
    for (const s of this.stoves) ents.push({ z: s.pos[1], draw: () => this.drawStove(c, s, time) });
    for (const tb of this.tables) ents.push({ z: tb.pos[1], draw: () => this.drawTable(c, tb, time) });
    for (const cu of this.customers) ents.push({ z: cu.z - 0.1, draw: () => this.drawCustomer(c, cu, time) });
    ents.push({ z: this.p.z, draw: () => this.drawPlayer(c, time) });
    ents.sort((a, b) => b.z - a.z);
    ents.forEach((e) => e.draw());
    this.ps.draw(c, 0, 0);

    // toasts
    this.toasts.forEach((t) => txt(t.txt, this._sx(t.x), this._sy(t.z) - 18 + t.oy, { size: 9, align: "center", color: t.col, weight: 900, stroke: "#1a1220", sw: 2.5, alpha: clamp(t.life, 0, 1) }));

    this.drawHUD(c, time);
    if (this.menuOpen) this.drawMenu(c, time);
    if (this.result) this.drawResult(c, time);
    else if (this.hintT > 0 && !this.started) this.drawHint(c);
  }
  drawStove(c, s, time) {
    const x = this._sx(s.pos[0]), y = this._sy(s.pos[1]);
    if (s.pop > 0) { c.save(); c.translate(x, y); const k = 1 + s.pop * 0.3; c.scale(k, k); c.translate(-x, -y); }
    stove(c, x, y, s.state, time);
    if (s.pop > 0) c.restore();
    if (s.state === "cooking") { const fr = 1 - s.cook / s.cookMax; this.ring(c, x, y - 18, fr, "#ff8a3d"); txt(Math.ceil(s.cook) + "s", x, y - 15, { size: 7, align: "center", color: "#fff", weight: 900 }); }
    if (s.state === "ready") { c.drawImage(dishIcon(s.dish), x - 8, y - 26 + Math.round(Math.sin(time * 4)), 16, 16); txt("E", x + 11, y - 18, { size: 8, align: "center", color: "#79c75a", weight: 900, stroke: "#1a1220", sw: 2 }); }
    const near = this.nearStove() === s && !this.menuOpen;
    if (near && s.state === "idle" && !this.hand) txt("E: Nấu", x, y + 16, { size: 8, align: "center", color: "#ffd23a", weight: 900, stroke: "#1a1220", sw: 2 });
  }
  drawTable(c, tb, time) { table(c, this._sx(tb.pos[0]), this._sy(tb.pos[1])); }
  drawCustomer(c, cu, time) {
    const x = this._sx(cu.x), y = this._sy(cu.z) - this._scale() * 1.4;
    const alpha = (cu.fade ?? 1) * cu.enter, type = cu.type || "quen", ty = CUST_TYPES[type];
    c.save(); c.globalAlpha = alpha;
    const yy = y - (1 - cu.enter) * 14;
    // impatient customers fidget while waiting
    const jig = type === "voi" && cu.state === "waiting" ? Math.round(Math.sin(time * 14)) : 0;
    chibi(c, x + jig, yy, { shirt: cu.shirt || "#3a6fd8", hair: cu.hair || "#2a1d2b", hat: !!cu.hat, portrait: cu.portrait });
    if (type === "sop") { R(c, x - 2 + jig, yy - 9, 4, 1, "#ffe9a0"); R(c, x - 1 + jig, yy - 8, 2, 1, "#e0a21a"); } // gold collar / chain
    // thought bubble with wanted dish, tinted by customer type
    if (cu.state === "waiting") {
      const bx = x + 12, by = yy - 22;
      c.fillStyle = ty.bubble; c.beginPath(); c.arc(bx, by, 10, 0, TAU); c.fill();
      R(c, x + 4, yy - 12, 2, 2, ty.bubble); R(c, x + 7, yy - 16, 3, 3, ty.bubble);
      c.imageSmoothingEnabled = false; c.drawImage(dishIcon(cu.want), bx - 8, by - 8, 16, 16);
      if (type !== "quen") pixIcon(c, type, bx - 12, by - 12); // type mark on the bubble's corner
      // patience ring: fraction of THIS customer's own max patience
      const fr = cu.patience / (cu.patienceMax || this.t.patience_s);
      this.ring(c, bx, by, fr, fr < 0.3 ? "#ff5a5a" : fr < 0.6 ? "#ffd23a" : "#79c75a", 11);
      if (fr < 0.3 && Math.floor(time * 6) % 2) txt("!", x - 10, yy - 14, { size: 11, color: "#ff5a5a", weight: 900 });
      txt(this.payFor(cu) + "k", bx + 13, by + 3, { size: 7, color: ty.col, weight: 900, stroke: "#1a1220", sw: 2, alpha });
    } else if (cu.state === "eating") { c.drawImage(dishIcon(cu.want), x - 8, yy - 6, 10, 10); txt(Math.floor(time * 3) % 2 ? "😋" : "😊", x + 8, yy - 10, { size: 9 }); }
    c.restore();
    this.drawBadge(cu, x + jig, yy, alpha);
  }
  // type badge above the customer's head (UI layer): pixel icon + short label
  drawBadge(cu, x, yy, alpha) {
    if (alpha <= 0.05) return;
    const type = cu.type || "quen", ty = CUST_TYPES[type], u = screen.ui;
    const tw = measure(ty.badge, 7, 900), w = Math.ceil(tw) + 13, h = 10;
    const bx = Math.round(x - w), by = Math.round(yy - (cu.hat ? 35 : 31)); // left of the order bubble, clear of the nón lá tip
    panel(bx, by, w, h, { fill: "rgba(12,18,32,.88)", border: ty.col, bw: 1, r: 3, alpha });
    u.save(); u.globalAlpha = alpha; pixIcon(u, type, bx + 3, by + 2); u.restore();
    txt(ty.badge, bx + 10, by + 8, { size: 7, color: ty.col, weight: 900, alpha });
  }
  drawPlayer(c, time) {
    const x = this._sx(this.p.x), y = this._sy(this.p.z) - this._scale() * 0.6;
    chibi(c, x, y, { shirt: P.suit, hair: P.hair, bun: true, apron: true, walk: this.p.walk, carry: this.hand ? this.hand.key : null });
  }
  ring(c, x, y, fr, col, r = 9) { c.strokeStyle = "rgba(0,0,0,.4)"; c.lineWidth = 2; c.beginPath(); c.arc(x, y, r, 0, TAU); c.stroke(); c.strokeStyle = col; c.lineWidth = 1.5; c.beginPath(); c.arc(x, y, r, -Math.PI / 2, -Math.PI / 2 + TAU * fr); c.stroke(); }

  drawHUD(c, time) {
    const u = screen.ui;
    const mm = Math.floor(Math.ceil(this.time) / 60), ss = Math.ceil(this.time) % 60, low = this.time < 20;
    panel(W / 2 - 24, 4, 48, 15, { fill: "rgba(8,20,38,.8)", border: low ? "#ff6b6b" : "#f3d27a", r: 7 });
    txt(`${mm}:${String(ss).padStart(2, "0")}`, W / 2, 15, { size: 11, align: "center", color: low ? "#ff8a8a" : "#fff", weight: 900 });
    panel(W / 2 - 22, 21, 44, 11, { fill: "rgba(8,20,38,.8)", border: "#2a5a7a", r: 5 });
    txt("Ngày " + this.day, W / 2, 29.5, { size: 7.5, align: "center", color: "#ffd23a", weight: 900 });
    // shift tally: served / walked out
    panel(6, 40, 70, 13, { fill: "rgba(8,20,38,.8)", border: "#2a5a7a", r: 5 });
    txt("Phục vụ " + this.served, 11, 49.5, { size: 7, color: "#9fe8a0", weight: 900 });
    txt("Bỏ " + this.left, 71, 49.5, { size: 7, align: "right", color: this.left ? "#ff8a8a" : "#9fb3c0", weight: 900 });
    // money
    panel(6, 5, 70, 15, { fill: "rgba(8,20,38,.8)", border: "#f3d27a", r: 6 });
    txt("🪙", 12, 16, { size: 9 }); txt(this.money + "k", 72, 16, { size: 11, align: "right", color: "#ffe14d", weight: 900 });
    // reputation stars
    const rx = 6, ry = 23;
    panel(rx, ry, 92, 14, { fill: "rgba(8,20,38,.8)", border: this.repFlash > 0 ? "#fff" : "#2a5a7a", r: 6 });
    for (let i = 0; i < 5; i++) { const full = this.rep >= i + 0.75, half = this.rep >= i + 0.25 && !full; this.star(u, rx + 10 + i * 15, ry + 7, full ? 1 : half ? 0.5 : 0, time, i); }
    txt(this.rep.toFixed(1), rx + 88, ry + 11, { size: 8, align: "right", color: "#fff", weight: 900 });
    // stock chips
    const keys = Object.keys(this.stock).filter((k) => this.stock[k] > 0);
    const sw2 = 30, sx0 = W - 6 - keys.length * sw2;
    keys.forEach((k, i) => { const x = sx0 + i * sw2; panel(x, 5, sw2 - 2, 15, { fill: "rgba(8,20,38,.8)", border: "#2a5a7a", r: 4 }); u.imageSmoothingEnabled = false; u.drawImage(icon(k), x + 2, 7, 10, 10); txt("×" + this.stock[k], x + sw2 - 4, 16, { size: 8, align: "right", color: "#cfe", weight: 900 }); });
    // hand indicator
    if (this.hand) { panel(W - 92, 23, 86, 14, { fill: "rgba(40,20,10,.85)", border: "#ff8a3d", r: 6 }); txt("Đang bưng: " + DISH_NAME[this.hand.key], W - 88, 33, { size: 7, color: "#ffd0a0", weight: 800 }); }
    txt("WASD đi · E nấu/bưng/phục vụ", W / 2, H - 5, { size: 7, align: "center", color: "rgba(255,255,255,.5)", weight: 700 });
  }
  star(u, x, y, fill, time, i) {
    u.save(); u.translate(x, y);
    const pop = this.repFlash > 0 ? 1 + Math.sin(time * 20) * 0.1 : 1; u.scale(pop, pop);
    u.beginPath();
    for (let k = 0; k < 10; k++) { const r = k % 2 ? 2 : 5, a = -Math.PI / 2 + k * Math.PI / 5; u[k ? "lineTo" : "moveTo"](Math.cos(a) * r, Math.sin(a) * r); }
    u.closePath();
    u.fillStyle = fill >= 1 ? "#ffd23a" : fill > 0 ? "#ffd23a" : "rgba(255,255,255,.15)";
    if (fill === 0.5) { u.save(); u.clip(); u.fillRect(-6, -6, 6, 12); u.fillStyle = "#ffd23a"; u.fillRect(-6, -6, 6, 12); u.restore(); } else u.fill();
    u.lineWidth = 0.6; u.strokeStyle = "rgba(0,0,0,.5)"; u.stroke();
    u.restore();
  }
  drawMenu(c, time) {
    c.fillStyle = "rgba(4,10,22,.6)"; c.fillRect(0, 0, W, H);
    const keys = Object.keys(this.menu), rowH = 34, pw = 240, ph = 26 + keys.length * rowH;
    const px = W / 2 - pw / 2, py = H / 2 - ph / 2;
    panel(px, py, pw, ph, { fill: "rgba(12,22,40,.96)", border: "#f3d27a", bw: 1.5, r: 6 });
    txt("CHỌN MÓN NẤU", W / 2, py + 15, { size: 11, align: "center", color: "#ffd23a", weight: 900 });
    if (this.cookMul !== 1) txt("Bếp ×" + this.cookMul, px + pw - 8, py + 14, { size: 7, align: "right", color: this.cookMul < 1 ? "#7ee87e" : "#ff9a9a", weight: 900 });
    keys.forEach((k, i) => {
      const y = py + 24 + i * rowH, m = this.menu[k], sel = i === this.menuSel, can = this.canCook(k);
      if (sel) panel(px + 5, y, pw - 10, rowH - 4, { fill: can ? "rgba(255,210,100,.18)" : "rgba(255,80,80,.14)", border: can ? "#ffd23a" : "#ff6b6b", r: 4 });
      screen.ui.imageSmoothingEnabled = false; screen.ui.drawImage(dishIcon(k), px + 12, y + 2, 18, 18);
      txt(DISH_NAME[k], px + 36, y + 11, { size: 9, color: can ? "#fff" : "#ff9a9a", weight: 800 });
      const rec = Object.entries(m.recipe).map(([ik, n]) => `${KIND_NAME[ik]}×${n}`).join(" + ");
      txt(rec, px + 36, y + 22, { size: 7, color: can ? "#9fb3c0" : "#d98", weight: 700 });
      txt(m.price + "k", px + pw - 12, y + 11, { size: 10, align: "right", color: "#ffe14d", weight: 900 });
      const eff = this.cookTime(k);
      if (eff !== m.cook_s) { // upgraded stove: effective time, base time dimmed beside it
        txt(fmtS(eff), px + pw - 12, y + 22, { size: 7, align: "right", color: "#7ee87e", weight: 900 });
        txt(fmtS(m.cook_s) + " →", px + pw - 12 - measure(fmtS(eff), 7, 900) - 3, y + 22, { size: 6.5, align: "right", color: "rgba(159,179,192,.6)", weight: 700 });
      } else txt(fmtS(m.cook_s), px + pw - 12, y + 22, { size: 7, align: "right", color: "#9fb3c0", weight: 700 });
    });
    txt("↑↓ chọn · E nấu · Esc huỷ", W / 2, py + ph - 6, { size: 7, align: "center", color: "rgba(255,255,255,.6)", weight: 700 });
  }
  drawHint(c) {
    const a = clamp(this.hintT, 0, 1);
    panel(W / 2 - 96, H / 2 - 18, 192, 36, { fill: `rgba(8,18,34,${0.85 * a})`, border: "#f3d27a", r: 6, alpha: a });
    txt("Tới bếp (E) nấu món khách muốn, rồi bưng ra bàn", W / 2, H / 2 - 2, { size: 8.5, align: "center", color: "#fff", weight: 800, alpha: a });
    txt("Khách bỏ đi = mất uy tín!", W / 2, H / 2 + 11, { size: 8, align: "center", color: "#ffd23a", weight: 700, alpha: a });
  }
  drawResult(c, time) {
    const r = this.result, k = clamp(r.t / 0.5, 0, 1);
    c.fillStyle = `rgba(4,10,22,${0.75 * k})`; c.fillRect(0, 0, W, H);
    if (r.t < 1.4) speedLines(c, W / 2, H / 2 - 20, time, "rgba(255,220,120,.12)");
    txt("HẾT BUỔI TỐI!", W / 2, H / 2 - 44, { size: 24 * lerp(1.5, 1, k), align: "center", color: "#ffd23a", weight: 900, italic: true, stroke: "#1a1220", sw: 5, rot: -0.03 });
    panel(W / 2 - 90, H / 2 - 30, 180, 76, { fill: "rgba(8,20,38,.92)", border: "#f3d27a", r: 5 });
    panel(W / 2 - 22, H / 2 - 36, 44, 11, { fill: "rgba(8,20,38,1)", border: "#f3d27a", r: 5 }); // day tab on the panel's top edge
    txt("Ngày " + (r.day ?? this.day), W / 2, H / 2 - 27.5, { size: 7.5, align: "center", color: "#ffd23a", weight: 900 });
    txt("Doanh thu", W / 2 - 80, H / 2 - 16, { size: 9, color: "#cfe", weight: 700 });
    txt(Math.floor(r.money * clamp(r.t, 0, 1)) + "k", W / 2 + 80, H / 2 - 16, { size: 11, align: "right", color: "#ffe14d", weight: 900 });
    txt("Khách", W / 2 - 80, H / 2 - 2, { size: 9, color: "#cfe", weight: 700 });
    txt("phục vụ " + r.served, W / 2 + 20, H / 2 - 2, { size: 9, align: "right", color: "#9fe8a0", weight: 900 });
    txt("bỏ đi " + r.left, W / 2 + 80, H / 2 - 2, { size: 9, align: "right", color: r.left ? "#ff8a8a" : "#9fb3c0", weight: 900 });
    txt("Uy tín", W / 2 - 80, H / 2 + 13, { size: 9, color: "#cfe", weight: 700 });
    const u = screen.ui; for (let i = 0; i < 5; i++) this.star(u, W / 2 - 6 + i * 13, H / 2 + 9, i < r.stars ? 1 : 0, time, i);
    R(c, W / 2 - 82, H / 2 + 22, 164, 1, "rgba(255,255,255,.2)");
    txt("ĐIỂM", W / 2 - 80, H / 2 + 37, { size: 10, color: "#fff", weight: 900 });
    txt("" + Math.floor(r.score * clamp(r.t * 0.8, 0, 1)), W / 2 + 80, H / 2 + 37, { size: 14, align: "right", color: "#7ee87e", weight: 900 });
    if (r.t > 1) txt(Math.floor(r.t * 2) % 2 ? "Enter: chơi lại từ đầu   ·   R: làm lại buổi tối" : "", W / 2, H - 20, { size: 9, align: "center", color: "#fff", weight: 900 });
  }
}
