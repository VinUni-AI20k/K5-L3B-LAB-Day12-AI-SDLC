// "Sáng tạo của nhóm" — GUI-only deep zone below the contract river (d > 30 m).
// Not part of Test Contract v1.0: headless/game.contract.json stay at d ∈ [0,30].
// Deep species are bigger, slow-patrolling and yield the SAME ingredient kinds in larger amounts,
// so the kho file between gather and quán keeps its 4 kinds.

export const DEEP = {
  depth: 60,            // client map depth (m)
  zone: 30,             // below this = deep zone
  pressure: 1.5,        // O₂ drain multiplier in the deep zone
  species: [
    { id: "ca_loc_bong", name: "Cá lóc bông", kind: "ca_loc", yield: 3, sprite: "sprites/fish_snakehead.png", fw: 48, fh: 16, frames: 1, facesLeft: true, scale: 1.1, radius: 2.6, speed: 1.1, range: 7,
      spawns: [[18, 36], [52, 40], [84, 34]] },
    { id: "dan_ca_linh_lon", name: "Đàn cá linh lớn", kind: "ca_linh", yield: 6, sprite: "sprites/fish_silver.png", fw: 16, fh: 16, frames: 1, facesLeft: true, scale: 0.9, radius: 2.8, speed: 1.4, range: 9, school: 6,
      spawns: [[30, 44], [66, 46], [92, 42]] },
    { id: "ca_loc_khong_lo", name: "Cá lóc khổng lồ", kind: "ca_loc", yield: 5, sprite: "sprites/fish_big_anim.png", fw: 54, fh: 49, frames: 4, facesLeft: false, scale: 0.75, radius: 3.2, speed: 0.8, range: 6,
      spawns: [[40, 55], [76, 56]] },
  ],
};

const IMG = {};
export function preloadDeep() {
  for (const sp of DEEP.species) if (!IMG[sp.sprite]) { const im = new Image(); im.src = "assets/" + sp.sprite; IMG[sp.sprite] = im; }
  props();
}

export function makeDeepFish() {
  const out = []; let n = 0;
  for (const sp of DEEP.species) for (const [x, d] of sp.spawns) out.push({ id: "D" + ++n, sp, kind: sp.kind, x, d, hx: x, hd: d, face: 1, caught: false, phase: n * 1.3 });
  return out;
}

// slow patrol around home; never faster than the diver, so they are always catchable
export function updateDeepFish(list, dt, maxD) {
  for (const f of list) {
    if (f.caught) continue;
    f.phase += dt * f.sp.speed / f.sp.range;
    const nx = f.hx + Math.sin(f.phase) * f.sp.range;
    f.face = Math.cos(f.phase) >= 0 ? 1 : -1;
    f.x = Math.max(1, Math.min(99, nx));
    f.d = Math.max(DEEP.zone + 1, Math.min(maxD - 1, f.hd + Math.sin(f.phase * 2.3) * 0.6));
  }
}

// draw centred at (x,y) in pixel-world space, facing +1 = right
export function drawDeepFish(c, f, x, y, t) {
  const sp = f.sp, im = IMG[sp.sprite];
  if (!im || !im.complete || !im.naturalWidth) { c.fillStyle = "#334"; c.fillRect(x - 8, y - 3, 16, 6); return; }
  const n = sp.school || 1;
  for (let i = 0; i < n; i++) {
    const ox = n > 1 ? Math.cos(i * 2.1 + t) * 9 + (i % 3) * 6 - 6 : 0, oy = n > 1 ? Math.sin(i * 1.7 + t * 1.3) * 5 + (i % 2) * 6 - 3 : 0;
    const frame = sp.frames > 1 ? Math.floor(t * 6 + i) % sp.frames : 0;
    const w = sp.fw * sp.scale, h = sp.fh * sp.scale;
    const flip = (f.face === 1) === sp.facesLeft; // sprite faces left: flip to face right
    c.save(); c.translate(Math.round(x + ox), Math.round(y + oy + Math.sin(t * 2 + i) * 1));
    if (flip) c.scale(-1, 1);
    c.drawImage(im, frame * sp.fw, 0, sp.fw, sp.fh, -w / 2, -h / 2, w, h);
    c.restore();
  }
}

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
export function drawDeepScenery(c, ox, oy, sx, sy, t, W, H, kelp, rock) {
  const im = props(), ok = im.complete && im.naturalWidth > 0;
  const prevSmooth = c.imageSmoothingEnabled; c.imageSmoothingEnabled = false;
  for (const [x, d, h] of TUFTS) {
    const px = Math.round(ox + x * sx), py = Math.round(oy + d * sy);
    if (px < -30 || px > W + 30 || py < -h || py > H + 20) continue;
    rock(c, px, py + 2, 12, 5, "#1b2733", "#2c3d4c"); kelp(c, px - 3, py, h, t, "#1d4a3a", "#2f6a50"); kelp(c, px + 4, py, h * 0.7, t + 1, "#1d4a3a", "#2f6a50");
  }
  for (const [x, d, k, s] of SCENERY) {
    const r = RECT[k], w = r[2] * s, h = r[3] * s, px = Math.round(ox + x * sx), py = Math.round(oy + d * sy);
    if (px < -w || px > W + w || py < -10 || py > H + h) continue;
    rock(c, px, py + 1, w * 0.6, 4, "#16212c", "#26384a");
    if (ok) { c.globalAlpha = 0.8; c.drawImage(im, r[0], r[1], r[2], r[3], Math.round(px - w / 2), Math.round(py - h), Math.round(w), Math.round(h)); c.globalAlpha = 1; }
  }
  c.imageSmoothingEnabled = prevSmooth;
  // glowing motes (bioluminescent plankton): fixed fill, alpha pulses
  c.fillStyle = "#9dffe0";
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
