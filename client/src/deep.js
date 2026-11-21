// "Sáng tạo của nhóm" — GUI-only deep zone below the contract river (d > 30 m).
// Not part of Test Contract v1.0: headless/game.contract.json stay at d ∈ [0,30].
// Deep species are bigger, slow-patrolling and yield the SAME ingredient kinds in larger amounts,
// so the kho file between gather and quán keeps its 4 kinds.

// Hunting (creative): every deep species has HP; the harpoon deals stats().spearDmg per hit. A hit that does not
// kill makes the fish flash, take knockback and flee (state "flee"); the boss Cá Tra Dầu charges instead.
// hp: hit points · reel: m/s the spear reels it in (bigger = slower) · flee: m/s while fleeing · fleeS: flee time
export const DEEP = {
  depth: 60,            // client map depth (m)
  zone: 30,             // below this = deep zone
  pressure: 1.5,        // O₂ drain multiplier in the deep zone
  species: [
    { id: "ca_loc_bong", name: "Cá lóc bông", kind: "ca_loc", yield: 3, sprite: "sprites/fish_snakehead.png", fw: 48, fh: 16, frames: 1, facesLeft: true, scale: 1.1, radius: 2.6, speed: 1.1, range: 7,
      hp: 4, reel: 11, flee: 4.2, fleeS: 2,
      spawns: [[18, 36], [52, 40], [84, 34]] },
    { id: "dan_ca_linh_lon", name: "Đàn cá linh lớn", kind: "ca_linh", yield: 6, sprite: "sprites/fish_silver.png", fw: 16, fh: 16, frames: 1, facesLeft: true, scale: 0.9, radius: 2.8, speed: 1.4, range: 9, school: 6,
      hp: 3, reel: 11, flee: 4.6, fleeS: 2,
      spawns: [[30, 44], [66, 46], [92, 42]] },
    // big and heavy: flees slower than the diver swims (4 m/s), and bites back when the diver is within biteR
    { id: "ca_loc_khong_lo", name: "Cá lóc khổng lồ", kind: "ca_loc", yield: 5, sprite: "sprites/fish_big_anim.png", fw: 54, fh: 49, frames: 4, facesLeft: false, scale: 0.75, radius: 3.2, speed: 0.8, range: 6,
      hp: 8, reel: 8, flee: 3.2, fleeS: 1.6, biteR: 2,
      spawns: [[40, 55], [76, 56]] },
  ],
  // Boss: giant Mekong catfish. One per dive at 52–58 m, slow patrol; when hit it charges the diver for chargeS
  // (contact = −1 Máu + knockback). No ingredients (the kho keeps the contract kinds): sold to the trader for bounty k.
  boss: { id: "ca_tra_dau", name: "Cá Tra Dầu", kind: null, yield: 0, boss: true, sprite: "sprites/fish_catfish.png", fw: 32, fh: 16, frames: 1, facesLeft: true,
    scale: 3.75, radius: 4.6, hitR: 3.2, speed: 0.7, range: 10, hp: 20, reel: 5, flee: 3, fleeS: 1.2,
    charge: 5.5, chargeS: 1.5, contactR: 2.8, push: 2.5, bounty: 300, depths: [52, 58], xs: [15, 85] },
};

const IMG = {};
export function preloadDeep() {
  for (const sp of [...DEEP.species, DEEP.boss]) if (!IMG[sp.sprite]) { const im = new Image(); im.src = "assets/" + sp.sprite; IMG[sp.sprite] = im; }
  props();
}

// start already on the patrol curve (x = home + sin(phase)·range), so the first update does not teleport it
function mk(id, sp, x, d, phase) { return { id, sp, kind: sp.kind, x: Math.max(1, Math.min(99, x + Math.sin(phase) * sp.range)), d, hx: x, hd: d, range: sp.range, face: 1, caught: false, phase, hp: sp.hp || 1, hpMax: sp.hp || 1, state: "patrol", st: 0, vx: 0, vd: 0, flash: 0, hpShow: 0 }; }
// collision radius of a deep fish against terrain (m)
export const bodyR = (f) => f.sp.boss ? 1.9 : f.sp.school ? 1.4 : Math.max(0.9, (f.sp.hitR ?? f.sp.radius * 0.7) * 0.6);
// terrain (terrain.js): move every spawn into open water (away from rock, current channels and the cave) and
// shrink / recentre each patrol so the whole sway path stays clear of rock
export function placeDeep(list, ter, maxD = DEEP.depth) {
  for (const f of list) {
    const [d0, d1] = band(f, maxD), r = bodyR(f);
    const fits = (a, b) => !ter.fishBlocked(a, b, r + 0.3) && !ter.fishBlocked(a, b - 0.7, r) && !ter.fishBlocked(a, b + 0.7, r);
    const [x, d] = ter.openSpot(f.hx, Math.max(d0 + 0.7, Math.min(d1 - 0.7, f.hd)), r, d0 + 0.7, d1 - 0.7, fits);
    const [L, R] = ter.freeSpan(x, d, r, 0.7, f.sp.range + 8);
    const c = Math.max(1, Math.min(99, x + (R - L) / 2)), half = (L + R) / 2;
    f.hx = c; f.hd = d; f.range = Math.max(0.2, Math.min(f.sp.range, half - 0.3));
    f.x = Math.max(1, Math.min(99, f.hx + Math.sin(f.phase) * f.range)); f.d = d;
  }
}
export function makeDeepFish(rand = Math.random) {
  const out = []; let n = 0;
  for (const sp of DEEP.species) for (const [x, d] of sp.spawns) { n++; out.push(mk("D" + n, sp, x, d, n * 1.3)); }
  const b = DEEP.boss; // one boss per dive, random spot in its band
  out.push(mk("B1", b, b.xs[0] + rand() * (b.xs[1] - b.xs[0]), b.depths[0] + rand() * (b.depths[1] - b.depths[0]), rand() * 6));
  return out;
}

// called by the scene when a hit does not kill: knockback along the spear (kx,kd unit), then flee or charge
export function hurtDeepFish(f, dmg, kx, kd) {
  f.hp = Math.max(0, f.hp - dmg); f.flash = 0.3; f.hpShow = 3;
  f.vx = kx * 7; f.vd = kd * 7;
  if (f.sp.boss) { f.state = "charge"; f.st = f.sp.chargeS; } else { f.state = "flee"; f.st = f.sp.fleeS; }
}

function band(f, maxD) { return f.sp.boss ? [f.sp.depths[0] - 2, Math.min(maxD - 3, f.sp.depths[1] + 1)] : [DEEP.zone + 1, maxD - 1]; }
// patrol: slow sway around home; never faster than the diver, so they are always catchable.
// env (optional): { px, pd, contact(f) } — diver position for flee/charge and the boss contact callback.
export function updateDeepFish(list, dt, maxD, env) {
  for (const f of list) {
    if (f.caught) continue;
    const sp = f.sp, [d0, d1] = band(f, maxD);
    if (f.flash > 0) f.flash -= dt;
    if (f.hpShow > 0) f.hpShow -= dt;
    const ox = f.x, od = f.d, rng = f.range ?? sp.range, tx = f.hx + Math.sin(f.phase) * rng, td = Math.max(d0, Math.min(d1, f.hd + Math.sin(f.phase * 2.3) * 0.6));
    if ((f.state === "flee" || f.state === "charge") && env) {
      f.st -= dt;
      const dx = env.px - f.x, dd = env.pd - f.d, r = Math.hypot(dx, dd) || 1e-6;
      const s = f.state === "charge" ? sp.charge : -sp.flee, k = Math.min(1, dt * (f.state === "charge" ? 5 : 4));
      f.vx += (dx / r * s - f.vx) * k; f.vd += (dd / r * s - f.vd) * k;
      f.x += f.vx * dt; f.d += f.vd * dt;
      if (Math.abs(f.vx) > 0.1) f.face = f.vx > 0 ? 1 : -1;
      if (f.state === "charge" && r <= sp.contactR) { env.contact?.(f, dx / r, dd / r); f.state = "flee"; f.st = 1; }
      else if (f.st <= 0) f.state = "return";
    } else if (f.state === "return" || f.state === "flee" || f.state === "charge") {
      const dx = tx - f.x, dd = td - f.d, r = Math.hypot(dx, dd), step = sp.speed * 2.5 * dt;
      f.vx = 0; f.vd = 0;
      if (r <= step + 0.05) f.state = "patrol"; else { f.x += dx / r * step; f.d += dd / r * step; if (Math.abs(dx) > 0.05) f.face = dx > 0 ? 1 : -1; }
      // blocked on the way home: slide along one axis (try d first — rock is mostly below)
      if (env?.blocked?.(f.x, f.d, bodyR(f))) { f.x = ox; if (env.blocked(f.x, f.d, bodyR(f))) { f.d = od; f.x = ox + dx / r * step; if (env.blocked(f.x, f.d, bodyR(f))) { f.x = ox; f.d = od - step; if (env.blocked(f.x, f.d, bodyR(f))) f.d = od; } } }
    } else {
      f.phase += dt * sp.speed / rng;
      f.face = Math.cos(f.phase) >= 0 ? 1 : -1;
      f.x = Math.min(99, tx); f.d = td;
    }
    f.x = Math.max(1, Math.min(99, f.x)); f.d = Math.max(d0, Math.min(d1, f.d));
    // terrain: flee / charge / patrol never enter rock (or, for fish, the current channels): stop at the surface
    if (env?.blocked && (f.x !== ox || f.d !== od) && env.blocked(f.x, f.d, bodyR(f))) {
      const r = bodyR(f);
      if (!env.blocked(f.x, od, r)) f.d = od; else if (!env.blocked(ox, f.d, r)) f.x = ox; else { f.x = ox; f.d = od; }
      f.vx *= 0.3; f.vd *= 0.3;
    }
  }
}

// white / red silhouettes of a sprite sheet for the hit flash (built once per image + colour)
const TINT = new Map();
function tinted(im, col) {
  const key = im.src + col; let cv = TINT.get(key);
  if (!cv) {
    cv = document.createElement("canvas"); cv.width = im.naturalWidth || im.width; cv.height = im.naturalHeight || im.height;
    const g = cv.getContext("2d"); g.drawImage(im, 0, 0); g.globalCompositeOperation = "source-in"; g.fillStyle = col; g.fillRect(0, 0, cv.width, cv.height);
    TINT.set(key, cv);
  }
  return cv;
}

// draw centred at (x,y) in pixel-world space, facing +1 = right
export function drawDeepFish(c, f, x, y, t) {
  const sp = f.sp, im = IMG[sp.sprite];
  if (!im || !im.complete || !im.naturalWidth) { c.fillStyle = "#334"; c.fillRect(x - 8, y - 3, 16, 6); return; }
  const n = sp.school || 1, prevSmooth = c.imageSmoothingEnabled; c.imageSmoothingEnabled = false;
  const src = f.flash > 0 ? tinted(im, Math.floor(f.flash * 20) % 2 ? "#ff5a5a" : "#ffffff") : im;
  const charging = f.state === "charge";
  for (let i = 0; i < n; i++) {
    const ox = n > 1 ? Math.cos(i * 2.1 + t) * 9 + (i % 3) * 6 - 6 : 0, oy = n > 1 ? Math.sin(i * 1.7 + t * 1.3) * 5 + (i % 2) * 6 - 3 : 0;
    const frame = sp.frames > 1 ? Math.floor(t * 6 + i) % sp.frames : 0;
    const w = sp.fw * sp.scale, h = sp.fh * sp.scale;
    const flip = (f.face === 1) === sp.facesLeft; // sprite faces left: flip to face right
    c.save(); c.translate(Math.round(x + ox), Math.round(y + oy + Math.sin(t * 2 + i) * 1));
    if (flip) c.scale(-1, 1);
    if (charging) c.rotate(Math.sin(t * 30) * 0.04);
    c.drawImage(src, frame * sp.fw, 0, sp.fw, sp.fh, -w / 2, -h / 2, w, h);
    c.restore();
  }
  c.imageSmoothingEnabled = prevSmooth;
}
// half-size of a deep fish on screen (px) — for HP bars / aim rings
export const deepBox = (f) => ({ w: f.sp.fw * f.sp.scale / 2 + (f.sp.school ? 10 : 0), h: f.sp.fh * f.sp.scale / 2 + (f.sp.school ? 6 : 0) });

// ---- deep scenery: sparse ledges with kelp, atlas props and glowing motes so 30–60 m is not empty ----
// Atlas rects from assets/manifest.json (bg/uw_props.png, CC0 ansimuz). Drawn with imageSmoothing off.
const PROPS = "bg/uw_props.png";
const RECT = { kelp: [614, 317, 52, 67], bush: [434, 332, 46, 51], coral: [514, 327, 48, 56], rockA: [49, 95, 85, 98], rockB: [33, 334, 85, 98] };
// [x m, d m, prop, scale] — props sit on a small rock ledge at that depth
const SCENERY = [
  [8, 38, "kelp", 0.45], [14, 49, "rockA", 0.28], [23, 33, "coral", 0.4], [34, 52, "bush", 0.45], [41, 37, "rockB", 0.26],
  [49, 45, "kelp", 0.5], [58, 34, "bush", 0.4], [63, 51, "coral", 0.45], [72, 41, "rockA", 0.3], [80, 47, "kelp", 0.45],
  [87, 36, "coral", 0.4], [95, 50, "rockB", 0.28],
];
// procedural kelp tufts on ledges between the props: [x, d, height px]
const TUFTS = [[4, 44, 22], [19, 41, 30], [29, 47, 18], [45, 55, 26], [54, 39, 20], [69, 44, 28], [77, 35, 16], [91, 43, 24]];
const MOTES = 28, mote = new Float32Array(MOTES * 3); // x m, d m, phase
for (let i = 0; i < MOTES; i++) { mote[i * 3] = (i * 37.3) % 100; mote[i * 3 + 1] = DEEP.zone + 2 + ((i * 13.7) % (DEEP.depth - DEEP.zone - 4)); mote[i * 3 + 2] = i * 1.37; }
let propsImg = null;
function props() { if (!propsImg) { propsImg = new Image(); propsImg.src = "assets/" + PROPS; } return propsImg; }

// screen x = ox + x*sx, screen y = oy + d*sy; kelp/rock come from art.js (passed in so deep.js stays art-agnostic)
// kelp bent by the water: shear around its base (lean −1..1, + = toward +x)
function leanKelp(c, kelp, x, y, h, t, lean, a, b) {
  if (Math.abs(lean) < 0.02) return kelp(c, x, y, h, t, a, b);
  c.save(); c.translate(0, y); c.transform(1, 0, -lean * 0.9, 1, 0, 0); kelp(c, x, 0, h, t, a, b); c.restore();
}
export { leanKelp };
// ter (terrain.js, optional): props / tufts sit on the terrain top at their x; leanAt(x, d) → kelp lean
const TOPS = new WeakMap();
export function drawDeepScenery(c, ox, oy, sx, sy, t, W, H, kelp, rock, ter = null, leanAt = null) {
  const im = props(), ok = im.complete && im.naturalWidth > 0;
  let tops = ter && TOPS.get(ter);
  if (ter && !tops) { tops = { t: TUFTS.map(([x]) => ter.topAt(x)), s: SCENERY.map(([x]) => ter.topAt(x)) }; TOPS.set(ter, tops); }
  const prevSmooth = c.imageSmoothingEnabled; c.imageSmoothingEnabled = false;
  for (let i = 0; i < TUFTS.length; i++) {
    const x = TUFTS[i][0], d = tops ? tops.t[i] : TUFTS[i][1], h = TUFTS[i][2];
    const px = Math.round(ox + x * sx), py = Math.round(oy + d * sy) + (tops ? 1 : 0);
    if (px < -30 || px > W + 30 || py < -h || py > H + h) continue;
    const ln = leanAt ? leanAt(x, d - 1) : 0;
    if (!tops) rock(c, px, py + 2, 12, 5, "#1b2733", "#2c3d4c");
    leanKelp(c, kelp, px - 3, py, h, t, ln, "#1d4a3a", "#2f6a50"); leanKelp(c, kelp, px + 4, py, h * 0.7, t + 1, ln, "#1d4a3a", "#2f6a50");
  }
  for (let i = 0; i < SCENERY.length; i++) {
    const [x, d0, k, s] = SCENERY[i], d = tops ? tops.s[i] : d0;
    const r = RECT[k], w = r[2] * s, h = r[3] * s, px = Math.round(ox + x * sx), py = Math.round(oy + d * sy) + (tops ? 2 : 0);
    if (px < -w || px > W + w || py < -10 || py > H + h) continue;
    if (!tops) rock(c, px, py + 1, w * 0.6, 4, "#16212c", "#26384a");
    if (ok) { c.globalAlpha = 0.8; c.drawImage(im, r[0], r[1], r[2], r[3], Math.round(px - w / 2), Math.round(py - h), Math.round(w), Math.round(h)); c.globalAlpha = 1; }
  }
  c.imageSmoothingEnabled = prevSmooth;
  // glowing motes (bioluminescent plankton): fixed fill, alpha pulses
  c.fillStyle = "#d9f08a"; // soft yellow-green
  for (let i = 0; i < MOTES; i++) {
    const ph = mote[i * 3 + 2], x = mote[i * 3] + Math.sin(t * 0.3 + ph) * 1.5, d = mote[i * 3 + 1] + Math.sin(t * 0.5 + ph * 2) * 0.8;
    const px = ox + x * sx, py = oy + d * sy;
    if (px < 0 || px > W || py < 0 || py > H) continue;
    const a = 0.25 + 0.55 * (0.5 + 0.5 * Math.sin(t * 2.2 + ph * 3));
    c.globalAlpha = a; c.fillRect(Math.round(px), Math.round(py), i % 4 ? 1 : 2, i % 4 ? 1 : 2);
    if (i % 4 === 0) { c.globalAlpha = a * 0.3; c.fillRect(Math.round(px) - 1, Math.round(py) - 1, 4, 4); }
  }
  c.globalAlpha = 1;
}
