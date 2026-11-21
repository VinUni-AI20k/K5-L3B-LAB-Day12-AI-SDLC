// GATHER scene — GUI ONLY. Local mock physics so it's playable now; swap `st` for the server snapshot later.
// World units: x in [0,100], d (depth) in [0,30], d=0 is the surface. Camera follows the diver on x.
// Core rules mirrored from Test Contract v1.1 (numbers from tuning.gather): swimming fish schools + scheduled
// spawns, Cá Sấu Năm Chèo (croc.js), HP / faint, oxygen / choke, docking, the day's NEEDED list.
// Sáng tạo (creative extras, never change the core numbers above): harpoon aiming, sprint, deep zone 30–60 m
// with big fish (deep.js), water snakes (creatures.js).
import { W, H, screen, input, clamp, lerp, fx, Particles, txt, panel, measure, reduceMotion } from "./engine.js";
import { sfx, music } from "./audio.js";
import { P, R, bands, sky, sun, cloud, bank, hyacinth, godRays, kelp, rock, WATER, diver, fish, nodeArt, dock, KIND_NAME, icon } from "./art.js";
import { speedLines } from "./cutscene.js";
import { DEEP, preloadDeep, makeDeepFish, updateDeepFish, drawDeepFish, drawDeepScenery } from "./deep.js";
import { SNAKE, makeSnakes, updateSnakes, drawSnake, snakeInReach, stunSnake } from "./creatures.js";
import { stats, recordCatch, save } from "./progress.js";
import { makeCrocs, updateCrocs, crocHit, startRecoil, crocNear, drawCroc } from "./croc.js";

const VS = 10; // vertical px per metre (camera scrolls with depth)

const TAU = Math.PI * 2;

export class GatherScene {
  // opts.day: campaign day (monster from_day filter; standalone = 1); opts.need: { kind: count } from day_plan
  constructor(contract, onEnd, opts = {}) {
    this.t = contract.tuning.gather; this.menu = contract.tuning.menu; this.onEnd = onEnd;
    this.hz = contract.tuning.tick_hz || 60; this.day = opts.day || 1; this.need = opts.need || null;
    const t = this.t;
    this.p = { x: t.start_pos[0], d: 0, vx: 0, vd: 0, heading: 0, face: 1, phase: 0 };
    // harpoon (GUI creative layer): aim with movement or the mouse, Space/click fires a spear on a rope
    this.aim = 0; this.tilt = 0; this.harp = null; this.mouseT = -1; this.mouse = { x: 0, y: 0 };
    this._onMove = (e) => { const r = screen.pc.getBoundingClientRect(); this.mouse.x = (e.clientX - r.left) / r.width * W; this.mouse.y = (e.clientY - r.top) / r.height * H; this.mouseT = performance.now(); };
    addEventListener("pointermove", this._onMove); addEventListener("pointerdown", this._onMove);
    // effective tuning = contract base + shop upgrades (progress.js); a fresh save gives exactly the contract values
    const st = this.stats = stats(contract);
    this.oxyMax = st.oxygenMax; this.oxy = st.oxygenMax;
    this.swim = st.swimSpeed; this.catchR = st.catchRadius;
    this.hpMax = st.hpMax ?? t.hp_max; this.hp = this.hpMax;
    this.hold = []; this.cap = st.holdCap;
    this.time = t.duration_s; this.invuln = 0; this.catchCd = 0; this.zeroOxy = 0;
    this.nodes = t.nodes.map((n) => ({ ...n, ready: true, regrow: 0, pop: 0 }));
    // v1.0: fish_initial is a list of schools; v1.1: a count, placed on distinct standard spawn points
    const init = Array.isArray(t.fish_initial) ? t.fish_initial : (() => {
      const pts = []; for (const [kind, ds] of Object.entries(t.fish_spawn_depths || {})) for (const x of t.fish_spawn_x || []) for (const d of ds) pts.push({ kind, pos: [x, d] });
      const out = [], used = new Set(); let k = 0;
      while (out.length < Math.min(t.fish_initial, pts.length) && k < 500) { const q = pts[Math.floor(Math.random() * pts.length)]; const key = q.pos.join(","); k++; if (used.has(key)) continue; used.add(key); out.push({ id: "F" + (out.length + 1), ...q }); }
      return out; })();
    this.fishSeq = 0;
    this.fish = init.map((f) => this.newSchool(f.kind, f.pos[0], f.pos[1]));
    this.spawnT = 0;
    // Cá Sấu Năm Chèo: M1 from day 1, M2 only from_day 3 (standalone gather = day-1 layout)
    this.mon = t.monsters || null; this.crocs = makeCrocs(this.mon, this.day); this.crocWarn = 0;
    this.yield = t.fish_yield || {};
    // creative extension: the client river goes deeper than the contract (see deep.js)
    this.maxD = Math.max(t.bounds.d[1], DEEP.depth); preloadDeep(); this.deep = makeDeepFish(); this.camY = 0; this.deepSeen = false;
    // aggressive creature (creatures.js); env is reused every frame (no per-frame allocation)
    this.snakes = makeSnakes(DEEP.zone); this.snakeSeen = !!save.catalog[SNAKE.id];
    this.snakeEnv = { px: 0, pd: 0, underwater: false, swim: this.swim, deepZone: DEEP.zone, maxD: this.maxD, maxX: t.bounds.x[1], sx: W / 26, sy: VS,
      bite: (s, nx, nd) => this.snakeBite(s, nx, nd), seen: () => this.onSnakeSeen() };
    this.cam = t.start_pos[0]; this.ps = new Particles(); this.psUI = new Particles();
    this.toasts = []; this.ended = false; this.hintT = 4; this.danger = 0; this.flashHurt = 0;
    this.score = 0; this.result = null; this.started = false; this.dockPulse = 0;
    music("underwater");
  }
  worth(kind) { // rough value of a caught item, for the end tally
    for (const m of Object.values(this.menu)) if (m.recipe[kind]) return m.price / (Object.values(m.recipe).reduce((a, b) => a + b, 0));
    return 10;
  }
  // swimming school (v1.1): fish_speed along a random heading, re-rolled every fish_turn_ticks, reflected at edges
  newSchool(kind, x, d) {
    const f = { id: "F" + (++this.fishSeq), kind, x, d, face: 1, caught: false, phase: Math.random() * 6, vx: 1, vd: 0, turn: (this.t.fish_turn_ticks || 120) / this.hz };
    this.heading(f); return f;
  }
  heading(f) { const a = Math.random() * TAU; f.vx = Math.cos(a); f.vd = Math.sin(a); f.face = f.vx >= 0 ? 1 : -1; }
  swimFish(dt) {
    const t = this.t, sp = t.fish_speed ?? 0, fx0 = t.fish_x || [1, t.bounds.x[1] - 1], turnS = (t.fish_turn_ticks || 120) / this.hz;
    for (const f of this.fish) {
      if (f.caught || f.hooked) continue;
      f.phase += dt; f.turn -= dt;
      if (f.turn <= 0) { f.turn += turnS; this.heading(f); }
      const band = (t.fish_depths || {})[f.kind] || [1, t.bounds.d[1] - 1];
      let nx = f.x + f.vx * sp * dt, nd = f.d + f.vd * sp * dt;
      if (nx < fx0[0]) { nx = 2 * fx0[0] - nx; f.vx = -f.vx; } else if (nx > fx0[1]) { nx = 2 * fx0[1] - nx; f.vx = -f.vx; }
      if (nd < band[0]) { nd = 2 * band[0] - nd; f.vd = -f.vd; } else if (nd > band[1]) { nd = 2 * band[1] - nd; f.vd = -f.vd; }
      f.x = Math.max(fx0[0], Math.min(fx0[1], nx)); f.d = Math.max(band[0], Math.min(band[1], nd));
      if (Math.abs(f.vx) > 0.05) f.face = f.vx > 0 ? 1 : -1;
    }
    // scheduled spawn: every fish_spawn_ticks, at most one school, under fish_max, clearance from every live school
    if (!t.fish_spawn_ticks) return;
    this.spawnT += dt;
    if (this.spawnT < t.fish_spawn_ticks / this.hz) return;
    this.spawnT -= t.fish_spawn_ticks / this.hz;
    const alive = this.fish.filter((f) => !f.caught);
    if (alive.length >= (t.fish_max ?? 12)) return;
    const clear = t.fish_spawn_clearance ?? 1, ok = {};
    for (const [kind, ds] of Object.entries(t.fish_spawn_depths || {})) {
      const pts = []; for (const x of t.fish_spawn_x || []) for (const d of ds) if (alive.every((f) => Math.hypot(f.x - x, f.d - d) > clear)) pts.push([x, d]);
      if (pts.length) ok[kind] = pts;
    }
    const kinds = Object.keys(ok); if (!kinds.length) return; // no free point: skip this turn
    const wts = kinds.map((k) => (t.fish_weights || {})[k] ?? 1), sum = wts.reduce((a, b) => a + b, 0);
    let r = Math.random() * sum, kind = kinds[kinds.length - 1];
    for (let i = 0; i < kinds.length; i++) { r -= wts[i]; if (r < 0) { kind = kinds[i]; break; } }
    const pt = ok[kind][Math.floor(Math.random() * ok[kind].length)];
    this.fish.push(this.newSchool(kind, pt[0], pt[1]));
  }
  crocBite(m) {
    const p = this.p, ratio = this.mon.loss_ratio ?? 0.5;
    const lose = Math.floor(this.hold.length * ratio), lost = lose ? this.hold.splice(this.hold.length - lose, lose) : []; // LIFO
    startRecoil(m, p.x, p.d, this.hz);
    this.toast("Cá Sấu Năm Chèo cắn! −1 Máu", "#ff6b6b");
    if (lost.length) { const by = {}; for (const k of lost) by[k] = (by[k] || 0) + 1; this.toast("Rơi mất: " + Object.entries(by).map(([k, n]) => KIND_NAME[k] + " ×" + n).join(", "), "#ffb36b"); }
    sfx("slam"); fx.shake(7, 0.45);
    this.hurt("croc");
  }
  toast(txt, col) { this.toasts.push({ txt, col, life: 1.6, y: 0 }); }
  nearestNode() { let best = null, bd = 1e9; for (const n of this.nodes) { if (!n.ready) continue; const dx = n.pos[0] - this.p.x, dd = (0) - this.p.d; const r = Math.hypot(dx, dd); if (r < bd) { bd = r; best = n; } } return bd <= this.t.interact_radius ? best : null; }
  // reach = upgraded catch radius; big deep fish keep their larger body radius plus the same net bonus
  nearestFish() { const cr = this.catchR, bonus = cr - this.t.catch_radius; let best = null, bd = 1e9; for (const f of [...this.fish, ...this.deep]) { if (f.caught) continue; const r = Math.hypot(f.x - this.p.x, f.d - this.p.d) - (f.sp ? Math.max(cr, f.sp.radius + bonus) : cr); if (r < bd) { bd = r; best = f; } } return bd <= 0 ? best : null; }
  atDock() { return Math.hypot(this.p.x - this.t.dock_pos[0], this.p.d - this.t.dock_pos[1]) <= this.t.dock_radius; }

  endRun(reason) {
    if (this.ended) return; this.ended = true;
    removeEventListener("pointermove", this._onMove); removeEventListener("pointerdown", this._onMove);
    if (this.harp?.hit) this.harp.hit.hooked = false; this.harp = null;
    if (reason === "fainted") this.hold = [];
    let val = 0; const by = {}; for (const k of this.hold) { by[k] = (by[k] || 0) + 1; val += this.worth(k); }
    this.result = { reason, by, val: Math.round(val), t: 0 };
    music(reason === "fainted" ? "theme" : "theme");
    sfx(reason === "fainted" ? "hurt" : "ding");
    if (reason !== "fainted") sfx("fanfare");
  }

  // kind: "choke" (goes through invulnerability, sets none), "croc" (invuln_ticks), "snake" (creative, 1.2 s)
  hurt(kind = "snake") {
    if (kind !== "choke" && this.invuln > 0) return;
    this.hp--; this.flashHurt = 0.4;
    if (kind === "croc") this.invuln = (this.mon?.invuln_ticks ?? 90) / this.hz; else if (kind === "snake") this.invuln = 1.2;
    fx.shake(5, 0.4); fx.flash("rgba(220,60,60,.5)", 0.2); sfx("hurt");
    this.toast("-1 ♥", "#ff6b6b");
    if (this.hp <= 0) this.endRun("fainted");
  }

  snakeBite(s, nx, nd) {
    const p = this.p;
    this.hurt(); fx.shake(4, 0.3); sfx("slam");
    this.toast(SNAKE.name + " cắn!", "#ff9a5a");
    p.x = clamp(p.x + nx * SNAKE.push, 0, this.t.bounds.x[1]); p.d = clamp(p.d + nd * SNAKE.push, this.t.surface_depth + 0.1, this.maxD);
    p.vx = nx * this.swim * 2; p.vd = nd * this.swim * 2;
    const sx = this._sx(p.x), sy = this._sy(p.d);
    for (let i = 0; i < 6; i++) this.ps.add({ x: sx, y: sy, vx: (Math.random() - .5) * 50, vy: (Math.random() - .5) * 50, size: 1, life: 0.35, color: "#ff8a8a" });
  }
  onSnakeSeen() {
    if (this.snakeSeen) return; this.snakeSeen = true;
    if (recordCatch(SNAKE.id, SNAKE.name)) this.discover(SNAKE.name);
    this.toast("Cẩn thận! Rắn nước cắn — Space làm choáng", "#ffb36b");
  }
  discover(name) { this.toast("Mới! Sổ tay: " + name, "#7dffb0"); fx.flash("rgba(160,255,200,.3)", 0.15); sfx("ding"); }

  update(dt) {
    for (const a of [this.ps, this.psUI]) a.update(dt);
    this.toasts.forEach((t) => { t.life -= dt; t.y -= dt * 18; }); this.toasts = this.toasts.filter((t) => t.life > 0);
    if (this.result) { this.result.t += dt; if (input.hit("restart")) this.onEnd({ restart: true }); else if (this.result.t > 0.6 && input.any()) this.onEnd(this.result); return; }

    const t = this.t, p = this.p;
    // --- input / movement (eased velocity) ---
    let [mx, md] = input.axis();
    if (mx || md) { const n = Math.hypot(mx, md) || 1; mx /= n; md /= n; this.started = true; this.hintT = 0; }
    this.sprint = input.down("sprint") && (mx || md) ? 1 : 0;
    const sp = this.swim * (this.sprint ? 1.8 : 1);
    p.vx = lerp(p.vx, mx * sp, 0.18); p.vd = lerp(p.vd, md * sp, 0.18);
    p.x = clamp(p.x + p.vx * dt, 0, t.bounds.x[1]);
    p.d = clamp(p.d + p.vd * dt, 0, this.maxD);
    if (mx || md) { p.heading = Math.atan2(md, mx); if (Math.abs(mx) > 0.01) p.face = mx > 0 ? 1 : -1; }
    // aim (world metres): mouse if it moved in the last 2.5 s, else the swim heading, else straight ahead
    const mouseAim = this.mouseT > 0 && performance.now() - this.mouseT < 2500;
    if (mouseAim) { const wx = this.cam + (this.mouse.x - W / 2) / this._scale(), wd = (this.mouse.y - this._surfaceY()) / VS; this.aim = Math.atan2(wd - p.d, wx - p.x); if (!(mx || md)) p.face = Math.cos(this.aim) >= 0 ? 1 : -1; }
    else if (mx || md) this.aim = p.heading;
    else this.aim = Math.cos(this.aim) * p.face >= 0 ? this.aim : (p.face > 0 ? 0 : Math.PI);
    // body tilt follows the swim direction on screen (or the aim while hovering with the mouse)
    { const vxs = p.vx * this._scale(), vys = p.vd * VS, moving = Math.hypot(p.vx, p.vd) > 0.4;
      let target = 0;
      if (moving) target = Math.atan2(vys, Math.abs(vxs) + 1e-3);
      else if (mouseAim && p.d > t.surface_depth) target = Math.atan2(Math.sin(this.aim) * VS, Math.abs(Math.cos(this.aim)) * this._scale() + 1e-3) * 0.6;
      if (p.d <= t.surface_depth) target = Math.min(target, 0.2);
      this.tilt = lerp(this.tilt, clamp(target, -1.4, 1.4), 0.15); }
    p.phase += dt * (1 + Math.hypot(p.vx, p.vd) * 0.3);
    const underwater = p.d > t.surface_depth;

    // --- oxygen / choke ---
    if (underwater) {
      const deepZone = p.d > DEEP.zone;
      if (deepZone && !this.deepSeen) { this.deepSeen = true; this.toast("Vùng nước sâu! Cá to — O₂ hao ×" + DEEP.pressure, "#9fd8ff"); sfx("whoosh"); }
      this.oxy = clamp(this.oxy - dt * (this.sprint ? 2 : 1) * (deepZone ? DEEP.pressure : 1), 0, this.oxyMax);
      if (this.oxy <= 0) { this.zeroOxy += dt; if (this.zeroOxy >= t.choke_interval_ticks / this.hz) { this.zeroOxy -= t.choke_interval_ticks / this.hz; this.hurt("choke"); if (this.ended) return; } }
      if (Math.random() < 0.3) this.ps.add({ x: this._sx(p.x), y: this._sy(p.d) - 2, vy: -14, g: 0, wobble: 6, seed: Math.random() * 6, size: 1, life: 1.1, color: "rgba(220,245,255,.7)" });
    } else { this.oxy = clamp(this.oxy + t.oxygen_refill_per_tick * dt, 0, this.oxyMax); this.zeroOxy = 0; }
    this.danger = this.oxy < this.oxyMax * 0.25 && underwater ? clamp(this.danger + dt * 2, 0, 1) : clamp(this.danger - dt * 3, 0, 1);
    if (this.danger > 0.5 && Math.floor(this.t_prev || 0) !== Math.floor(this.time)) {}

    if (this.invuln > 0) this.invuln -= dt;
    if (this.catchCd > 0) this.catchCd -= dt;

    // --- Cá Sấu Năm Chèo: move (patrol/chase/recoil), then at most one hit on the nearest ---
    updateCrocs(this.crocs, dt, { px: p.x, pd: p.d, bx: t.bounds.x });
    if (p.d >= 10 && this.invuln <= 0) { const m = crocHit(this.crocs, p.x, p.d); if (m) { this.crocBite(m); if (this.ended) return; } }
    { const n = crocNear(this.crocs, p.x, p.d); this.crocWarn = n && n.dist <= n.m.sp.detect_radius ? Math.min(1, this.crocWarn + dt * 4) : Math.max(0, this.crocWarn - dt * 3); }
    // --- fish schools swim + scheduled spawns (v1.1) ---
    this.swimFish(dt);
    updateDeepFish(this.deep.filter((f) => !f.hooked), dt, this.maxD);
    { const e = this.snakeEnv; e.px = p.x; e.pd = p.d; e.underwater = underwater; updateSnakes(this.snakes, dt, e); }
    // --- node regrow ---
    for (const n of this.nodes) { if (!n.ready) { n.regrow -= dt; if (n.regrow <= 0) { n.ready = true; this.toast(KIND_NAME[n.kind] + " mọc lại", "#79c75a"); } } if (n.pop > 0) n.pop -= dt; }

    // --- actions ---
    if (input.hit("interact")) {
      if (this.atDock() && this.hold.length) { this.endRun("docked"); }
      else { const n = this.nearestNode(); if (n && !underwater && this.hold.length < this.cap) this.pick(n); else if (n && underwater) this.toast("Lên mặt nước để hái", "#ffd23a"); else if (n) { this.toast("Giỏ đầy! Về bến (E)", "#ff8a8a"); sfx("hurt"); } }
    }
    if ((input.hit("catch") || (input.hit("confirm") && this.mouseT > 0)) && underwater && !this.harp && this.catchCd <= 0) this.fire();
    this.updateHarpoon(dt);
    if (input.hit("restart")) this.onEnd({ restart: true });

    // --- timer ---
    this.time -= dt; this.dockPulse += dt;
    if (this.time <= 0) { this.time = 0; this.endRun(this.hold.length ? "timeup" : "timeup_empty"); }

    // --- camera ---
    this.cam = lerp(this.cam, clamp(p.x, W / 2 / this._scale(), t.bounds.x[1] - W / 2 / this._scale()), 0.1);
    const maxCamY = 58 + this.maxD * VS + 14 - H;
    this.camY = lerp(this.camY, clamp(58 + p.d * VS - H * 0.45, 0, maxCamY), 0.12);
    if (this.hintT > 0) this.hintT -= dt;
  }

  harpRange() { return 5 + (this.catchR - this.t.catch_radius) * 2; }
  hitRadius(f) { return f.sp ? f.sp.radius * 0.7 : 1.1; }
  fire() {
    const p = this.p, ax = Math.cos(this.aim), ad = Math.sin(this.aim);
    this.harp = { x: p.x + ax * 0.6, d: p.d + ad * 0.6, ax, ad, dist: 0, state: "out", hit: null };
    sfx("whoosh"); fx.shake(1, 0.08);
  }
  // first catchable thing along the aim ray (for the aim highlight)
  aimTarget() {
    const p = this.p, ax = Math.cos(this.aim), ad = Math.sin(this.aim), R = this.harpRange();
    let best = null, bt = 1e9;
    for (const f of [...this.fish, ...this.deep]) { if (f.caught || f.hooked) continue; const rx = f.x - p.x, rd = f.d - p.d, tt = rx * ax + rd * ad; if (tt < 0 || tt > R + this.hitRadius(f)) continue; const off = Math.abs(rx * ad - rd * ax); if (off <= this.hitRadius(f) && tt < bt) { bt = tt; best = f; } }
    return best;
  }
  updateHarpoon(dt) {
    const h = this.harp; if (!h) return; const p = this.p;
    if (h.state === "out") {
      const step = 24 * dt; h.x += h.ax * step; h.d += h.ad * step; h.dist += step;
      if (h.d < 0) { h.d = 0; h.state = "back"; }
      const sn = snakeInReach(this.snakes, h.x, h.d, 0.4);
      if (sn) { this.stun(sn); h.state = "back"; }
      else for (const f of [...this.fish, ...this.deep]) {
        if (f.caught || f.hooked || Math.hypot(f.x - h.x, f.d - h.d) > this.hitRadius(f)) continue;
        if (this.hold.length + (f.sp ? 1 : this.yield[f.kind] || 1) > this.cap) { this.toast("Giỏ không đủ chỗ cho cả đàn! Về bến (E)", "#ff8a8a"); sfx("hurt"); }
        else { f.hooked = true; h.hit = f; sfx("catch"); fx.hitstop(0.05); fx.shake(f.sp ? 3 : 2, 0.15); }
        h.state = "back"; break;
      }
      if (h.dist >= this.harpRange()) h.state = "back";
      if (h.state === "back" && !h.hit) for (let i = 0; i < 4; i++) this.ps.add({ x: this._sx(h.x), y: this._sy(h.d), vx: (Math.random() - .5) * 30, vy: (Math.random() - .5) * 30, size: 1, life: 0.3, color: "rgba(255,255,255,.5)" });
    } else {
      const dx = p.x - h.x, dd = p.d - h.d, r = Math.hypot(dx, dd), step = (h.hit?.sp ? 11 : 16) * dt;
      if (r <= step + 0.3) { const f = h.hit; this.harp = null; this.catchCd = this.t.catch_cooldown_s; if (f) { f.hooked = false; this.grab(f); } return; }
      h.x += dx / r * step; h.d += dd / r * step;
    }
    if (h.hit) { h.hit.x = h.x; h.hit.d = h.d; }
  }

  pick(n) {
    n.ready = false; n.regrow = this.t.regrow_s; n.pop = 0.4;
    this.hold.push(n.kind); sfx("pick");
    this.toast("+ " + KIND_NAME[n.kind], "#ffd23a");
    fx.flash("rgba(255,220,120,.25)", 0.12);
    const sx = this._sx(n.pos[0]), sy = this._sy(0);
    for (let i = 0; i < 8; i++) this.ps.add({ x: sx, y: sy, vx: (Math.random() - .5) * 40, vy: -20 - Math.random() * 20, g: 60, size: 1 + (i % 2), life: 0.6, color: n.kind === "bong_sung" ? "#ff8fb1" : "#ffd23a" });
  }
  stun(s) {
    stunSnake(s); sfx("slam"); fx.shake(3, 0.2); fx.hitstop(0.04);
    this.toast("Choáng!", "#ffe14d");
    const sx = this._sx(s.x), sy = this._sy(s.d);
    this.ps.add({ x: sx, y: sy, ring: true, size: 3, life: 0.35, color: "#ffe14d", fade: false });
  }
  grab(f) {
    f.caught = true; this.catchCd = this.t.catch_cooldown_s;
    const n = Math.min(f.sp ? f.sp.yield : this.yield[f.kind] || 1, this.cap - this.hold.length);
    if (!f.sp) this.fish = this.fish.filter((x) => x !== f);
    for (let i = 0; i < n; i++) this.hold.push(f.kind);
    sfx("catch"); fx.hitstop(0.05); fx.flash("rgba(180,240,255,.3)", 0.1); fx.shake(2, 0.2);
    if (f.sp) { this.toast(f.sp.name + "!", "#ffe14d"); fx.shake(4, 0.3); }
    this.toast("+ " + KIND_NAME[f.kind] + (n > 1 ? " ×" + n : ""), f.kind === "ca_linh" ? "#d4e8f2" : f.kind === "ca_keo" ? "#c8b89a" : "#8a9a5a");
    // species catalog: contract fish log under their kind, deep fish under their species id
    const name = f.sp ? f.sp.name : KIND_NAME[f.kind].charAt(0).toUpperCase() + KIND_NAME[f.kind].slice(1);
    if (recordCatch(f.sp ? f.sp.id : f.kind, name)) this.discover(name);
    const sx = this._sx(f.x), sy = this._sy(f.d);
    this.ps.add({ x: sx, y: sy, ring: true, size: 2, life: 0.4, color: "#bdefff", fade: false });
    for (let i = 0; i < 10; i++) this.ps.add({ x: sx, y: sy, vx: (Math.random() - .5) * 60, vy: (Math.random() - .5) * 60, size: 1, life: 0.5, color: "#e8fbff" });
  }

  // ---- screen transforms (world -> pixel canvas) ----
  _scale() { return W / 26; }               // show ~26m of river width
  _surfaceY() { return 58 - this.camY; }
  _sx(x) { return (x - this.cam) * this._scale() + W / 2; }
  _sy(d) { return this._surfaceY() + d * VS; }

  draw() {
    const c = screen.px, t = this.t, p = this.p, time = this.t_now = performance.now() / 1000;
    const surY = this._surfaceY(), botY = this._sy(this.maxD);
    const cam = this.cam, sc = this._scale();
    // sky strip
    if (surY > 0) {
      c.save(); c.translate(0, -this.camY);
      sky(c, "day", 0, 58, time);
      sun(c, 360 - cam * 2, 20, 14, "#fff2c0", "rgba(255,210,140,.2)");
      for (let i = 0; i < 4; i++) cloud(c, ((i * 150 - cam * 6 + time * 4) % 600 + 600) % 600 - 60, 14 + (i % 2) * 10, 1, "rgba(255,255,255,.7)");
      bank(c, 57, cam * sc * 0.3, "#6a4d7b", 3, 0.7);
      c.restore();
    }
    // water body
    bands(c, 0, surY, W, botY - surY + 30, WATER, 16);
    godRays(c, cam * sc, surY, botY - surY, time, 0.08);
    // deep zone: darker, colder water below DEEP.zone
    { const zy = this._sy(DEEP.zone); const g = c.createLinearGradient(0, zy - 40, 0, botY); g.addColorStop(0, "rgba(4,10,30,0)"); g.addColorStop(0.25, "rgba(4,10,30,.45)"); g.addColorStop(1, "rgba(2,4,16,.8)"); c.fillStyle = g; c.fillRect(0, zy - 40, W, botY - zy + 40);
      R(c, 0, zy, W, 1, "rgba(140,200,255,.18)"); txt("— VÙNG SÂU · cá to —", W - 6, zy - 2, { size: 7, align: "right", color: "rgba(160,215,255,.55)", weight: 800 }); }
    if (botY > this._sy(DEEP.zone) && this._sy(DEEP.zone) < H) drawDeepScenery(c, W / 2 - cam * sc, surY, sc, VS, time, W, H, kelp, rock);
    // parallax weeds + hyacinth mats
    for (let i = 0; i < 8; i++) { const wx = ((i * 190 + 40) - cam * sc) ; if (wx > -40 && wx < W + 40) hyacinth(c, wx, surY, 24 + (i % 3) * 10, time, i); }
    for (let i = 0; i < 24; i++) { const kx = (i * 46 - cam * sc * 1.1); const mx = ((kx % (W + 60)) + W + 60) % (W + 60) - 30; kelp(c, mx, botY, 24 + (i % 5) * 14, time); }
    c.fillStyle = "#2c2419"; c.fillRect(0, botY - 4, W, H - botY + 8);
    for (let i = 0; i < 10; i++) { const rx = (i * 70 - cam * sc); const mx = ((rx % (W + 80)) + W + 80) % (W + 80) - 40; rock(c, mx, botY - 3, 10 + (i % 3) * 5, 6); }
    // depth guides
    for (let d = 5; d <= this.maxD; d += 5) { const y = this._sy(d); R(c, 0, y, W, 1, "rgba(255,255,255,.05)"); txt(d + "m", 3, y - 1, { size: 7, color: "rgba(255,255,255,.3)", weight: 700 }); }
    // surface shimmer
    R(c, 0, surY, W, 1, "rgba(230,250,255,.85)");
    for (let x = 0; x < W; x += 8) R(c, x + Math.round(Math.sin(time * 2 + x) * 2), surY - 1, 4, 1, "rgba(255,255,255,.5)");

    // dock
    dock(c, this._sx(t.dock_pos[0]), surY, time);
    if (this.hold.length && this.atDock()) { const pz = 0.5 + 0.5 * Math.sin(this.dockPulse * 6); txt("E: Cập bến ↑", this._sx(t.dock_pos[0]), surY - 26, { size: 8, align: "center", color: "#ffe14d", weight: 900, alpha: 0.6 + pz * 0.4, stroke: "#1a1220", sw: 2 }); }

    // nodes
    for (const n of this.nodes) { const x = this._sx(n.pos[0]); if (x < -20 || x > W + 20) continue; const near = !(p.d > t.surface_depth) && Math.hypot(n.pos[0] - p.x, p.d) <= t.interact_radius && n.ready; nodeArt(c, n.kind, x, surY, time, n.ready); if (near && this.hold.length < this.cap) txt("E: hái", x, surY - 26, { size: 8, align: "center", color: "#ffd23a", weight: 900, stroke: "#1a1220", sw: 2 }); }

    // fish
    for (const f of this.fish) { if (f.caught) continue; const x = this._sx(f.x), y = this._sy(f.d); if (x < -20 || x > W + 20 || y < -20 || y > H + 20) continue; fish(c, f.kind, x, y, f.face, time + f.phase, f.kind === "ca_loc" ? 1 : 1); }
    for (const f of this.deep) { if (f.caught) continue; const x = this._sx(f.x), y = this._sy(f.d); if (x < -60 || x > W + 60 || y < -40 || y > H + 40) continue; drawDeepFish(c, f, x, y, time + f.phase); }

    for (const s of this.snakes) drawSnake(c, s, W / 2 - cam * sc, surY, sc, VS, time);
    for (const m of this.crocs) { const x = this._sx(m.x), y = this._sy(m.d); if (x > -60 && x < W + 60 && y > -30 && y < H + 30) drawCroc(c, m, x, y, time + m.t); }
    const under0 = p.d > t.surface_depth, px0 = this._sx(p.x), py0 = this._sy(p.d);
    const tgt = under0 && !this.harp ? this.aimTarget() : null;
    if (under0 && !this.harp) { // dotted aim guide
      const RR = this.harpRange(), ax = Math.cos(this.aim), ad = Math.sin(this.aim);
      for (let k = 1.2; k <= RR; k += 0.6) R(c, Math.round(this._sx(p.x + ax * k)), Math.round(this._sy(p.d + ad * k)), 1, 1, `rgba(255,240,180,${0.5 - k / RR * 0.35})`);
      const ex = this._sx(p.x + ax * RR), ey = this._sy(p.d + ad * RR); c.strokeStyle = "rgba(255,240,180,.4)"; c.strokeRect(Math.round(ex) - 2, Math.round(ey) - 2, 4, 4);
    }
    if (tgt) { const fx2 = this._sx(tgt.x), fy2 = this._sy(tgt.d); c.strokeStyle = "rgba(255,225,80,.85)"; c.beginPath(); c.arc(fx2, fy2, (tgt.sp ? 20 : 9) + Math.sin(time * 8), 0, TAU); c.stroke(); txt(tgt.sp ? "Space · " + tgt.sp.name + " ×" + tgt.sp.yield : "Space", fx2, fy2 - (tgt.sp ? 23 : 12), { size: 7, align: "center", color: "#ffe14d", weight: 900, stroke: "#1a1220", sw: 2 }); }
    if (this.harp) { // rope + spear tip
      const h = this.harp, hx = this._sx(h.x), hy = this._sy(h.d);
      c.strokeStyle = "rgba(230,225,200,.75)"; c.lineWidth = 1; c.beginPath(); c.moveTo(px0, py0); c.lineTo(hx, hy); c.stroke();
      const a = Math.atan2(h.ad * VS, h.ax * this._scale()); c.save(); c.translate(Math.round(hx), Math.round(hy)); c.rotate(h.state === "out" ? a : a + Math.PI);
      R(c, -6, 0, 6, 1, "#8a8f99"); R(c, 0, -1, 2, 3, "#e8eef5"); R(c, 2, 0, 2, 1, "#e8eef5"); c.restore();
    }
    // catch radius + player
    const px = this._sx(p.x), py = this._sy(p.d), under = p.d > t.surface_depth;
    const sn = under ? snakeInReach(this.snakes, p.x, p.d, this.catchR) : null;
    if (sn && !tgt && !this.harp) txt("Space · choáng", this._sx(sn.x), this._sy(sn.d) + 14, { size: 7, align: "center", color: "#ffe14d", weight: 900, stroke: "#1a1220", sw: 2 });
    const blink = this.invuln > 0 && Math.floor(time * 16) % 2;
    if (!blink) { // speargun in hand along the aim, then the diver rotated to the swim direction
      if (under && !this.harp) { const ax = Math.cos(this.aim) * this._scale(), ay = Math.sin(this.aim) * VS, n = Math.hypot(ax, ay) || 1; c.strokeStyle = "#5a5f6a"; c.lineWidth = 2; c.beginPath(); c.moveTo(px + ax / n * 3, py + ay / n * 3); c.lineTo(px + ax / n * 11, py + ay / n * 11); c.stroke(); c.lineWidth = 1; }
      diver(c, px, py, p.face, p.phase, Math.hypot(p.vx, p.vd) / this.swim, { grab: !!this.harp, tilt: this.tilt * p.face }); }
    this.ps.draw(c, 0, 0);

    // danger vignette
    if (this.danger > 0.01) {
      const g = c.createRadialGradient(W / 2, H / 2, H * 0.25, W / 2, H / 2, H * 0.75);
      g.addColorStop(0, "rgba(220,30,30,0)"); g.addColorStop(1, `rgba(200,10,10,${0.5 * this.danger * (0.6 + 0.4 * Math.sin(time * 10))})`);
      c.fillStyle = g; c.fillRect(0, 0, W, H);
    }
    if (this.flashHurt > 0) { this.flashHurt -= 0.016; }

    this.drawHUD(c, time);
    if (this.result) this.drawResult(c, time);
    else if (this.hintT > 0 && !this.started) this.drawHint(c);
  }

  drawHUD(c, time) {
    const u = screen.ui, p = this.p, under = p.d > this.t.surface_depth;
    // "Thủy quái!" — purple screen border while a monster is within its detect radius
    if (this.crocWarn > 0.01) {
      const a = this.crocWarn * (0.65 + 0.35 * Math.sin(time * 9));
      u.save(); u.strokeStyle = `rgba(170,70,255,${a})`; u.lineWidth = 6; u.strokeRect(3, 3, W - 6, H - 6); u.restore();
      txt("Thủy quái!", W / 2, 34, { size: 12, align: "center", color: "#d9a6ff", weight: 900, stroke: "#1a0830", sw: 3, alpha: this.crocWarn });
    }
    // timer pill (colour change at ≤ 30 s)
    const mm = Math.floor(Math.ceil(this.time) / 60), ss = Math.ceil(this.time) % 60;
    const low = this.time <= 30;
    panel(W / 2 - 26, 4, 52, 15, { fill: "rgba(8,20,38,.8)", border: low ? "#ff6b6b" : "#f3d27a", r: 7 });
    txt(`${mm}:${String(ss).padStart(2, "0")}`, W / 2, 15, { size: 11, align: "center", color: low ? "#ff8a8a" : "#fff", weight: 900, alpha: low && this.time < 10 && Math.floor(time * 4) % 2 ? 0.5 : 1 });
    // oxygen (< 25 %: red + blink)
    const ox = 8, oy = 6, ow = 92, oh = 11, fr = this.oxy / this.oxyMax;
    const lowO = fr < 0.25, blinkO = lowO && Math.floor(time * 5) % 2;
    panel(ox, oy, ow, oh, { fill: "rgba(4,16,30,.8)", border: lowO ? "#ff5a5a" : "#2a5a7a", r: 5 });
    const ocol = lowO ? "#ff5a5a" : fr < 0.5 ? "#ffd23a" : "#4fd0ff";
    u.save(); u.globalAlpha = blinkO ? 0.45 : 1; u.beginPath(); u.roundRect(ox + 1.5, oy + 1.5, Math.max(0, (ow - 3) * fr), oh - 3, 4); u.clip();
    u.fillStyle = ocol; u.fillRect(ox, oy, ow, oh);
    u.fillStyle = "rgba(255,255,255,.3)"; u.fillRect(ox, oy + 1, ow, 2); u.restore();
    txt("O₂", ox + 5, oy + 9, { size: 7, color: "#dff4ff", weight: 900 });
    txt(Math.ceil(this.oxy) + "/" + this.oxyMax + "s", ox + ow - 4, oy + 9, { size: 7, color: "#fff", align: "right", weight: 900 });
    if (this.oxy <= 0 && under) txt("Hết hơi!", W / 2, H / 2 - 40, { size: 16, align: "center", color: "#ff5a5a", weight: 900, stroke: "#1a1220", sw: 3, alpha: 0.6 + 0.4 * Math.sin(time * 10) });
    // HP hearts + depth
    for (let i = 0; i < this.hpMax; i++) { const hx = ox + 6 + i * 12, hy = oy + oh + 8; this.heart(u, hx, hy, i < this.hp, time); }
    const deepNow = p.d > DEEP.zone;
    txt("Máu " + this.hp + "/" + this.hpMax, ox + 6, oy + oh + 24, { size: 7, color: "#ffb0c0", weight: 900, stroke: "#06101e", sw: 2 });
    txt("↓ " + Math.round(p.d) + "m" + (deepNow ? "  O₂×" + DEEP.pressure : ""), ox + 6 + this.hpMax * 12 + 4, oy + oh + 12, { size: 8, color: deepNow ? "#9fd8ff" : "#dff4ff", weight: 900, stroke: "#06101e", sw: 2 });
    // catch cooldown (harpoon in flight counts as busy)
    { const cdMax = this.t.catch_cooldown_s || 0.5, busy = !!this.harp, k = busy ? 0 : 1 - clamp(this.catchCd / cdMax, 0, 1);
      const cx = ox + 50, cy = oy + oh + 18; panel(cx, cy, 42, 9, { fill: "rgba(4,16,30,.8)", border: k >= 1 ? "#7dffb0" : "#5a6a7a", r: 4 });
      u.fillStyle = k >= 1 ? "#7dffb0" : "#ffd23a"; u.fillRect(cx + 1.5, cy + 1.5, 39 * k, 6);
      txt(k >= 1 ? "Lao ✓" : "Lao…", cx + 21, cy + 7, { size: 7, align: "center", color: "#08131f", weight: 900 }); }
    // basket: one row for the contract's 12 slots, two rows once the "Giỏ lưới lớn" upgrade adds more
    const bw = 108, bx = W - bw - 6, by = 6, cap = this.cap, rows = cap > 12 ? 2 : 1, perRow = Math.ceil(cap / rows);
    const slotw = (bw - 10) / perRow, ic = Math.min(10, slotw + 1), bh = 6 + rows * 10 - 1;
    panel(bx, by, bw, bh, { fill: "rgba(8,20,38,.8)", border: "#f3d27a", r: 6 });
    u.imageSmoothingEnabled = false;
    for (let i = 0; i < cap; i++) { const row = Math.floor(i / perRow), col = i % perRow, sxx = bx + 5 + col * slotw, syy = by + 3 + row * 10; if (this.hold[i]) u.drawImage(icon(this.hold[i]), sxx + (slotw - 1 - ic) / 2, syy + 4.5 - ic / 2, ic, ic); else { u.fillStyle = "rgba(255,255,255,.08)"; u.fillRect(sxx, syy, slotw - 1, 9); } }
    txt(`Giỏ ${this.hold.length}/${cap}`, bx + bw / 2, by + bh + 9, { size: 7, align: "center", color: this.hold.length >= cap ? "#ff8a8a" : "#cfe", weight: 900 });
    // basket by kind + the day's NEEDED list (collected / needed, ✓ when met)
    const have = {}; for (const k of this.hold) have[k] = (have[k] || 0) + 1;
    const kinds = this.need ? Object.keys(this.need) : Object.keys(have);
    for (const k of Object.keys(have)) if (!kinds.includes(k)) kinds.push(k);
    if (kinds.length) {
      const ly = by + bh + 13, lh = 11, ph = 12 + kinds.length * lh;
      panel(bx, ly, bw, ph, { fill: "rgba(8,20,38,.78)", border: "#7ac0ff", r: 6 });
      txt(this.need ? "CẦN LẤY HÔM NAY" : "TRONG GIỎ", bx + bw / 2, ly + 9, { size: 7, align: "center", color: "#9fd8ff", weight: 900 });
      kinds.forEach((k, i) => {
        const yy = ly + 12 + i * lh, n = have[k] || 0, need = this.need?.[k], met = need != null && n >= need;
        u.drawImage(icon(k), bx + 4, yy, 9, 9);
        txt(KIND_NAME[k] || k, bx + 16, yy + 8, { size: 7, color: met ? "#7dffb0" : "#fff", weight: 800 });
        txt(need != null ? `${n}/${need}${met ? " ✓" : ""}` : "×" + n, bx + bw - 4, yy + 8, { size: 7, align: "right", color: met ? "#7dffb0" : need != null ? "#ffd23a" : "#cfe", weight: 900 });
      });
    }

    // toasts near player
    const px = this._sx(p.x), py = this._sy(p.d);
    this.toasts.forEach((t, i) => txt(t.txt, px, py - 14 + t.y - (this.toasts.length - 1 - i) * 11, { size: 9, align: "center", color: t.col, weight: 900, stroke: "#1a1220", sw: 2.5, alpha: clamp(t.life, 0, 1) }));
    // controls hint (bottom)
    txt("WASD bơi · E hái/cập bến · Space/chuột: bắn lao · Shift bơi nhanh · Esc/P tạm dừng", W / 2, H - 5, { size: 7, align: "center", color: "rgba(255,255,255,.55)", weight: 700 });
  }
  heart(u, x, y, full, time) {
    u.save(); u.translate(x, y); u.scale(0.95, 0.95);
    const beat = full && this.hp === 1 ? 1 + Math.sin(time * 8) * 0.12 : 1; u.scale(beat, beat);
    u.fillStyle = full ? "#ff5a7a" : "rgba(40,20,30,.75)";
    for (const [dx, dy, w, h] of [[-4, -3, 3, 3], [1, -3, 3, 3], [-5, 0, 10, 3], [-4, 3, 8, 2], [-2, 5, 4, 2]]) u.fillRect(dx, dy, w, h);
    if (full) u.fillStyle = "rgba(255,255,255,.6)", u.fillRect(-3, -2, 2, 2);
    u.restore();
  }
  drawHint(c) {
    const a = clamp(this.hintT, 0, 1);
    panel(W / 2 - 92, H / 2 - 20, 184, 40, { fill: `rgba(8,18,34,${0.85 * a})`, border: "#f3d27a", r: 6, alpha: a });
    txt("Lặn xuống bắt cá & hái bông", W / 2, H / 2 - 4, { size: 10, align: "center", color: "#fff", weight: 900, alpha: a });
    txt("Coi chừng Cá Sấu Năm Chèo dưới 10 m · canh O₂!", W / 2, H / 2 + 10, { size: 8, align: "center", color: "#ffd23a", weight: 700, alpha: a });
  }
  drawResult(c, time) {
    const r = this.result, k = clamp(r.t / 0.5, 0, 1);
    c.fillStyle = `rgba(4,10,22,${0.72 * k})`; c.fillRect(0, 0, W, H);
    const win = r.reason !== "fainted";
    if (win && r.t < 1.2) speedLines(screen.px, W / 2, H / 2, time, "rgba(255,220,120,.14)");
    const yc = H / 2 - 30;
    const title = r.reason === "fainted" ? "NGẤT XỈU!" : r.reason === "docked" ? "VỀ BẾN AN TOÀN" : "HẾT GIỜ";
    const col = r.reason === "fainted" ? "#ff5a5a" : "#7ee8ff";
    txt(title, W / 2, yc, { size: 26 * lerp(1.6, 1, k), align: "center", color: col, weight: 900, italic: true, stroke: "#1a1220", sw: 5, rot: -0.03 });
    if (r.reason === "fainted") txt("Hết máu — giỏ đã mất. Về bến sớm hơn lần sau!", W / 2, yc + 20, { size: 9, align: "center", color: "#ffb0b0", weight: 700 });
    else {
      const names = Object.keys(r.by);
      panel(W / 2 - 100, yc + 14, 200, 20 + names.length * 11, { fill: "rgba(8,20,38,.9)", border: "#f3d27a", r: 4 });
      txt("GIỎ HÔM NAY", W / 2, yc + 26, { size: 8, align: "center", color: "#ffd23a", weight: 900 });
      names.forEach((kk, i) => { const yy = yc + 38 + i * 11; const cnt = Math.min(r.by[kk], Math.floor(r.t * 6)); screen.ui.imageSmoothingEnabled = false; screen.ui.drawImage(icon(kk), W / 2 - 86, yy - 8, 9, 9); txt(KIND_NAME[kk], W / 2 - 72, yy, { size: 8, color: "#fff", weight: 700 }); txt("×" + r.by[kk], W / 2 + 86, yy, { size: 8, align: "right", color: "#cfe", weight: 900 }); });
    }
    if (r.t > 0.8) txt(Math.floor(r.t * 2) % 2 ? "Enter: nấu quán →   R: lặn lại" : "", W / 2, H - 22, { size: 9, align: "center", color: "#fff", weight: 900 });
  }
}
