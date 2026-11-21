// Timeline-driven cutscenes. A script is a flat list of steps; blocking steps pause the timeline.
import { W, H, screen, input, fx, ease, clamp, lerp, txt, wrap, panel, measure, reduceMotion } from "./engine.js";
import { sfx, music } from "./audio.js";
import { portrait, R } from "./art.js";

// ---------- shared comic-style effects ----------
export function speedLines(c, cx, cy, t, col = "rgba(255,255,255,.55)", n = 28) {
  c.save(); c.fillStyle = col;
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2 + t * 0.6 + Math.sin(i * 12.9) * 0.08;
    const r0 = 70 + ((i * 37) % 40) + Math.sin(t * 9 + i) * 8, r1 = 420;
    const w = 0.012 + ((i * 7) % 5) * 0.004;
    c.beginPath();
    c.moveTo(cx + Math.cos(a - w) * r1, cy + Math.sin(a - w) * r1);
    c.lineTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0);
    c.lineTo(cx + Math.cos(a + w) * r1, cy + Math.sin(a + w) * r1);
    c.fill();
  }
  c.restore();
}
export function halftone(c, x, y, w, h, col, step = 6, grow = true) {
  c.fillStyle = col;
  for (let yy = 0; yy < h; yy += step) for (let xx = (yy / step) % 2 ? step / 2 : 0; xx < w; xx += step) {
    const r = grow ? Math.max(0, (xx / w) * step * 0.45) : step * 0.3;
    if (r >= 0.5) c.fillRect(Math.round(x + xx - r / 2), Math.round(y + yy - r / 2), Math.ceil(r), Math.ceil(r));
  }
}
// Big comic title with chromatic split + thick outline (UI layer).
export function slamText(str, x, y, size, o = {}) {
  const rot = o.rot ?? -0.06;
  if (!reduceMotion && o.split !== false) {
    txt(str, x - 1.6, y, { size, italic: true, weight: 900, color: "rgba(255,40,90,.75)", align: o.align || "center", rot, scale: o.scale });
    txt(str, x + 1.6, y, { size, italic: true, weight: 900, color: "rgba(40,220,255,.75)", align: o.align || "center", rot, scale: o.scale });
  }
  txt(str, x, y, { size, italic: true, weight: 900, color: o.color || "#fff", stroke: o.stroke || "#1a1220", sw: o.sw || size * 0.22, align: o.align || "center", rot, scale: o.scale, alpha: o.alpha });
}

// ---------- intro card: "character name slam" ----------
function drawIntroCard(c, card, k, t) {
  const D = card.dur;
  const inK = ease.out(clamp(k / 0.35, 0, 1));
  const outK = ease.in(clamp((k - (D - 0.35)) / 0.35, 0, 1));
  const sweep = -outK * (W + 200);
  // backdrop: two diagonal panels + halftone + speed lines
  c.save(); c.translate(sweep, 0);
  c.fillStyle = card.colA; c.beginPath(); c.moveTo(-40, 0); c.lineTo(lerp(-40, W * 0.72, inK), 0); c.lineTo(lerp(-40, W * 0.48, inK), H); c.lineTo(-40, H); c.fill();
  c.fillStyle = card.colB; c.beginPath(); c.moveTo(W + 40, 0); c.lineTo(lerp(W + 40, W * 0.72, inK), 0); c.lineTo(lerp(W + 40, W * 0.48, inK), H); c.lineTo(W + 40, H); c.fill();
  c.save(); c.beginPath(); c.moveTo(-40, 0); c.lineTo(W * 0.72, 0); c.lineTo(W * 0.48, H); c.lineTo(-40, H); c.clip();
  speedLines(c, 120, H / 2, t, "rgba(255,255,255,.22)");
  halftone(c, 0, 0, W * 0.7, H, "rgba(0,0,0,.18)", 7);
  c.restore();
  // diagonal stripe
  c.fillStyle = card.stripe || "#fff";
  c.beginPath(); c.moveTo(W * 0.72, 0); c.lineTo(W * 0.735, 0); c.lineTo(W * 0.495, H); c.lineTo(W * 0.48, H); c.fill();
  // portrait, huge chunky pixels
  const pk = ease.back(clamp((k - 0.08) / 0.45, 0, 1));
  const img = portrait(card.portrait), S = 7;
  const px = lerp(-200, 40, pk) + Math.sin(t * 2) * 1.5, py = H - img.height * S + 6;
  c.imageSmoothingEnabled = false;
  c.globalAlpha = 0.35; c.fillStyle = "#000"; c.fillRect(px + 8, py + 8, img.width * S, img.height * S - 8); c.globalAlpha = 1;
  c.drawImage(img, Math.round(px), Math.round(py), img.width * S, img.height * S);
  c.restore();
  // text on UI layer
  const nk = clamp((k - 0.28) / 0.22, 0, 1);
  if (nk > 0) {
    const sc = lerp(2.4, 1, ease.out(nk));
    slamText(card.name, W * 0.68 + sweep, H * 0.5, 44, { scale: sc, color: card.nameCol || "#fff", alpha: Math.min(1, nk * 2) });
  }
  const sk = clamp((k - 0.55) / 0.3, 0, 1);
  if (sk > 0) {
    const n = Math.floor(card.sub.length * sk);
    panel(W * 0.42 + sweep, H * 0.6, W * 0.52, 22, { fill: "rgba(20,10,30,.85)", border: card.nameCol || "#fff", r: 2 });
    txt(card.sub.slice(0, n), W * 0.68 + sweep, H * 0.6 + 15, { size: 10, align: "center", color: "#fff" });
  }
  if (card.tag && k > 0.7) txt(card.tag, W * 0.68 + sweep, H * 0.37, { size: 9, align: "center", color: card.tagCol || "#ffe08a", weight: 900 });
}

// ---------- title card ----------
function drawTitleCard(c, card, k, t) {
  const D = card.dur;
  const inK = ease.out(clamp(k / 0.25, 0, 1));
  const outK = ease.in(clamp((k - (D - 0.3)) / 0.3, 0, 1));
  const bandH = 64 * inK * (1 - outK);
  c.fillStyle = card.band || "rgba(10,10,20,.85)";
  c.fillRect(0, H / 2 - bandH / 2, W, bandH);
  for (let i = 0; i < 14; i++) {
    const y = H / 2 - bandH / 2 + ((i * 13) % Math.max(1, bandH));
    const x = ((t * 600 + i * 97) % (W + 100)) - 50;
    R(c, x, y, 30 + (i % 3) * 20, 1, "rgba(255,255,255,.25)");
  }
  if (bandH > 4) {
    c.fillStyle = card.color || "#ffd23f";
    c.fillRect(0, H / 2 - bandH / 2, W, 2); c.fillRect(0, H / 2 + bandH / 2 - 2, W, 2);
  }
  const tk = clamp((k - 0.12) / 0.18, 0, 1);
  if (tk > 0 && outK < 1) {
    slamText(card.text, W / 2 - outK * 300, H / 2 + 8, 30, { scale: lerp(2, 1, ease.out(tk)), color: card.color || "#ffd23f", rot: -0.03, alpha: 1 - outK });
    if (card.sub) txt(card.sub, W / 2 + outK * 300, H / 2 + 24, { size: 9, align: "center", color: "#fff", alpha: clamp((k - 0.4) * 3, 0, 1) * (1 - outK) });
  }
}

// ---------- the player ----------
export class Cutscene {
  constructor(steps, onDone) {
    this.steps = steps; this.i = 0; this.onDone = onDone;
    this.t = 0; this.cam = { x: 0, y: 0, z: 1 }; this.v = {};
    this.bg = null; this.tweens = []; this.cur = null; this.curT = 0;
    this.bars = 0; this.fade = { a: 1, to: 1, col: "#000", spd: 2 }; this.skipHold = 0; this.done = false;
    this.say = null; this.caption = null; this.card = null;
    this.advance();
  }
  tween(obj, to, dur, e = ease.inOut) {
    const from = {}; for (const k in to) from[k] = obj[k] ?? 0;
    this.tweens.push({ obj, from, to, dur, t: 0, e });
  }
  advance() {
    this.cur = null; this.curT = 0;
    while (this.i < this.steps.length) {
      const s = this.steps[this.i++];
      if (s.bg) { this.bg = s.bg; continue; }
      if (s.music !== undefined) { music(s.music); continue; }
      if (s.sfx) { sfx(s.sfx); continue; }
      if (s.shake) { fx.shake(s.shake, s.t || 0.4); continue; }
      if (s.flash) { fx.flash(s.flash, s.t || 0.2); continue; }
      if (s.set) { Object.assign(this.v, s.set); continue; }
      if (s.fade) { this.fade.to = s.fade === "out" ? 1 : 0; this.fade.col = s.color || "#000"; this.fade.spd = 1 / (s.dur || 0.5); if (s.wait) { this.cur = s; return; } continue; }
      if (s.cam) { this.tween(this.cam, s.cam, s.dur, s.ease ? ease[s.ease] : ease.inOut); if (s.wait) { this.cur = { wait: s.dur }; return; } continue; }
      if (s.tween) { this.tween(this.v, s.tween, s.dur, s.ease ? ease[s.ease] : ease.inOut); if (s.wait) { this.cur = { wait: s.dur }; return; } continue; }
      if (s.caption) { this.caption = { ...s, k: 0 }; this.cur = s; return; }
      if (s.say) { this.say = { ...s, k: 0, shown: 0 }; this.cur = s; return; }
      if (s.intro) { this.card = { type: "intro", ...s.intro, dur: s.intro.dur || 2.9, k: 0, hit: false }; this.cur = s; sfx("whoosh"); return; }
      if (s.title) { this.card = { type: "title", ...s.title, dur: s.title.dur || 2.2, k: 0, hit: false }; this.cur = s; sfx("whoosh"); return; }
      if (s.wait !== undefined) { this.cur = s; return; }
    }
    this.finish();
  }
  finish() { if (this.done) return; this.done = true; this.onDone?.(); }
  update(dt) {
    if (this.done) return;
    this.t += dt; this.curT += dt;
    this.bars = Math.min(1, this.bars + dt * 2.5);
    const f = this.fade; f.a += Math.sign(f.to - f.a) * Math.min(Math.abs(f.to - f.a), dt * f.spd);
    for (const tw of this.tweens) {
      tw.t = Math.min(tw.dur, tw.t + dt); const k = tw.e(tw.t / tw.dur);
      for (const key in tw.to) tw.obj[key] = lerp(tw.from[key], tw.to[key], k);
    }
    this.tweens = this.tweens.filter((tw) => tw.t < tw.dur);
    // skip: hold Esc
    if (input.down("back")) { this.skipHold += dt; if (this.skipHold > 0.7) { sfx("click"); this.finish(); return; } } else this.skipHold = 0;

    const s = this.cur; if (!s) return;
    if (s.wait !== undefined && this.curT >= s.wait) return this.advance();
    if (s.fade && Math.abs(f.a - f.to) < 0.001) return this.advance();
    if (s.caption) {
      const c = this.caption; c.k = this.curT;
      if (this.curT >= (s.dur || 2.6) || (this.curT > 0.4 && input.hit("confirm"))) { this.caption = null; return this.advance(); }
    }
    if (s.say) {
      const d = this.say;
      const before = Math.floor(d.shown);
      d.shown = Math.min(d.text.length, d.shown + dt * 42);
      if (Math.floor(d.shown) > before && Math.floor(d.shown) % 2 === 0 && d.text[Math.floor(d.shown) - 1] !== " ") sfx("blip");
      if (input.hit("confirm") || input.hit("catch") || input.hit("interact")) {
        if (d.shown < d.text.length) d.shown = d.text.length;
        else { sfx("click"); this.say = null; return this.advance(); }
      }
    }
    if (this.card) {
      const c = this.card; c.k = this.curT;
      const impact = c.type === "intro" ? 0.3 : 0.14;
      if (!c.hit && c.k >= impact) { c.hit = true; sfx("slam"); fx.shake(c.type === "intro" ? 6 : 4, 0.35); fx.flash("#fff", 0.1); fx.hitstop(0.06); }
      if (c.k >= c.dur) { this.card = null; return this.advance(); }
    }
  }
  draw() {
    const c = screen.px;
    if (this.bg) this.bg(c, this);
    if (this.card) (this.card.type === "intro" ? drawIntroCard : drawTitleCard)(c, this.card, this.card.k, this.t);
    // letterbox
    const bh = Math.round(22 * ease.out(this.bars));
    c.fillStyle = "#000"; c.fillRect(0, 0, W, bh); c.fillRect(0, H - bh, W, bh);
    // caption (location/time card)
    if (this.caption) {
      const cp = this.caption, n = Math.floor(cp.caption.length * clamp(cp.k / 1.0, 0, 1));
      const a = clamp(cp.k * 3, 0, 1) * clamp(((cp.dur || 2.6) - cp.k) * 3, 0, 1);
      txt(cp.caption.slice(0, n), cp.x ?? 18, cp.y ?? 44, { size: cp.size || 13, color: "#fff", shadow: "rgba(0,0,0,.6)", alpha: a, align: cp.align || "left" });
      if (cp.sub) txt(cp.sub, cp.x ?? 18, (cp.y ?? 44) + 13, { size: 8, color: "#ffe2a8", alpha: a * clamp(cp.k - 0.8, 0, 1), align: cp.align || "left", weight: 700 });
    }
    if (this.say) this.drawSay(this.say);
    if (this.skipHold > 0) {
      const u = screen.ui; u.save(); u.strokeStyle = "#fff"; u.lineWidth = 1.5;
      u.beginPath(); u.arc(W - 16, H - 11, 5, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * (this.skipHold / 0.7)); u.stroke(); u.restore();
    }
    txt("Giữ Esc để bỏ qua", W - 26, H - 8, { size: 7, align: "right", color: "rgba(255,255,255,.55)", weight: 700 });
    if (this.fade.a > 0.001) { const u = screen.ui; u.save(); u.globalAlpha = this.fade.a; u.fillStyle = this.fade.col; u.fillRect(0, 0, W, H); u.restore(); }
  }
  drawSay(d) {
    const right = d.side === "right";
    const bx = 14, by = H - 22 - 62, bw = W - 28, bh = 58;
    panel(bx, by, bw, bh, { fill: "rgba(14,12,28,.92)", border: "#f3d27a", bw: 1.5, r: 5 });
    const img = portrait(d.portrait || "sen"), S = 2.2;
    const pw = img.width * S;
    const ix = right ? bx + bw - pw - 8 : bx + 8;
    const u = screen.ui; u.save(); u.imageSmoothingEnabled = false;
    u.fillStyle = "rgba(255,255,255,.07)"; u.fillRect(ix - 2, by + 4, pw + 4, bh - 8);
    u.drawImage(img, ix, by + bh - img.height * S - 3, pw, img.height * S); u.restore();
    const tx = right ? bx + 12 : bx + pw + 18, tw = bw - pw - 34;
    const nameW = measure(d.say, 9, 900) + 12;
    panel(tx - 2, by - 8, nameW, 13, { fill: d.color || "#d94a3d", border: "#fff", r: 2 });
    txt(d.say, tx + 4, by + 2, { size: 9, weight: 900, color: "#fff" });
    const lines = wrap(d.text, tw, 10);
    let left = Math.floor(d.shown);
    lines.forEach((ln, i) => { const part = ln.slice(0, Math.max(0, left)); left -= ln.length + 1; txt(part, tx, by + 18 + i * 13, { size: 10, color: "#f6efe0", weight: 700 }); });
    if (d.shown >= d.text.length && Math.floor(this.t * 3) % 2) txt("▼", bx + bw - 12, by + bh - 6, { size: 8, color: "#f3d27a" });
  }
}
