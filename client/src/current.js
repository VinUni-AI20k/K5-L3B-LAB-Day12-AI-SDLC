// Dòng nước lũ (flood current) — Test Contract v1.2 §2 extension, mirrored in the GUI:
// for t = interval·k (k ≥ 1, phase ticks): warning at t − warning_ticks (text + arrow icon + sound), active from t to
// t + duration − 1 with a direction ±x drawn from the dive's seeded stream when the warning is announced (= the draw
// for that start). While active it adds `speed` m/s to the diver's x movement when the diver's depth at the START of
// the step is ≥ min_depth (not to fish / monsters; never accumulated into the diver's velocity). current_end at t+duration.
// Also: flowing particle lines for the permanent deep channels (terrain.js) and fast flood streaks.
export const CURRENT_DEFAULTS = { interval_ticks: 1800, duration_ticks: 480, warning_ticks: 120, min_depth: 10, speed: 1.5 };

function mulberry32(a) { return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

export class Flood {
  // cfg: contract gather.current (or undefined → defaults); seed: per dive; on: { warning(n,dir), start(dir,dur), end(dir,reason) }
  constructor(cfg, seed, hz = 60, on = {}) {
    this.c = { ...CURRENT_DEFAULTS, ...(cfg || {}) }; this.hz = hz; this.on = on;
    this.rand = mulberry32(seed | 0); this.lockDir = 0; // set ±1 to lock the direction (tests / scenario current_direction)
    this.n = 0; this.acc = 0;                 // phase tick of the current step
    this.next = this.c.interval_ticks;        // start tick of the next flood
    this.warned = false; this.pend = 1;
    this.active = false; this.dir = 0; this.endAt = 0;
    this.vis = 0; this.lean = 0;              // smoothed visual intensity / kelp lean (−1..1)
  }
  // call once per step BEFORE movement; returns the x push (m/s) for this step given the diver's depth at step start
  step(dt, d0) {
    const c = this.c, n = this.n;
    if (this.active && n >= this.endAt) { this.active = false; this.on.end?.(this.dir, "elapsed"); }
    if (!this.active && !this.warned && n >= this.next - c.warning_ticks) {
      this.warned = true; this.pend = this.lockDir || (this.rand() < 0.5 ? -1 : 1); this.on.warning?.(this.next, this.pend);
    }
    if (!this.active && n >= this.next) {
      if (!this.warned) { this.warned = true; this.pend = this.lockDir || (this.rand() < 0.5 ? -1 : 1); }
      this.active = true; this.dir = this.pend; this.endAt = this.next + c.duration_ticks; this.next += c.interval_ticks; this.warned = false;
      this.on.start?.(this.dir, c.duration_ticks);
    }
    const push = this.active && d0 >= c.min_depth ? this.dir * c.speed : 0;
    // advance the phase clock
    this.acc += dt * this.hz; const k = Math.floor(this.acc + 1e-6); if (k > 0) { this.n += k; this.acc -= k; }
    const target = this.active ? 1 : 0; this.vis += (target - this.vis) * Math.min(1, dt * (this.active ? 3 : 1.5));
    this.lean += ((this.active ? this.dir : 0) - this.lean) * Math.min(1, dt * 2);
    return push;
  }
  warning() { return !this.active && this.warned ? this.pend : 0; }      // ±1 while the warning is up
  secondsLeft() { return this.active ? Math.max(0, (this.endAt - this.n) / this.hz) : 0; }
  stop(reason = "phase_end") { if (this.active) { this.active = false; this.on.end?.(this.dir, reason); } }
  snapshot() { return this.active ? { direction: this.dir, ticks_left: this.endAt - this.n } : null; }
}

// ---------- visuals (fixed pools, no per-frame allocation) ----------
const NS = 70, streak = new Float32Array(NS * 3); // x px, y frac, speed
for (let i = 0; i < NS; i++) { streak[i * 3] = (i * 97.3) % 480; streak[i * 3 + 1] = ((i * 0.6180339) % 1); streak[i * 3 + 2] = 0.6 + ((i * 7) % 10) / 10; }
export function updateFloodFx(fl, dt, W) {
  const v = fl.active ? fl.dir : fl.lean >= 0 ? 1 : -1;
  for (let i = 0; i < NS; i++) {
    let x = streak[i * 3] + v * (260 + 240 * streak[i * 3 + 2]) * dt * Math.max(0.15, fl.vis);
    if (x > W + 40) x -= W + 80; else if (x < -40) x += W + 80;
    streak[i * 3] = x;
  }
}
// streaks + drifting bubbles across the band of the screen below yTop
export function drawFloodFx(c, fl, W, H, yTop, t) {
  const a = fl.vis; if (a < 0.02 || yTop >= H) return;
  const y0 = Math.max(0, yTop), hh = H - y0, dir = fl.active ? fl.dir : fl.lean >= 0 ? 1 : -1;
  c.fillStyle = "#f2e2b8"; // silt
  for (let i = 0; i < NS; i++) {
    const s = streak[i * 3 + 2], x = Math.round(streak[i * 3]), y = Math.round(y0 + streak[i * 3 + 1] * hh + Math.sin(t * 3 + i) * 2);
    if (i % 5 === 0) { c.globalAlpha = a * 0.5; c.fillRect(x, y, 2, 2); continue; } // bubble
    c.globalAlpha = a * (0.12 + 0.25 * s); c.fillRect(dir > 0 ? x - Math.round(18 * s) : x, y, Math.round(18 * s) + 4, 1);
  }
  c.globalAlpha = 1;
}

// permanent channel particles: per channel a pool of points flowing along (vx,vd), world metres
export class ChannelFx {
  constructor(channels, per = 36) {
    this.ch = channels; this.per = per; this.p = new Float32Array(channels.length * per * 3); // x, d, life
    let s = 7; const r = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
    this.r = r;
    for (let k = 0; k < channels.length; k++) for (let i = 0; i < per; i++) this.seed(k, i, true);
  }
  seed(k, i, anywhere) {
    const ch = this.ch[k], o = (k * this.per + i) * 3, r = this.r;
    const along = ch.vx !== 0;
    if (along) { this.p[o] = anywhere ? ch.x0 + r() * (ch.x1 - ch.x0) : (ch.vx > 0 ? ch.x0 : ch.x1); this.p[o + 1] = ch.d0 + 0.3 + r() * (ch.d1 - ch.d0 - 0.6); }
    else { this.p[o] = ch.x0 + 0.3 + r() * (ch.x1 - ch.x0 - 0.6); this.p[o + 1] = anywhere ? ch.d0 + r() * (ch.d1 - ch.d0) : (ch.vd < 0 ? ch.d1 : ch.d0); }
    this.p[o + 2] = 0.6 + r() * 0.8;
  }
  update(dt) {
    for (let k = 0; k < this.ch.length; k++) { const ch = this.ch[k];
      for (let i = 0; i < this.per; i++) { const o = (k * this.per + i) * 3, sp = this.p[o + 2];
        this.p[o] += ch.vx * sp * 1.4 * dt; this.p[o + 1] += ch.vd * sp * 1.4 * dt;
        if (this.p[o] < ch.x0 || this.p[o] > ch.x1 || this.p[o + 1] < ch.d0 || this.p[o + 1] > ch.d1) this.seed(k, i, false);
      } }
  }
  draw(c, ox, oy, sx, sy, W, H, t) {
    c.fillStyle = "#ead7a6";
    for (let k = 0; k < this.ch.length; k++) { const ch = this.ch[k], horiz = ch.vx !== 0;
      const X0 = ox + ch.x0 * sx, X1 = ox + ch.x1 * sx, Y0 = oy + ch.d0 * sy, Y1 = oy + ch.d1 * sy;
      if (X1 < 0 || X0 > W || Y1 < 0 || Y0 > H) continue;
      // faint band so the channel reads as a stream
      c.globalAlpha = 0.06 + 0.02 * Math.sin(t * 2 + k); c.fillRect(Math.max(0, Math.round(X0)), Math.round(Y0), Math.round(Math.min(W, X1) - Math.max(0, X0)), Math.round(Y1 - Y0));
      for (let i = 0; i < this.per; i++) { const o = (k * this.per + i) * 3, x = Math.round(ox + this.p[o] * sx), y = Math.round(oy + this.p[o + 1] * sy);
        if (x < -20 || x > W + 20 || y < -20 || y > H + 20) continue;
        const L = Math.round(6 + this.p[o + 2] * 8);
        c.globalAlpha = 0.25 + 0.3 * (this.p[o + 2] - 0.6);
        if (horiz) c.fillRect(ch.vx > 0 ? x - L : x, y, L, 1); else c.fillRect(x, ch.vd < 0 ? y : y - L, 1, L);
        if (i % 6 === 0) { c.globalAlpha = 0.5; c.fillRect(x, y, 2, 2); }
      } }
    c.globalAlpha = 1;
  }
}
