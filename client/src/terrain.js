// "Sáng tạo của nhóm" — GUI-only underwater terrain (never in headless / Test Contract).
// Contract zone d ∈ [0,30]: rocks only as edge / background decoration, NO collision (fish bands, croc depths and
// diver movement there are untouched). Creative deep zone d ∈ (30,60]: a seabed with mountains and valleys, 3 rock
// pillars, a ledge, one cave pocket (crystals + a clam worth +30k once per dive) — all SOLID: the diver slides along
// them, deep fish / the boss / the spear collide with them. Two permanent current channels (a river-bottom stream
// pushing +x and an upwelling beside a pillar) are carved through the rock.
// The shape is analytic (solid(x,d)), deterministic per day seed; the drawing is baked once into an offscreen canvas.
// Backdrop: 3 parallax layers of underwater ridges (uw_far.png + ridgeline, uw_mid.png arches, near ridges).

const ZONE = 30, BOT = 60;

function mulberry32(a) { return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const hash = (i, j) => { let h = (i * 374761393 + j * 668265263) | 0; h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };

const IMGS = {};
function img(path) { let im = IMGS[path]; if (!im) { im = new Image(); im.src = "assets/" + path; IMGS[path] = im; } return im; }
const ready = (im) => im && im.complete && im.naturalWidth > 0;
export function preloadTerrain() { img("bg/uw_tiles.png"); img("bg/uw_far.png"); img("bg/uw_mid.png"); }
const mkCanvas = (w, h) => { const cv = document.createElement("canvas"); cv.width = w; cv.height = h; return cv; };

export class Terrain {
  constructor(seed = 1) {
    const r = mulberry32((seed * 2654435761) ^ 0x9e3779b9), j = (a) => (r() - 0.5) * 2 * a;
    this.seed = seed;
    this.fa = r() * 6; this.fb = r() * 6;
    // seabed mountains (gaussian bumps on the floor profile)
    this.mts = [{ x: 9 + j(3), h: 7 + r() * 4, w: 4.5 + r() * 2 }, { x: 52 + j(3), h: 6 + r() * 4, w: 4 + r() * 2 }, { x: 89 + j(3), h: 8 + r() * 4, w: 5 + r() * 2 }];
    // pillars [x, half-width, top depth, phase]
    this.pil = [{ x: 24 + j(2), hw: 1.6 + r() * 0.5, top: 36 + r() * 4, ph: r() * 6 }, { x: 63 + j(1.5), hw: 1.8 + r() * 0.4, top: 35 + r() * 3, ph: r() * 6 }, { x: 74.5 + j(1), hw: 1.5 + r() * 0.4, top: 37 + r() * 4, ph: r() * 6 }];
    const p2 = this.pil[1];
    this.ledge = { x0: p2.x - 11 - r() * 2, x1: p2.x, d0: 40.4 + j(0.4) };
    // cave pocket: rock mass on the floor with a hollow interior, tunnel entrance on the right
    const cx = 39 + j(1);
    this.cave = { cx, hw: 7, top: 48, ix: cx - 0.5, id: 53.6, rx: 5, rd: 2.6, t0: 52.4, t1: 55, tx0: cx + 2, tx1: cx + 8.2 };
    this.clam = { x: cx - 2.6, d: 55.3, open: false, t: 0 };
    this.crystals = [];
    for (let i = 0; i < 7; i++) { const a = Math.PI * (0.15 + i * 0.12) + (i % 2 ? 0.05 : -0.05), up = i % 2 === 0; const k = up ? -1 : 1; this.crystals.push({ x: this.cave.ix + Math.cos(a * 2.2) * this.cave.rx * 0.82, d: this.cave.id + k * this.cave.rd * 0.86 * Math.max(0.5, Math.abs(Math.sin(a * 2.2))), up, s: 3 + (i % 3), ph: i * 1.7 }); }
    // permanent current channels (m/s); carved open through the rock
    const p3 = this.pil[2];
    this.channels = [
      { name: "stream", x0: 2, x1: 98, d0: 44, d1: 47, vx: 2, vd: 0 },
      { name: "upwell", x0: p3.x + p3.hw + 0.6, x1: p3.x + p3.hw + 3.2, d0: 33, d1: 56.5, vx: 0, vd: -2.5 },
    ];
    // contract zone (0–30 m) — collides with the DIVER and the SPEAR only (fish / monsters keep their contract
    // movement and are drawn in front). Everything sits in the gaps between the spawn columns x∈{15,30,45,60,75,90}
    // (≥ 3 m clear), off the croc lanes (M1 x 58–66 @ 22–26, M2 x 83–91 @ 16–20), below 3 m (nodes / dock at d=0).
    this.spil = [{ x: 22.5, hw: 1.45, top: 9 + r() * 1.5, ph: r() * 6, wide: 0.03 }, { x: 52.5, hw: 1.55, top: 9.5 + r() * 1.5, ph: r() * 6, wide: 0.03 }, { x: 80, hw: 1.2, top: 11 + r() * 1.5, ph: r() * 6, wide: 0.02 }];
    this.smounds = [{ x: 37.5, h: 9 + r() * 2, w: 3.2, lim: 4.4 }, { x: 68.5, h: 2.8 + r() * 0.4, w: 2.5, lim: 3.4 }, { x: 8.5, h: 5 + r() * 2, w: 2.2, lim: 3.4 }];
    this.sshelf = [{ x0: 19, x1: 22.5, d0: 16 + r(), th: 1.1 }, { x0: 52.5, x1: 56.6, d0: 13 + r(), th: 1.0 }, { x0: 48.4, x1: 52.5, d0: 20 + r(), th: 0.9, left: true }];
    this.cv = null; this.cvMoss = false; this.bg = null;
  }
  // left bank stays thin under the dock (start x=2) so the diver can drop straight down; it widens below ~20 m
  bankL(d) { return (d < 20 ? 0.5 + d * 0.05 : 1.5 + (d - 20) * 0.1) + Math.sin(d * 0.7 + this.fa) * 0.2 + Math.sin(d * 2.1) * 0.1; }
  bankR(d) { return 100 - (2.5 + Math.sin(d * 0.6 + this.fb) * 0.55 + Math.sin(d * 1.9 + 2) * 0.25 + (d > 18 ? (d - 18) * 0.035 : 0)); }
  // contract-zone rock (background layer): river-bank cliffs from 3 m, pillars, mounds on the 30 m floor, shelves
  shallow(x, d) {
    if (d < 3) return false;
    if (x < this.bankL(d) || x > this.bankR(d)) return true;
    if (d < 8.5) return false;
    for (const p of this.spil) { const dx = x - p.x, hw = p.hw * (1 + 0.15 * Math.sin(d * 1.6 + p.ph)) + (d - p.top) * p.wide; if (d >= p.top && dx >= -hw && dx <= hw && d >= p.top + 1.2 * (dx / hw) * (dx / hw)) return true; }
    for (const m of this.smounds) { const dx = x - m.x; if (dx >= -m.lim && dx <= m.lim) { const u = dx / m.w; if (d >= ZONE - m.h * Math.exp(-u * u) + Math.sin(x * 1.7) * 0.2) return true; } }
    for (const s of this.sshelf) if (x >= s.x0 && x <= s.x1) { const k = s.left ? (s.x1 - x) / (s.x1 - s.x0) : (x - s.x0) / (s.x1 - s.x0), top = s.d0 + Math.sin(x * 2.3) * 0.2; if (d >= top && d <= top + s.th * (0.45 + 0.55 * (1 - k))) return true; }
    return false;
  }

  floorAt(x) {
    let f = 57.6 + Math.sin(x * 0.23 + this.fa) * 1.0 + Math.sin(x * 0.61 + this.fb) * 0.6;
    for (const m of this.mts) { const u = (x - m.x) / m.w; f -= m.h * Math.exp(-u * u); }
    return f < 44.5 ? 44.5 : f;
  }
  chanAt(x, d) { for (const ch of this.channels) if (x >= ch.x0 && x <= ch.x1 && d >= ch.d0 && d <= ch.d1) return ch; return null; }
  caveOpen(x, d) {
    const c = this.cave, u = (x - c.ix) / c.rx, v = (d - c.id) / c.rd;
    return u * u + v * v < 1 || (x >= c.tx0 && x <= c.tx1 && d >= c.t0 && d <= c.t1);
  }
  inCave(x, d) { const c = this.cave; return Math.abs(x - c.cx) <= c.hw + 1.5 && d >= c.top - 1; }
  // solid rock? (contract zone never)
  solid(x, d) {
    if (d < 0 || d > BOT || x < 0 || x > 100) return false;
    if (d < ZONE) return this.shallow(x, d);
    for (const ch of this.channels) if (x >= ch.x0 && x <= ch.x1 && d >= ch.d0 && d <= ch.d1) return false;
    const c = this.cave, cu = (x - c.cx) / c.hw;
    if (cu >= -1 && cu <= 1 && d >= c.top + Math.sin(x * 1.1) * 0.5 + cu * cu * 2.2) return !this.caveOpen(x, d);
    if (d >= this.floorAt(x)) return true;
    for (const p of this.pil) {
      const dx = x - p.x, hw = p.hw * (1 + 0.18 * Math.sin(d * 1.7 + p.ph)) + (d > p.top ? (d - p.top) * 0.05 : 0);
      if (dx >= -hw && dx <= hw && d >= p.top + 1.4 * (dx / hw) * (dx / hw)) return true;
    }
    const L = this.ledge;
    if (x >= L.x0 && x <= L.x1) { const k = (x - L.x0) / (L.x1 - L.x0), top = L.d0 + Math.sin(x * 2.1) * 0.25 + (1 - k) * 0.4; if (d >= top && d <= L.d0 + 0.7 + 1.5 * k) return true; }
    return false;
  }
  // circle of radius r (m) touches rock?
  hits(x, d, r) {
    if (d + r < 3) return false;
    if (this.solid(x, d)) return true;
    for (let rr = r; rr > 0.05; rr -= 0.5) { // rings every 0.5 m so thin ledges are never stepped over
      const q = rr * 0.7071;
      if (this.solid(x + rr, d) || this.solid(x - rr, d) || this.solid(x, d + rr) || this.solid(x, d - rr) ||
        this.solid(x + q, d + q) || this.solid(x - q, d + q) || this.solid(x + q, d - q) || this.solid(x - q, d - q)) return true;
    }
    return false;
  }
  // fish avoid rock, channels (with margin) and the cave
  fishBlocked(x, d, r) {
    if (this.hits(x, d, r)) return true;
    for (const ch of this.channels) if (x >= ch.x0 - r && x <= ch.x1 + r && d >= ch.d0 - r && d <= ch.d1 + r) return true;
    return this.inCave(x, d);
  }
  // nearest open-water point to (x,d) for a body of radius r inside [dmin,dmax] (spiral search)
  openSpot(x, d, r, dmin = ZONE + 1, dmax = BOT - 1, pred = null) {
    const ok = (a, b) => b >= dmin && b <= dmax && a >= 1 && a <= 99 && (pred ? pred(a, b) : !this.fishBlocked(a, b, r + 0.5));
    if (ok(x, d)) return [x, d];
    for (let rad = 0.5; rad <= 30; rad += 0.5) for (let k = 0; k < 24; k++) {
      const a = k / 24 * Math.PI * 2, nx = x + Math.cos(a) * rad, nd = d + Math.sin(a) * rad * 0.6;
      if (ok(nx, nd)) return [nx, nd];
    }
    return [x, Math.max(dmin, Math.min(dmax, d))];
  }
  // free horizontal span around x at depths d±dd (for a patrol of a body of radius r): [left, right] in m
  freeSpan(x, d, r, dd = 0.7, max = 14) {
    const bad = (a) => a < 1 || a > 99 || this.fishBlocked(a, d - dd, r) || this.fishBlocked(a, d, r) || this.fishBlocked(a, d + dd, r);
    let L = 0, R = 0; if (bad(x)) return [0, 0];
    while (L < max && !bad(x - L - 0.25)) L += 0.25;
    while (R < max && !bad(x + R + 0.25)) R += 0.25;
    return [L, R];
  }
  // first rock below d=ZONE at x (for props on top of the terrain)
  topAt(x) { for (let d = ZONE + 0.5; d < BOT; d += 0.25) if (this.solid(x, d)) return d; return BOT; }

  // ---------- drawing ----------
  // bake rock into a world-pixel canvas (sx px/m horizontally, sy px/m vertically, d=0 at y=0)
  bake(sx, sy) {
    const tiles = img("bg/uw_tiles.png"), moss = ready(tiles);
    const w = Math.ceil(100 * sx) + 2, h = Math.ceil(BOT * sy) + 12;
    const cv = this.cv && this.cv.width === w ? this.cv : mkCanvas(w, h), g = cv.getContext("2d");
    g.clearRect(0, 0, w, h); g.imageSmoothingEnabled = false;
    const B = 2, cols = Math.ceil(w / B), rows = Math.ceil(h / B), y0 = Math.floor(ZONE * sy / B) - 1;
    // contract-zone edge outcrops (background decoration, translucent, no collision)
    g.globalAlpha = 0.6;
    for (let j = 0; j < 0; j++) {
      const d = j * B / sy;
      const wl = 1.6 + Math.sin(d * 0.45 + this.fa) * 0.9 + Math.sin(d * 1.3) * 0.4 + (d > 20 ? (d - 20) * 0.12 : 0);
      const wr = 1.4 + Math.sin(d * 0.5 + this.fb) * 0.8 + Math.sin(d * 1.1 + 2) * 0.4 + (d > 22 ? (d - 22) * 0.1 : 0);
      const xl = Math.round(wl * sx / B), xr = Math.round((100 - wr) * sx / B);
      g.fillStyle = "#43331f"; g.fillRect(0, j * B, xl * B, B); g.fillRect(xr * B, j * B, w - xr * B, B);
      g.fillStyle = "#5a4630"; g.fillRect(xl * B - B, j * B, B, B); g.fillRect(xr * B, j * B, B, B);
    }
    // little background rock clumps on the contract floor edges (30 m line), purely decorative
    for (const xm of [5, 13, 27, 71, 86, 94]) { const cx = xm * sx, cy = ZONE * sy; g.fillStyle = "#43331f"; g.beginPath(); g.ellipse(cx, cy, 14 + (xm % 3) * 5, 7 + (xm % 2) * 3, 0, Math.PI, 0); g.fill(); g.fillStyle = "#5a4630"; g.fillRect(Math.round(cx - 8), Math.round(cy - 6), 8, 1); }
    g.globalAlpha = 1;
    // deep-zone rock: per 2-px block, shaded by depth into the rock; cave interior = dark back wall
    const PAL = ["#5b8a35", "#3f6028", "#4a3d26", "#3a2f1e", "#2e2417", "#221a10"]; // mossy green top → olive-brown rock
    const SPAL = ["#4d6233", "#3b4a2a", "#3f3627", "#342c20", "#2b241a", "#231d15"]; // contract zone: darker, desaturated (background)
    const above = new Int16Array(cols); // solid blocks directly above (edge distance), per column
    for (let j = Math.floor(2 * sy / B); j < rows; j++) {
      const sh = (j + 0.5) * B / sy < ZONE;
      const d = (j + 0.5) * B / sy;
      for (let i = 0; i < cols; i++) {
        const x = (i + 0.5) * B / sx, s = this.solid(x, d);
        if (!s) {
          above[i] = 0;
          if (d > ZONE && this.inCave(x, d) && this.caveOpen(x, d)) { g.fillStyle = hash(i, j) < 0.15 ? "#1c140c" : "#130d07"; g.fillRect(i * B, j * B, B, B); }
          continue;
        }
        const e = above[i]++; const n = hash(i, j);
        let k = e === 0 ? 0 : e === 1 ? 1 : e < 4 ? 2 : e < 8 ? 3 : 4;
        if (k >= 3 && n < 0.12) k = 2; else if (k >= 2 && n > 0.9) k = 5;
        const side = !this.solid(x - B / sx, d) || !this.solid(x + B / sx, d), under = !this.solid(x, d + B / sy);
        g.fillStyle = sh ? (under ? "#19140e" : side && k > 1 ? "#3d3528" : SPAL[k]) : under ? "#1a130b" : side && k > 1 ? "#4f4129" : PAL[k];
        g.fillRect(i * B, j * B, B, B);
        // mossy lumps on top edges from the uw_tiles sea-floor strip (4-px slices), else procedural moss
        if (e === 0 && (d > ZONE + 0.3 || (sh && d > 3.2))) {
          g.globalAlpha = sh ? 0.55 : 1;
          if (moss && i % 2 === 0) { const sxx = 16 + ((i * 2 + (j & 7) * 13) % 172); g.drawImage(tiles, sxx, 110, 4, 22, i * B, j * B - 7, 4, 22); }
          else if (!moss) { g.fillStyle = "#6a9a3c"; g.fillRect(i * B, j * B - (n < 0.3 ? 2 : 0), B, n < 0.3 ? 2 : 1); }
          g.globalAlpha = 1;
        }
      }
    }
    // hanging roots + water hyacinth clumps on the bank cliffs near the surface
    for (const [x0, x1, s] of [[0, 4.2, 1], [95.8, 100, 2]]) for (let k = 0; k < 9; k++) {
      const x = (x0 + (x1 - x0) * (k + 0.5) / 9) * sx, len = (2.5 + hash(k, s) * 4.5) * sy;
      g.fillStyle = k % 2 ? "#5a4026" : "#6e5232";
      for (let y = 0; y < len; y += 1) g.fillRect(Math.round(x + Math.sin(y * 0.15 + k) * 1.5), Math.round(y), 1, 1);
      if (k % 3 === 0) { g.fillStyle = "#4f8a3a"; g.fillRect(Math.round(x) - 3, 0, 7, 2); g.fillStyle = "#79b04a"; g.fillRect(Math.round(x) - 2, 0, 3, 1); g.fillStyle = "#b98ac8"; g.fillRect(Math.round(x) + 1, 0, 1, 1); }
    }
    this.cv = cv; this.cvMoss = moss; this.cvS = sx;
    return cv;
  }
  // ox, oy: screen position of world (0, 0); visible part of the baked canvas only
  draw(c, ox, oy, sx, sy, W, H) {
    if (!this.cv || this.cvS !== sx || (!this.cvMoss && ready(img("bg/uw_tiles.png")))) this.bake(sx, sy);
    const cv = this.cv, X = Math.round(ox), Y = Math.round(oy);
    const s0 = Math.max(0, -X), t0 = Math.max(0, -Y), sw = Math.min(cv.width - s0, W - (X + s0)), sh = Math.min(cv.height - t0, H - (Y + t0));
    if (sw <= 0 || sh <= 0) return;
    const prev = c.imageSmoothingEnabled; c.imageSmoothingEnabled = false;
    c.drawImage(cv, s0, t0, sw, sh, X + s0, Y + t0, sw, sh);
    c.imageSmoothingEnabled = prev;
  }
  // crystals + clam (animated, a handful of draws)
  drawCave(c, ox, oy, sx, sy, t, W, H) {
    const cv = this.cave, px = ox + cv.cx * sx, py = oy + cv.id * sy;
    if (px < -200 || px > W + 200 || py < -100 || py > H + 100) return;
    c.save(); c.globalCompositeOperation = "lighter";
    for (const q of this.crystals) {
      const x = Math.round(ox + q.x * sx), y = Math.round(oy + q.d * sy), a = 0.55 + 0.35 * Math.sin(t * 2 + q.ph), s = q.s, dir = q.up ? -1 : 1;
      c.globalAlpha = a * 0.25; c.fillStyle = "#c8ff8a"; c.beginPath(); c.arc(x, y + dir * s, s * 2.6, 0, Math.PI * 2); c.fill();
      c.globalAlpha = a; c.fillStyle = "#e2ffa8";
      c.beginPath(); c.moveTo(x - s * 0.6, y); c.lineTo(x, y + dir * s * 2.2); c.lineTo(x + s * 0.6, y); c.closePath(); c.fill();
      c.fillStyle = "#fffbe0"; c.fillRect(x - 1, y + dir * s, 1, 2);
    }
    c.restore();
    const k = this.clam, x = Math.round(ox + k.x * sx), y = Math.round(oy + k.d * sy), open = k.open ? Math.min(1, k.t * 3) : 0.12 + 0.08 * Math.sin(t * 1.5);
    c.fillStyle = "#4a3a5a"; c.beginPath(); c.ellipse(x, y + 2, 9, 4, 0, 0, Math.PI); c.fill();          // bottom shell
    c.fillStyle = "#7a5f8a"; c.fillRect(x - 8, y + 1, 16, 1);
    if (!k.open || k.t < 3) { c.globalAlpha = k.open ? Math.max(0, 1 - k.t / 3) : 1; c.fillStyle = "#fff7e0"; c.beginPath(); c.arc(x, y, 2.5, 0, Math.PI * 2); c.fill(); c.globalAlpha = 0.3 + 0.2 * Math.sin(t * 4); c.fillStyle = "#ffe9a0"; c.beginPath(); c.arc(x, y, 5, 0, Math.PI * 2); c.fill(); c.globalAlpha = 1; }
    c.save(); c.translate(x - 9, y + 1); c.rotate(-open * 1.1); c.fillStyle = "#5c4870"; c.beginPath(); c.ellipse(9, 0, 9, 4, 0, Math.PI, 0); c.fill(); c.fillStyle = "#8d72a0"; c.fillRect(3, -3, 12, 1); c.restore();
  }

  // ---------- parallax backdrop (3 layers), cached procedural ridgelines ----------
  ridge(w, h, seed, col, colL, rough) {
    const cv = mkCanvas(w, h), g = cv.getContext("2d"), r = mulberry32(seed);
    const pk = []; for (let i = 0; i < 6; i++) pk.push([r() * w, 0.35 + r() * 0.55, 40 + r() * 90]);
    const top = new Float32Array(w);
    for (let x = 0; x < w; x++) {
      let y = 0.15; for (const [px, hh, ww] of pk) for (const o of [-w, 0, w]) { const u = (x - px - o) / ww; y = Math.max(y, hh * Math.exp(-u * u)); }
      y += Math.sin(x * 0.09 + seed) * 0.03 * rough + Math.sin(x * 0.31) * 0.015 * rough;
      top[x] = Math.round(h - y * h);
    }
    for (let x = 0; x < w; x++) { g.fillStyle = col; g.fillRect(x, top[x], 1, h - top[x]); g.fillStyle = colL; g.fillRect(x, top[x], 1, 1); }
    // a few arch holes / texture streaks
    g.fillStyle = "rgba(0,0,0,.18)"; for (let i = 0; i < 40; i++) { const x = Math.floor(r() * w), y = top[x] + 4 + Math.floor(r() * (h - top[x])); g.fillRect(x, y, 2 + Math.floor(r() * 6), 1); }
    return cv;
  }
  bakeBg() {
    const far = img("bg/uw_far.png"), mid = img("bg/uw_mid.png");
    if (!this.bg) this.bg = { farRidge: this.ridge(640, 120, 11 + this.seed, "#5a4630", "#6e5a3e", 1), nearRidge: this.ridge(720, 120, 37 + this.seed, "#2e2217", "#43331f", 2.5), mid: null, far: null };
    if (!this.bg.mid && ready(mid)) { // uw_mid at half size, tinted into the water colour
      const cv = mkCanvas(480, 256), g = cv.getContext("2d"); g.imageSmoothingEnabled = false; g.drawImage(mid, 0, 0, 480, 256);
      g.globalCompositeOperation = "source-atop"; g.fillStyle = "rgba(74,54,30,.62)"; g.fillRect(0, 0, 480, 256); this.bg.mid = cv; // brown silt wash
    }
    if (!this.bg.far && ready(far)) { // uw_far with a sepia / silt wash baked in
      const w = far.naturalWidth, h = far.naturalHeight, cv = mkCanvas(w, h), g = cv.getContext("2d"); g.imageSmoothingEnabled = false; g.drawImage(far, 0, 0);
      g.globalCompositeOperation = "source-atop"; g.fillStyle = "rgba(88,62,32,.7)"; g.fillRect(0, 0, w, h); this.bg.far = cv; }
  }
  // camX = camera x in world px, camY = vertical camera (px), vis = 0..1 (fades in with depth)
  drawBackdrop(c, camX, camY, W, H, vis, t, rays) {
    this.bakeBg(); const bg = this.bg, prev = c.imageSmoothingEnabled; c.imageSmoothingEnabled = false;
    const tile = (im, f, yb, a, fill) => {
      const w = im.width || im.naturalWidth, h = im.height || im.naturalHeight; if (!w) return;
      const y = Math.round(yb - h); if (y > H) return;
      let x = -Math.round((camX * f) % w); if (x > 0) x -= w;
      c.globalAlpha = a; for (; x < W; x += w) c.drawImage(im, x, y, w, h);
      if (fill && yb < H) { c.fillStyle = fill; c.fillRect(0, Math.round(yb), W, H - Math.round(yb) + 1); }
    };
    if (bg.far) tile(bg.far, 0.12, 345 - camY * 0.16, 0.12 + 0.45 * vis, null);
    tile(bg.farRidge, 0.2, 330 - camY * 0.2, 0.25 + 0.55 * vis, "#5a4630");
    if (rays) rays();
    if (bg.mid) tile(bg.mid, 0.5, 420 - camY * 0.33, 0.15 + 0.6 * vis, null);
    tile(bg.nearRidge, 0.7, 520 - camY * 0.6, 0.2 + 0.7 * vis, "#2e2217");
    c.globalAlpha = 1; c.imageSmoothingEnabled = prev;
  }
}
