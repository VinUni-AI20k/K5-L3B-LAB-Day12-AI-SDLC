// Procedural pixel art. Everything draws on the low-res `px` canvas with integer rects, so it reads as pixel art.
import { W, H, lerp } from "./engine.js";

export const P = {
  ink: "#1a1220", white: "#fff6e8",
  skin: "#eaa57a", skinD: "#c97a52",
  hair: "#2a1d2b", hairL: "#4a3348",
  suit: "#1aa6a0", suitD: "#11706f", suitL: "#5fd6c4",
  orange: "#ff8a3d", orangeD: "#d9582a",
  mask: "#ffd23f", lens: "#a6f0ff",
  wood: "#8a5a33", woodD: "#5e3a20", woodL: "#b07a48",
  red: "#d94a3d", redD: "#9e2d2a", gold: "#f3c454",
  leaf: "#3f9a4a", leafD: "#2a6b38", leafL: "#79c75a",
  pink: "#ff8fb1", pinkD: "#e0567f", pinkL: "#ffd0de",
  yellow: "#ffd23a", yellowD: "#e0a21a",
  silver: "#d4e8f2", silverD: "#8fb0c4",
  loc: "#55603e", locD: "#2f3826", locL: "#8a9a5a",
  straw: "#e9cf8a", strawD: "#c4a35e",
  keo: "#8a7a66", keoD: "#5a4c3e", keoL: "#b0a28a",
};

export const R = (c, x, y, w, h, col) => { c.fillStyle = col; c.fillRect(Math.round(x), Math.round(y), w, h); };

function hexRgb(h) { const n = parseInt(h.slice(1), 16); return [n >> 16, (n >> 8) & 255, n & 255]; }
export function mix(a, b, t) {
  const A = hexRgb(a), B = hexRgb(b);
  return `rgb(${Math.round(lerp(A[0], B[0], t))},${Math.round(lerp(A[1], B[1], t))},${Math.round(lerp(A[2], B[2], t))})`;
}

// Quantized vertical gradient with a checker dither between bands (pixel-art look).
export function bands(c, x, y, w, h, stops, n = 10) {
  const bh = h / n;
  for (let i = 0; i < n; i++) {
    const t = i / (n - 1);
    let k = 0; while (k < stops.length - 2 && t > stops[k + 1][0]) k++;
    const [t0, c0] = stops[k], [t1, c1] = stops[k + 1];
    const col = mix(c0, c1, (t - t0) / (t1 - t0 || 1));
    const y0 = Math.round(y + i * bh), y1 = Math.round(y + (i + 1) * bh);
    c.fillStyle = col; c.fillRect(x, y0, w, y1 - y0);
    if (i > 0) {
      c.fillStyle = c._prev || col;
      for (let xx = x + ((y0 / 1) & 1); xx < x + w; xx += 2) c.fillRect(xx, y0, 1, 1);
    }
    c._prev = col;
  }
  c._prev = null;
}

// ---------- pixel maps (portraits, icons) ----------
const PAL = {
  k: P.ink, h: P.hair, H: P.hairL, s: P.skin, S: P.skinD, w: P.white, e: P.ink, p: "#f07a7a", m: "#a8403a",
  y: P.mask, l: P.lens, L: "#e8fdff", t: P.suit, T: P.suitD, o: P.orange,
  g: "#c9c2d4", G: "#8a8399", v: "#7a4fa0", V: "#57357a", n: P.straw, N: P.strawD,
  b: "#3a6fd8", B: "#24479a", r: P.red, R: P.redD, c: "#f2efe6", C: "#b9b2a0", f: P.yellow, F: P.yellowD,
  x: P.leaf, X: P.leafD, i: P.pink, I: P.pinkD, u: P.loc, U: P.locD, z: P.silver, Z: P.silverD, a: P.wood, A: P.woodD, q: "#f7b733",
  // v1.1 kinds/dishes: cá kèo brown-grey, canh chua orange-red, lẩu mắm dark clay + broth
  j: P.keo, J: P.keoD, O: "#e8642a", Q: "#ff9a4a", D: "#3a2622", E: "#6a4434", M: "#7a4a2a", K: "#a8683a",
};
const cache = new Map();
export function pmap(key, rows) {
  if (cache.has(key)) return cache.get(key);
  const w = Math.max(...rows.map((r) => r.length)), h = rows.length;
  const cv = document.createElement("canvas"); cv.width = w; cv.height = h;
  const c = cv.getContext("2d");
  rows.forEach((row, y) => [...row.padEnd(w, ".")].forEach((ch, x) => { if (PAL[ch]) { c.fillStyle = PAL[ch]; c.fillRect(x, y, 1, 1); } }));
  cache.set(key, cv);
  return cv;
}

export const PORTRAITS = {
  sen: [
    "........kkkkkkkk........",
    "......kkhhhhhhhhkk......",
    ".....khhhHHhhhhhhhk.....",
    "....khhyyyyyyyyyyhhk....",
    "....khylLllyylLlyyhhk...",
    "...khhyllllyyllllyhhk...",
    "...khhhyyyyhhyyyyhhhhk..",
    "...khhssssssssssssshhk..",
    "...khsswwssssswwsssshk..",
    "...khsswessssswesssshkk.",
    "...khssssssssssssssshhok",
    "...kSspsssssssssspssshok",
    "....kSsssssmmssssssShkok",
    "....kSSsssssssssssSSk.k.",
    ".....kkSSsssssssSSkk....",
    ".......kkSSSSSSSkk......",
    "......ktkkSSSSSkktk.....",
    ".....kttttkkkkkttttk....",
    "....kttoTtttttttToTtk...",
    "...kttTottttttttToTttk..",
    "..kttTTottttttttToTTttk.",
    "..kttTTottttttttToTTttk.",
    "..kttTTottttttttToTTttk.",
    "..kkkkkkkkkkkkkkkkkkkkk.",
  ],
  ba: [
    ".........kkkkkk.........",
    "........kggggggk........",
    ".......kgGgggGggk.......",
    "........kkggggkk........",
    ".....kkkggggggggkkk.....",
    "....kgggggGGGGgggggk....",
    "...kgggGGssssssGGgggk...",
    "...kggGssssssssssGggk...",
    "...kgGsssSssssSsssGgk...",
    "...kgssskkksskkkssssgk..",
    "...kgsssssssssssssssgk..",
    "...kgspsssssSsssssspsgk.",
    "....kSssssskmmmksssssk..",
    "....kSSsssssssssssSSk...",
    ".....kSSSssssssssSSk....",
    "......kkSSSSSSSSSkk.....",
    ".....kvkkkSSSSSkkkvk....",
    "....kvvvvvkkkkkvvvvvk...",
    "...kvvVvvvvwvvvvvVvvvk..",
    "..kvvVVvvvvwvvvvvVVvvvk.",
    "..kvvVVvvvvwvvvvvVVvvvk.",
    "..kvvVVvvvvwvvvvvVVvvvk.",
    "..kvvVVvvvvwvvvvvVVvvvk.",
    "..kkkkkkkkkkkkkkkkkkkkk.",
  ],
  khach: [
    "...........kk...........",
    "..........knnk..........",
    ".........knNnnk.........",
    "........knnNnnnk........",
    ".......knnnNnnnnk.......",
    "......knnnnNnnnnnk......",
    "....kknnnnnNnnnnnnkk....",
    "..kkNNNNNNNNNNNNNNNNkk..",
    "....kkkhhhhhhhhhhkkk....",
    ".....khssssssssssshk....",
    ".....kssweksssweksk.....",
    ".....ksssssssssssssk....",
    ".....kspssssSsssspsk....",
    ".....kSsssskkkksssSk....",
    "......kSssskmmksssk.....",
    ".......kkSSSSSSSkk......",
    "......kbkkSSSSSkkbk.....",
    ".....kbbbbkkkkkbbbbk....",
    "....kbbBbbbbwbbbbBbbk...",
    "...kbbBBbbbbwbbbbBBbbk..",
    "..kbbbBBbbbbwbbbbBBbbbk.",
    "..kbbbBBbbbbwbbbbBBbbbk.",
    "..kbbbBBbbbbwbbbbBBbbbk.",
    "..kkkkkkkkkkkkkkkkkkkkk.",
  ],
};

// 10x10 item icons (hold slots, stock, recipes)
export const ICONS = {
  ca_linh: ["..........", "..........", "...zzzz...", ".ZzzzzzzZ.", "ZzezzzzzzZ", ".zzzzzzzzZ", "..ZZZZZ.Z.", "..........", "..........", ".........."],
  ca_loc: ["..........", "..........", ".uuUuUuu..", "uuuuuuuuuU", "eUuUuUuUuu", "uuuuuuuuuU", ".UUUUUUU..", "..........", "..........", ".........."],
  bong_dien_dien: ["....x.....", "...xfx....", "..fFfx.f..", "..fFf.fFf.", "...f.xfFf.", "....x..f..", "....x.x...", "....xx....", "....x.....", "....x....."],
  bong_sung: ["....ii....", "...iIIi...", "..iiIIii..", ".iIiiiiIi.", "..iiqqii..", "...iqqi...", "....xx....", "....x.....", "..xxxxxx..", ".XxxxxxxX."],
  ca_keo: ["..........", "..k..k....", ".jkjJkjJ..", "jjjjjjjjJ.", "JjJjJjJjjJ", ".JJJJJJJ.J", "..........", ".k........", "jkjjjjjJ..", ".JJJJJJ.J."],
  keo_neo: ["..f...f...", ".fFx.xfF..", "..xXxXx...", ".xXxxxXx..", "xXx.x.xXx.", ".x..x..x..", "..x.x.x...", "...xxx....", "....X.....", "....X....."],
};
// 16x16 dish icons
export const DISHES = {
  ca_loc_nuong_trui: [
    "................", "................", "....n.n..n.n....", "...nNnNnnNnNn...",
    "..AuuuuuuuuuuA..", ".AuUuUuUuUuUuuA.", "AeuuuuuuuuuuuuuA", ".AuUuUuUuUuUuuA.",
    "..AuuuuuuuuuuA..", "...nNnNnnNnNn...", "..cccccccccccc..", ".ccCCCCCCCCCCcc.",
    "..cccccccccccc..", "................", "................", "................",
  ],
  goi_bong_sung: [
    "................", "......x..x......", ".....xix.xi.....", "....xiIxxIix....",
    "...ixIiirriIxi..", "...xIixrrrxiIx..", "..ccxiIixIixicc.", ".cccxxxxxxxxxccc",
    "cccccccccccccccc", ".cCCCCCCCCCCCCc.", "..cccccccccccc..", "................",
    "................", "................", "................", "................",
  ],
  lau_ca_linh_dien_dien: [
    "......c..c......", ".....c..c..c....", "......c..c......", "..AAAAAAAAAAAA..",
    ".AqqfqqzZqfqqqA.", ".AqfFqzzzqqfFqA.", ".AqqqZzzzZqqqqA.", ".AqfqqqzqqqfqqA.",
    "AAAAAAAAAAAAAAAA", "aAaaaaaaaaaaaaAa", ".aaaaaaaaaaaaaa.", "..aAaaaaaaaaAa..",
    "...rRrRrRrRrRr..", "..rqrqrqrqrqrqr.", "................", "................",
  ],
};
// v1.1 dishes
DISHES.canh_chua_ca_loc = [
  "................", "......c..c......", ".....c..c..c....", "................",
  "..cccccccccccc..", ".cOOfOOuuOOfOOc.", ".cOfFfOuUuOfFfc.", ".cOOfOxOuOxOfOc.",
  ".cQOOOOOOOOOOQc.", "..cOOOOOOOOOOc..", "...ccccccccccc..", "....cCCCCCCCc...",
  ".....cccccccc...", "................", "................", "................",
];
DISHES.ca_keo_nuong = [
  "................", "................", "...r.....r......", "..jjjjjjjjjk....",
  "aaJjrjJjrjJjjaaa", "..jjjjjjjjjk....", "...J.r..J.r.....", "................",
  "....r...r.......", "..jjjjjjjjjk....", "aaJjrjJjrjJjjaaa", "..jjjjjjjjjk....",
  "...J..r..J......", "..nnnnnnnnnnnn..", ".nNNNNNNNNNNNNn.", "..nnnnnnnnnnnn..",
];
DISHES.lau_mam = [
  ".....C...C......", "....C...C...C...", ".....C...C......", ".EEEEEEEEEEEEEE.",
  "EDMMfMMxxMMjMMDE", "EDMxXMMfMMjjMMDE", "EDMMMxMMMfMMxMDE", "EDMjMMMxXMMMMMDE",
  "EEEEEEEEEEEEEEEE", "DDKDDDDDDDDDDKDD", ".DDDDDDDDDDDDDD.", "..DKDDDDDDDDKD..",
  "...rRrRrRrRrRr..", "..rqrqrqrqrqrqr.", "................", "................",
];
export const DISH_NAME = { ca_loc_nuong_trui: "Cá lóc nướng trui", goi_bong_sung: "Gỏi bông súng", lau_ca_linh_dien_dien: "Lẩu cá linh bông điên điển",
  canh_chua_ca_loc: "Canh chua cá lóc bông điên điển", ca_keo_nuong: "Cá kèo nướng muối ớt", lau_mam: "Lẩu mắm miền Tây" };
export const KIND_NAME = { ca_linh: "cá linh", ca_loc: "cá lóc", bong_dien_dien: "bông điên điển", bong_sung: "bông súng", ca_keo: "cá kèo", keo_neo: "kèo nèo" };

export const icon = (k) => pmap("i:" + k, ICONS[k] || ICONS.ca_linh);
export const dishIcon = (k) => pmap("d:" + k, DISHES[k] || DISHES.goi_bong_sung);
export const portrait = (k) => pmap("p:" + k, PORTRAITS[k]);

// ---------- sky & river scenery ----------
export const SKIES = {
  dawn: [[0, "#2b2a5c"], [0.45, "#c25b7c"], [0.75, "#f59d6b"], [1, "#ffd59a"]],
  day: [[0, "#4aa6e0"], [0.7, "#9ed7f0"], [1, "#e4f6fb"]],
  dusk: [[0, "#1d1740"], [0.4, "#6b2f6e"], [0.7, "#e0614f"], [1, "#ffb35c"]],
  night: [[0, "#070b1f"], [0.6, "#16224a"], [1, "#2b3566"]],
};
export function sky(c, kind, y0 = 0, h = H, t = 0) {
  bands(c, 0, y0, W, h, SKIES[kind], 14);
  if (kind === "night") {
    for (let i = 0; i < 60; i++) {
      const x = (i * 97) % W, y = y0 + ((i * 53) % Math.max(1, h * 0.8));
      if (Math.sin(t * 2 + i) > -0.3) R(c, x, y, 1, 1, i % 7 ? "#c9d4ff" : "#fff6c8");
    }
  }
}
export function sun(c, x, y, r, col = "#fff1b0", glow = "rgba(255,200,120,.25)") {
  for (let k = 3; k >= 1; k--) { c.fillStyle = glow; c.beginPath(); c.arc(x, y, r + k * 6, 0, Math.PI * 2); c.fill(); }
  c.fillStyle = col; c.beginPath(); c.arc(Math.round(x), Math.round(y), r, 0, Math.PI * 2); c.fill();
}
export function cloud(c, x, y, s, col) {
  c.fillStyle = col;
  for (const [dx, dy, r] of [[0, 0, 6], [7, -3, 7], [15, 0, 6], [7, 2, 6]]) { c.beginPath(); c.arc(Math.round(x + dx * s), Math.round(y + dy * s), r * s, 0, Math.PI * 2); c.fill(); }
}
// Riverside silhouette: stilt houses + coconut palms. off = parallax offset.
export function bank(c, baseY, off, col, seed = 1, tall = 1) {
  c.fillStyle = col;
  for (let i = -1; i < 12; i++) {
    const x = Math.round(((i * 61 + seed * 17) % 600) - (off % 600));
    const xx = ((x % 600) + 600) % 600 - 60;
    const kind = (i * 7 + seed) % 3;
    if (kind === 0) { // stilt house
      const w = 26 + (i % 3) * 6, h = 12 * tall;
      c.fillRect(xx, baseY - h - 4, w, h);
      c.beginPath(); c.moveTo(xx - 3, baseY - h - 4); c.lineTo(xx + w / 2, baseY - h - 14 * tall); c.lineTo(xx + w + 3, baseY - h - 4); c.fill();
      for (let p = 2; p < w; p += 6) c.fillRect(xx + p, baseY - 4, 1, 5);
    } else { // palm
      const h = (26 + (i % 4) * 5) * tall;
      for (let k = 0; k < h; k++) c.fillRect(Math.round(xx + Math.sin(k / 9) * 2), baseY - k, 2, 1);
      const tx = xx + Math.sin(h / 9) * 2, ty = baseY - h;
      for (let a = 0; a < 6; a++) {
        const ang = -Math.PI / 2 + (a - 2.5) * 0.55;
        for (let r = 0; r < 12; r++) c.fillRect(Math.round(tx + Math.cos(ang) * r), Math.round(ty + Math.sin(ang) * r + r * r * 0.04), 2, 1);
      }
    }
  }
  c.fillRect(0, baseY, W, 3);
}
// Water surface strip (river seen from the side, above-water part).
export function riverTop(c, y, h, t, cols = ["#5aa7b5", "#3c8696", "#2b6c7d"]) {
  bands(c, 0, y, W, h, [[0, cols[0]], [0.5, cols[1]], [1, cols[2]]], 6);
  c.fillStyle = "rgba(255,255,255,.35)";
  for (let i = 0; i < 40; i++) {
    const x = ((i * 47 + t * (8 + (i % 3) * 4)) % (W + 20)) - 10, yy = y + 2 + ((i * 13) % Math.max(1, h - 3));
    c.fillRect(Math.round(x), Math.round(yy), 3 + (i % 3) * 2, 1);
  }
}
// Mekong ghe: painted eyes on the bow, optional cây bẹo pole with hanging produce, optional rower.
export function ghe(c, x, y, s = 1, o = {}) {
  const L = Math.round(46 * s), Hh = Math.round(7 * s);
  const hull = o.hull || P.wood, dark = o.dark || P.woodD;
  c.fillStyle = dark;
  c.beginPath(); c.moveTo(x - L / 2, y - Hh); c.lineTo(x + L / 2, y - Hh - 2 * s); c.lineTo(x + L / 2 - 6 * s, y); c.lineTo(x - L / 2 + 4 * s, y); c.closePath(); c.fill();
  c.fillStyle = hull; c.fillRect(Math.round(x - L / 2 + 3 * s), Math.round(y - Hh), Math.round(L - 8 * s), Math.round(3 * s));
  R(c, x - L / 2 + 2 * s, y - Hh - 1, L - 6 * s, 1, P.red);
  // the eye
  R(c, x + L / 2 - 9 * s, y - Hh + 1 * s, 4 * s, 3 * s, P.white);
  R(c, x + L / 2 - 7 * s, y - Hh + 1 * s, 2 * s, 2 * s, P.ink);
  R(c, x + L / 2 - 9 * s, y - Hh, 4 * s, 1, P.red);
  if (o.roof) {
    c.fillStyle = o.roof;
    c.beginPath(); c.moveTo(x - 12 * s, y - Hh); c.quadraticCurveTo(x - 3 * s, y - Hh - 12 * s, x + 6 * s, y - Hh); c.fill();
  }
  if (o.beo) { // cây bẹo
    R(c, x - 6 * s, y - Hh - 26 * s, 1, 26 * s, P.woodD);
    const goods = [P.orange, P.yellow, P.leafL, P.pink];
    for (let i = 0; i < 3; i++) R(c, x - 8 * s + i * 2, y - Hh - 24 * s + i * 3 * s, 3 * s, 3 * s, goods[(i + (o.beo | 0)) % 4]);
  }
  if (o.rower) chibiSide(c, x + 2 * s, y - Hh, o.rower, s);
}
// Small side-view person standing on a boat (for wide shots).
export function chibiSide(c, x, y, o = {}, s = 1) {
  const sh = o.shirt || P.suit;
  R(c, x - 2 * s, y - 7 * s, 4 * s, 5 * s, sh);
  R(c, x - 2 * s, y - 2 * s, 1 * s, 2 * s, P.ink); R(c, x + 1 * s, y - 2 * s, 1 * s, 2 * s, P.ink);
  R(c, x - 2 * s, y - 11 * s, 4 * s, 4 * s, P.skin);
  if (o.hat) { c.fillStyle = P.straw; c.beginPath(); c.moveTo(x - 5 * s, y - 10 * s); c.lineTo(x, y - 15 * s); c.lineTo(x + 5 * s, y - 10 * s); c.fill(); }
  else R(c, x - 2 * s, y - 12 * s, 4 * s, 2 * s, o.hair || P.hair);
  if (o.pole) R(c, x + 2 * s, y - 14 * s, 1, 16 * s, P.woodD);
}

// Lục bình (water hyacinth) mat floating at y, roots hanging down.
export function hyacinth(c, x, y, w, t, seed = 0) {
  for (let i = 0; i < w; i += 3) {
    const sway = Math.round(Math.sin(t * 1.5 + i * 0.4 + seed) * 1.5);
    const len = 6 + ((i * 7 + seed) % 9);
    c.fillStyle = "rgba(60,40,30,.55)";
    for (let k = 0; k < len; k++) c.fillRect(x + i + Math.round(Math.sin(k / 3 + t + i) * sway * 0.5), y + 2 + k, 1, 1);
  }
  for (let i = 0; i < w; i += 4) {
    R(c, x + i, y - 2, 4, 3, i % 8 ? P.leaf : P.leafL);
    R(c, x + i + 1, y - 3, 2, 1, P.leafL);
    if ((i + seed) % 12 === 0) { R(c, x + i + 1, y - 6, 2, 3, "#b48ad8"); R(c, x + i + 1, y - 7, 1, 1, "#e2c9ff"); }
  }
}

// ---------- underwater ----------
export const WATER = [[0, "#3fb6c4"], [0.18, "#1f8aa0"], [0.45, "#155f80"], [0.75, "#0e3c5e"], [1, "#081f38"]];
export function godRays(c, camX, top, height, t, alpha = 0.07) {
  c.save();
  c.globalCompositeOperation = "lighter";
  for (let i = 0; i < 7; i++) {
    const bx = ((i * 83 - camX * 0.3) % (W + 120) + W + 120) % (W + 120) - 60 + Math.sin(t * 0.4 + i) * 10;
    const w = 14 + (i % 3) * 10;
    const g = c.createLinearGradient(0, top, 0, top + height);
    g.addColorStop(0, `rgba(200,245,255,${alpha * (1 + (i % 2))})`); g.addColorStop(1, "rgba(200,245,255,0)");
    c.fillStyle = g;
    c.beginPath(); c.moveTo(bx, top); c.lineTo(bx + w, top); c.lineTo(bx + w + 70, top + height); c.lineTo(bx + 40, top + height); c.fill();
  }
  c.restore();
}
export function kelp(c, x, baseY, h, t, col = P.leafD, colL = P.leaf) {
  for (let k = 0; k < h; k++) {
    const sw = Math.round(Math.sin(t * 1.3 + k * 0.18 + x) * (k / h) * 5);
    R(c, x + sw, baseY - k, 2, 1, k % 6 < 3 ? col : colL);
    if (k % 7 === 3) R(c, x + sw + (k % 14 < 7 ? 2 : -2), baseY - k, 2, 1, colL);
  }
}
export function rock(c, x, y, w, h, col = "#2a3b4a", colL = "#3e5466") {
  c.fillStyle = col; c.beginPath(); c.ellipse(x, y, w, h, 0, Math.PI, 0); c.fill();
  c.fillStyle = colL; c.fillRect(Math.round(x - w * 0.5), Math.round(y - h * 0.8), Math.round(w * 0.6), 1);
}

// ---------- characters ----------
// Út Sen swimming, side view. (x,y)=center, facing ±1, phase in seconds, speed 0..1.
export function diver(c, x, y, facing, phase, speed = 1, o = {}) {
  c.save();
  c.translate(Math.round(x), Math.round(y));
  if (facing < 0) c.scale(-1, 1);
  if (o.tilt) c.rotate(o.tilt * facing);
  const kick = Math.sin(phase * (6 + speed * 8));
  // ponytail streaming behind
  for (let i = 0; i < 6; i++) R(c, 3 - i, -4 + Math.round(Math.sin(phase * 8 - i * 0.7) * (i / 3)), 1, 1, P.hair);
  R(c, 2, -4, 1, 1, P.orange);
  // legs + fins
  const legs = [[kick * 2, P.suit], [-kick * 2, P.suitD]];
  for (const [dy, col] of legs) {
    R(c, -12, -1 + Math.round(dy * 0.5), 6, 2, col);
    R(c, -16, -1 + Math.round(dy), 4, 2, P.skin);
    R(c, -20, -2 + Math.round(dy * 1.4), 4, 3, P.orange);
    R(c, -21, -1 + Math.round(dy * 1.6), 1, 2, P.orangeD);
  }
  // torso
  R(c, -7, -3, 11, 5, P.suit); R(c, -7, -3, 11, 1, P.suitL); R(c, -7, 1, 11, 1, P.suitD);
  R(c, -2, -3, 1, 5, P.orange);
  // arms: reaching forward, stroke when moving
  const arm = Math.round(Math.sin(phase * (4 + speed * 6)) * 2 * speed);
  if (o.grab) { R(c, 3, -2, 9, 2, P.skin); R(c, 11, -3, 2, 4, P.skin); }
  else { R(c, 3, -2 + arm, 6, 1, P.skin); R(c, 3, 1 - arm, 5, 1, P.skinD); }
  // head
  R(c, 4, -5, 6, 6, P.skin); R(c, 3, -6, 6, 3, P.hair); R(c, 3, -3, 2, 3, P.hair);
  R(c, 6, -4, 4, 3, P.mask); R(c, 7, -3, 3, 1, P.lens);
  R(c, 5, -1, 1, 1, "#f07a7a");
  c.restore();
}
// Ca linh: school of small silver fish. Ca loc: one long dark snakehead.
export function fish(c, kind, x, y, facing, t, scale = 1) {
  c.save(); c.translate(Math.round(x), Math.round(y)); if (facing < 0) c.scale(-1, 1);
  if (kind === "ca_loc") {
    const w = Math.round(Math.sin(t * 7) * 1.5);
    c.scale(scale, scale);
    R(c, -11, -2, 18, 4, P.loc); R(c, -11, -3, 16, 1, P.locD); R(c, -9, 2, 14, 1, P.locL);
    for (let i = -8; i < 4; i += 4) R(c, i, -2, 2, 3, P.locD);
    R(c, 7, -2, 4, 4, P.loc); R(c, 9, -1, 1, 1, P.yellow); R(c, 10, 1, 1, 1, P.locD);
    R(c, -15, -3 + w, 4, 2, P.locD); R(c, -15, 1 + w, 4, 2, P.locD);
    R(c, -6, -4, 10, 1, P.locD);
  } else if (kind === "ca_keo") {
    // cá kèo: 3 slim brown-grey mudskipper-like gobies, eyes bulging on top of the head
    const pts = [[0, 0], [-8, 4], [5, 5]];
    pts.forEach(([dx, dy], i) => {
      const yy = dy + Math.round(Math.sin(t * 2.5 + i * 2) * 1), xx = dx + Math.round(Math.cos(t * 1.7 + i));
      const wig = Math.round(Math.sin(t * 10 + i) * 0.8);
      R(c, xx - 4, yy - 1, 9, 2, P.keo); R(c, xx - 4, yy + 1, 8, 1, P.keoL); R(c, xx - 3, yy - 2, 6, 1, P.keoD);
      for (let k = -3; k < 4; k += 2) R(c, xx + k, yy - 1, 1, 1, P.keoD);
      R(c, xx + 3, yy - 3, 1, 1, P.ink); R(c, xx + 5, yy, 1, 1, P.keoD);
      R(c, xx - 6, yy - 1 + wig, 2, 3, P.keoD);
    });
  } else {
    const pts = [[0, 0], [-7, -4], [-6, 4], [6, -5], [5, 5], [-13, 1], [11, 0]];
    pts.forEach(([dx, dy], i) => {
      const yy = dy + Math.round(Math.sin(t * 3 + i) * 1.2), xx = dx + Math.round(Math.cos(t * 2 + i * 2));
      const wig = Math.round(Math.sin(t * 12 + i) * 0.7);
      R(c, xx - 2, yy - 1, 5, 2, P.silver); R(c, xx - 2, yy, 5, 1, P.silverD);
      R(c, xx + 2, yy - 1, 1, 1, P.ink);
      R(c, xx - 4, yy - 1 + wig, 2, 2, P.silverD);
    });
  }
  c.restore();
}
// Harvest nodes at the surface. y = surface line in screen px.
export function nodeArt(c, kind, x, y, t, ready) {
  c.save(); if (!ready) c.globalAlpha = 0.45;
  if (kind === "bong_sung") {
    for (let k = 0; k < 40; k++) R(c, x + Math.round(Math.sin(t + k * 0.15) * 2), y + k, 1, 1, k % 4 ? "#3d7a3a" : "#5a9a4a");
    R(c, x - 9, y - 1, 8, 2, P.leafD); R(c, x + 3, y - 1, 8, 2, P.leaf); R(c, x - 8, y - 2, 6, 1, P.leafL);
    if (ready) {
      const b = Math.round(Math.sin(t * 2) * 1);
      R(c, x - 3, y - 6 + b, 6, 4, P.pink); R(c, x - 2, y - 8 + b, 4, 3, P.pinkL); R(c, x - 4, y - 4 + b, 2, 2, P.pinkD); R(c, x + 2, y - 4 + b, 2, 2, P.pinkD);
      R(c, x - 1, y - 5 + b, 2, 1, P.yellow);
    } else R(c, x - 1, y - 4, 2, 3, P.leafL);
  } else if (kind === "keo_neo") {
    // kèo nèo: a bunch of broad green leaves on stalks standing out of the water, small yellow flowers on top
    for (let k = 0; k < 14; k++) R(c, x + Math.round(Math.sin(t + k * 0.3) * 1), y + k, 1, 1, "#3d6a3a");
    for (const [dx, h] of [[-5, 12], [-2, 16], [1, 18], [4, 14], [7, 10]]) {
      const sw = Math.round(Math.sin(t * 1.5 + dx) * 1);
      for (let k = 0; k < h; k++) R(c, x + dx + (k > h - 4 ? sw : 0), y - k, 1, 1, P.leafD);
      R(c, x + dx - 2 + sw, y - h - 1, 5, 3, P.leaf); R(c, x + dx - 1 + sw, y - h - 2, 3, 1, P.leafL); R(c, x + dx + sw, y - h, 1, 2, P.leafD);
    }
    if (ready) for (let i = 0; i < 5; i++) { const sw = Math.round(Math.sin(t * 2 + i) * 1); R(c, x - 5 + i * 3 + sw, y - 20 - (i % 2) * 2, 2, 2, i % 2 ? P.yellow : P.yellowD); }
    else R(c, x - 1, y - 8, 2, 3, P.leafL);
  } else {
    for (let k = 0; k < 20; k++) R(c, x + Math.round(Math.sin(k / 5) * 1), y - k, 1, 1, P.leafD);
    for (let k = 0; k < 14; k++) R(c, x - 6 + k, y - 14 - Math.round(Math.sin(k / 3) * 3), 1, 1, P.leaf);
    for (let i = 0; i < 9; i++) R(c, x - 7 + (i * 5) % 14, y - 20 + ((i * 3) % 7), 2, 1, P.leafL);
    if (ready) for (let i = 0; i < 7; i++) {
      const sw = Math.round(Math.sin(t * 2 + i) * 1);
      R(c, x - 6 + (i * 7) % 13 + sw, y - 12 + ((i * 5) % 6), 2, 3, i % 2 ? P.yellow : P.yellowD);
    }
    for (let k = 0; k < 10; k++) R(c, x + Math.round(Math.sin(t + k) * 1), y + k, 1, 1, "#3d6a3a");
  }
  c.restore();
}
// Wooden pier at the dock.
export function dock(c, x, y, t) {
  R(c, x - 26, y - 6, 34, 3, P.woodL); R(c, x - 26, y - 3, 34, 2, P.woodD);
  for (let i = -24; i < 8; i += 7) R(c, x + i, y - 3, 2, 14, P.woodD);
  ghe(c, x + 14, y + 1 + Math.round(Math.sin(t * 2)), 0.6, { roof: "#7a4a2a" });
  R(c, x - 20, y - 18, 1, 12, P.woodD);
  R(c, x - 23, y - 22, 7, 5, P.red); R(c, x - 22, y - 21, 5, 3, P.gold);
}

// ---------- restaurant (top-down) ----------
export function planks(c, x, y, w, h) {
  for (let r = 0; r < h; r += 6) {
    R(c, x, y + r, w, 6, (r / 6) % 2 ? "#b98a55" : "#c69660");
    R(c, x, y + r + 5, w, 1, "#8a6038");
    for (let k = ((r / 6) % 3) * 13; k < w; k += 40) R(c, x + k, y + r, 1, 5, "#8a6038");
  }
}
export function lantern(c, x, y, t, col = P.red) {
  const sw = Math.round(Math.sin(t * 2 + x) * 1);
  R(c, x + sw, y, 1, 3, P.ink);
  c.fillStyle = "rgba(255,180,80,.18)"; c.beginPath(); c.arc(x + sw, y + 7, 9, 0, Math.PI * 2); c.fill();
  R(c, x - 3 + sw, y + 3, 7, 8, col); R(c, x - 2 + sw, y + 4, 5, 6, P.orange); R(c, x - 3 + sw, y + 3, 7, 1, P.gold); R(c, x - 3 + sw, y + 10, 7, 1, P.gold);
  R(c, x + sw, y + 11, 1, 2, P.gold);
}
export function stove(c, x, y, state, t, p = 0) {
  R(c, x - 11, y - 8, 22, 18, "#7a3b28"); R(c, x - 11, y - 8, 22, 2, "#a5553a"); R(c, x - 10, y + 8, 20, 2, "#4a2216");
  R(c, x - 7, y - 4, 14, 10, P.ink);
  if (state !== "idle") {
    const f = Math.round(Math.sin(t * 20) * 1);
    R(c, x - 5, y + 1 + f, 10, 4, P.orange); R(c, x - 3, y - 1 - f, 6, 3, P.yellow);
    c.fillStyle = "rgba(255,140,60,.2)"; c.beginPath(); c.arc(x, y, 18, 0, Math.PI * 2); c.fill();
  }
  R(c, x - 9, y - 11, 18, 5, "#3a3a44"); R(c, x - 9, y - 11, 18, 1, "#6a6a78");
  if (state === "ready") R(c, x - 7, y - 12, 14, 2, P.gold);
  if (state === "cooking" || state === "ready") {
    for (let i = 0; i < 3; i++) {
      const k = ((t * 0.8 + i / 3) % 1);
      c.globalAlpha = 1 - k; R(c, x - 5 + i * 5 + Math.round(Math.sin(k * 9 + i) * 2), y - 14 - k * 16, 2, 2, "#fff"); c.globalAlpha = 1;
    }
  }
}
export function table(c, x, y) {
  c.fillStyle = "rgba(0,0,0,.18)"; c.beginPath(); c.ellipse(x + 2, y + 3, 16, 9, 0, 0, Math.PI * 2); c.fill();
  c.fillStyle = P.woodD; c.beginPath(); c.ellipse(x, y + 1, 15, 8, 0, 0, Math.PI * 2); c.fill();
  c.fillStyle = P.woodL; c.beginPath(); c.ellipse(x, y, 15, 8, 0, 0, Math.PI * 2); c.fill();
  c.fillStyle = "#d9b07a"; c.beginPath(); c.ellipse(x, y - 1, 11, 5, 0, 0, Math.PI * 2); c.fill();
  for (const [dx, dy] of [[-20, 0], [20, 0], [0, 12]]) { R(c, x + dx - 3, y + dy - 2, 6, 4, P.woodD); R(c, x + dx - 3, y + dy - 2, 6, 1, P.woodL); }
}
// Top-down-ish chibi (front view). walk = phase; carry = dish id.
export function chibi(c, x, y, o = {}) {
  const bob = o.walk ? Math.round(Math.abs(Math.sin(o.walk * 10))) : 0;
  c.fillStyle = "rgba(0,0,0,.22)"; c.beginPath(); c.ellipse(x, y + 1, 5, 2, 0, 0, Math.PI * 2); c.fill();
  const yy = y - bob;
  const step = o.walk ? Math.round(Math.sin(o.walk * 10)) : 0;
  R(c, x - 3, yy - 2 + step, 2, 3, P.ink); R(c, x + 1, yy - 2 - step, 2, 3, P.ink);
  R(c, x - 4, yy - 9, 8, 7, o.shirt || P.suit);
  if (o.apron) { R(c, x - 3, yy - 7, 6, 5, P.white); R(c, x - 3, yy - 7, 6, 1, P.orange); }
  R(c, x - 5, yy - 8, 1, 4, P.skin); R(c, x + 4, yy - 8, 1, 4, P.skin);
  R(c, x - 4, yy - 16, 8, 7, P.skin);
  R(c, x - 2, yy - 13, 1, 1, P.ink); R(c, x + 1, yy - 13, 1, 1, P.ink);
  if (o.hat) {
    c.fillStyle = P.straw; c.beginPath(); c.moveTo(x - 9, yy - 14); c.lineTo(x, yy - 23); c.lineTo(x + 9, yy - 14); c.fill();
    R(c, x - 9, yy - 14, 18, 1, P.strawD);
  } else {
    R(c, x - 5, yy - 18, 10, 4, o.hair || P.hair); R(c, x - 5, yy - 15, 2, 4, o.hair || P.hair); R(c, x + 3, yy - 15, 2, 4, o.hair || P.hair);
    if (o.bun) { R(c, x - 2, yy - 21, 4, 3, o.hair || P.hair); R(c, x - 1, yy - 19, 2, 1, P.orange); }
  }
  if (o.carry) c.drawImage(dishIcon(o.carry), x - 8, yy - 33);
}
export function ripple(c, x, y, t, seed) {
  const k = (t * 0.5 + seed) % 1;
  c.strokeStyle = `rgba(255,255,255,${0.35 * (1 - k)})`; c.lineWidth = 1;
  c.beginPath(); c.ellipse(Math.round(x), Math.round(y), 3 + k * 10, 1 + k * 4, 0, 0, Math.PI * 2); c.stroke();
}
