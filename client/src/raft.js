// Side-view drawing helpers for the night floating restaurant (nhà bè) in scene_quan.js.
// Everything draws on the low-res `px` canvas with integer rects so it reads as pixel art.
import { W } from "./engine.js";
import { P, R, ghe, lantern, dishIcon, ripple } from "./art.js";

const TAU = Math.PI * 2;

// ---------- depth scaling: draw into a scratch canvas, blit back nearest-neighbour ----------
let scratch = null;
const SW = 128, SH = 112, AX = 64, AY = 100; // anchor (feet) inside the scratch canvas
export function scaled(c, s, ax, ay, fn) {
  if (s >= 0.999) return fn(c, ax, ay);
  if (!scratch) { scratch = document.createElement("canvas"); scratch.width = SW; scratch.height = SH; }
  const sc = scratch.getContext("2d");
  sc.clearRect(0, 0, SW, SH); sc.imageSmoothingEnabled = false;
  fn(sc, AX, AY);
  c.imageSmoothingEnabled = false;
  c.drawImage(scratch, 0, 0, SW, SH, Math.round(ax - AX * s), Math.round(ay - AY * s), Math.round(SW * s), Math.round(SH * s));
}

// ---------- side-view chibi (faces right when face = 1) ----------
// o: { face, shirt, pants, hair, skin, hat, bun, apron, walk, sit, carry, arm: "stir"|"eat"|"wave", t, angry }
export function personSide(c, x, y, o = {}) {
  const f = o.face < 0 ? -1 : 1;
  const walk = o.walk || 0, moving = walk > 0 && !o.sit;
  const bob = moving ? (Math.abs(Math.sin(walk * 10)) > 0.6 ? 1 : 0) : 0;
  const Y = y - bob;
  const r = (dx, dy, w, h, col) => R(c, f === 1 ? x + dx : x - dx - w + 1, Y + dy, w, h, col);
  const skin = o.skin || P.skin, shirt = o.shirt || P.suit, pants = o.pants || "#2a2238", hair = o.hair || P.hair;
  c.fillStyle = "rgba(0,0,0,.28)"; c.beginPath(); c.ellipse(x, y, 6, 1.5, 0, 0, TAU); c.fill();
  if (o.sit) {
    r(-1, -6, 5, 2, pants); r(3, -4, 2, 3, pants); r(3, -1, 3, 1, P.ink);
  } else {
    const sw = moving ? Math.round(Math.sin(walk * 10) * 2) : 0;
    r(-2 - sw, -5, 2, 4, pants); r(-2 - sw, -1, 3, 1, P.ink);
    r(0 + sw, -5, 2, 4, pants); r(0 + sw, -1, 3, 1, P.ink);
  }
  // torso
  r(-3, -12, 7, 7, shirt); r(-3, -12, 1, 7, "rgba(0,0,0,.18)");
  if (o.apron) { r(0, -11, 4, 6, P.white); r(-3, -10, 7, 1, P.orange); }
  // arm
  const t = o.t || 0;
  if (o.carry) { r(1, -12, 3, 2, shirt); r(2, -19, 2, 7, skin); r(-3, -21, 9, 1, P.woodD); }
  else if (o.arm === "stir") { const k = Math.round(Math.sin(t * 6) * 1.5); r(1, -11, 3, 2, shirt); r(3, -10, 4, 2, skin); r(6 + k, -15, 1, 7, P.woodD); r(5 + k, -9, 3, 1, P.woodL); }
  else if (o.arm === "eat") { const k = Math.sin(t * 5) > 0 ? 1 : 0; r(1, -11, 3, 2, shirt); r(3, -10 - k, 4, 2, skin); r(6, -13 - k, 1, 4, P.straw); r(7, -13 - k, 1, 4, P.straw); }
  else if (o.arm === "wave") { const k = Math.sin(t * 8) > 0 ? 1 : 0; r(1, -12, 3, 2, shirt); r(3 + k, -18, 2, 6, skin); }
  else { const as = moving ? Math.round(Math.sin(walk * 10 + Math.PI)) : 0; r(-1 + as, -11, 2, 5, shirt); r(-1 + as, -6, 2, 1, skin); }
  // head
  r(-4, -21, 9, 9, skin); r(-4, -13, 9, 1, "rgba(0,0,0,.12)");
  if (o.hat) {
    c.fillStyle = P.straw; c.beginPath(); c.moveTo(x - 9, Y - 19); c.lineTo(x, Y - 29); c.lineTo(x + 10, Y - 19); c.closePath(); c.fill();
    R(c, x - 9, Y - 19, 20, 1, P.strawD); r(-5, -19, 3, 4, hair);
  } else {
    r(-5, -23, 10, 3, hair); r(-5, -21, 3, 6, hair); r(3, -21, 2, 2, hair);
    if (o.bun) { r(-8, -24, 4, 4, hair); r(-5, -22, 1, 1, o.bunTie || P.orange); }
  }
  if (o.angry) { r(1, -19, 3, 1, P.ink); r(2, -17, 1, 1, P.ink); r(3, -14, 2, 1, P.redD); }
  else { r(2, -18, 1, 2, P.ink); r(3, -15, 1, 1, "#f07a7a"); }
  if (o.carry) c.drawImage(dishIcon(o.carry), x - 8 + f, Y - 37);
}

// ---------- furniture ----------
export function stool(c, x, y) {
  R(c, x - 4, y - 5, 8, 2, P.woodL); R(c, x - 4, y - 4, 8, 1, P.woodD);
  R(c, x - 3, y - 3, 1, 3, P.woodD); R(c, x + 2, y - 3, 1, 3, P.woodD);
}
export function sideTable(c, x, y) {
  c.fillStyle = "rgba(0,0,0,.25)"; c.beginPath(); c.ellipse(x, y, 16, 2, 0, 0, TAU); c.fill();
  R(c, x - 12, y - 11, 2, 11, P.woodD); R(c, x + 10, y - 11, 2, 11, P.woodD);
  R(c, x - 11, y - 5, 22, 1, P.woodD);
  R(c, x - 15, y - 14, 30, 2, P.woodL); R(c, x - 15, y - 12, 30, 2, P.woodD);
  R(c, x - 13, y - 14, 6, 1, "#d9a86a");
  // chopstick cup + chili jar
  R(c, x - 10, y - 18, 3, 4, "#c9c2d4"); R(c, x - 10, y - 21, 1, 3, P.straw); R(c, x - 8, y - 20, 1, 2, P.straw);
  R(c, x - 5, y - 17, 3, 3, P.red); R(c, x - 5, y - 18, 3, 1, "#f2efe6");
}
// clay stove (lò đất) with a wok, side view
export function clayStove(c, x, y, state, t) {
  c.fillStyle = "rgba(0,0,0,.3)"; c.beginPath(); c.ellipse(x, y, 16, 2.5, 0, 0, TAU); c.fill();
  R(c, x - 13, y - 18, 26, 18, "#9a4a30"); R(c, x - 14, y - 19, 28, 2, "#c06a45");
  R(c, x - 13, y - 3, 26, 3, "#6a2e1c"); R(c, x + 10, y - 17, 3, 14, "#7e3a25");
  R(c, x - 6, y - 12, 12, 9, P.ink); R(c, x - 4, y - 13, 8, 1, P.ink);
  const lit = state !== "idle";
  if (lit) {
    const fl = Math.round(Math.sin(t * 22) * 1);
    R(c, x - 5, y - 8 + fl, 10, 5, P.orange); R(c, x - 3, y - 11 - fl, 6, 4, P.yellow); R(c, x - 1, y - 12 + fl, 2, 2, "#fff6c8");
  } else { R(c, x - 5, y - 5, 10, 2, "#5a2018"); R(c, x - 3, y - 6, 2, 1, "#d9582a"); }
  R(c, x - 10, y - 5, 7, 2, P.woodD); R(c, x + 4, y - 4, 7, 2, P.wood);
  // wok
  R(c, x - 11, y - 22, 22, 3, "#3a3a44"); R(c, x - 12, y - 23, 24, 1, "#6a6a78"); R(c, x + 12, y - 23, 5, 1, P.woodD);
  if (state === "cooking") R(c, x - 7, y - 24 + (Math.sin(t * 9) > 0 ? 0 : 1), 14, 1, "#c97a52");
  if (state === "ready") R(c, x - 9, y - 24, 18, 1, P.gold);
}
// the pass: a small counter where finished dishes wait
export function passCounter(c, x, y) {
  c.fillStyle = "rgba(0,0,0,.25)"; c.beginPath(); c.ellipse(x, y, 14, 2, 0, 0, TAU); c.fill();
  R(c, x - 12, y - 15, 24, 15, P.wood); R(c, x - 13, y - 17, 26, 2, P.woodL);
  for (let i = -9; i < 12; i += 6) R(c, x + i, y - 14, 1, 13, P.woodD);
  R(c, x - 12, y - 1, 24, 1, P.woodD);
  R(c, x + 6, y - 20, 4, 3, P.gold); R(c, x + 7, y - 21, 2, 1, P.yellowD); // service bell
}
// back shelf + hanging pots behind the kitchen (x0..x1, standing on the back edge yb)
export function kitchenBack(c, x0, x1, yb, t) {
  const top = yb - 30;
  R(c, x0, top, x1 - x0, 30, "#4a2c18"); R(c, x0, top, x1 - x0, 2, P.woodL);
  R(c, x0, top + 14, x1 - x0, 2, P.woodL);
  const jar = ["#c97a52", "#e9cf8a", "#7a4fa0", "#3f9a4a", "#d94a3d", "#d4e8f2"];
  for (let i = 0, x = x0 + 4; x < x1 - 6; i++, x += 9) {
    const col = jar[i % jar.length];
    R(c, x, top + 7, 5, 7, col); R(c, x + 1, top + 5, 3, 2, col); R(c, x + 1, top + 4, 3, 1, P.woodD);
    if (i % 2) { R(c, x - 1, top + 22, 7, 6, "#8a6a3a"); R(c, x, top + 20, 2, 2, P.leafL); R(c, x + 3, top + 19, 2, 3, P.leaf); }
    else { R(c, x, top + 23, 5, 5, "#e8e2d0"); R(c, x, top + 23, 5, 1, "#a09a88"); }
  }
  // frame with hanging pots
  R(c, x0 + 2, top - 26, 2, 26, P.woodD); R(c, x1 - 4, top - 26, 2, 26, P.woodD);
  R(c, x0 + 2, top - 26, x1 - x0 - 4, 2, P.woodD);
  for (let i = 0, x = x0 + 12; x < x1 - 10; i++, x += 18) {
    const sw = Math.round(Math.sin(t * 1.5 + i) * 1);
    R(c, x, top - 24, 1, 4, "#2a2230");
    if (i % 3 === 0) { R(c, x - 5 + sw, top - 20, 11, 6, "#5a5a66"); R(c, x - 6 + sw, top - 20, 13, 1, "#8a8a96"); R(c, x + 6 + sw, top - 19, 3, 1, P.woodD); }
    else if (i % 3 === 1) { R(c, x + sw, top - 20, 1, 9, P.woodD); R(c, x - 2 + sw, top - 11, 5, 3, "#8a8a96"); }
    else { R(c, x - 4 + sw, top - 20, 9, 8, "#c97a52"); R(c, x - 4 + sw, top - 20, 9, 1, "#e8a070"); }
  }
}

// ---------- roof, posts, lantern strings ----------
export function roofAndPosts(c, xl, xr, yFront, t) {
  // side posts (behind everything on the deck)
  R(c, xl, 16, 5, yFront - 16, P.woodD); R(c, xl + 1, 16, 1, yFront - 16, P.wood);
  R(c, xr - 5, 16, 5, yFront - 16, P.woodD); R(c, xr - 4, 16, 1, yFront - 16, P.wood);
  // thatch
  R(c, 0, 0, W, 13, "#5a3a1c");
  for (let x = 0; x < W; x += 3) { const h = 3 + ((x * 7) % 5); R(c, x, 11, 2, h, x % 2 ? P.strawD : "#a8834a"); R(c, x, 2 + (x * 5) % 8, 1, 3, "#7a5426"); }
  R(c, 0, 16, W, 3, "#3a2212"); R(c, 0, 16, W, 1, P.woodL);
}
// sagging string of lanterns from (x0,y0) to (x1,y0); returns lantern positions (for glows/reflections)
export function lanternString(c, x0, x1, y0, sag, n, t, out) {
  for (let x = x0; x <= x1; x++) { const u = (x - x0) / (x1 - x0); R(c, x, y0 + Math.round(sag * 4 * u * (1 - u)), 1, 1, "#2a1a12"); }
  const cols = [P.red, P.orange, "#f3c454", P.red];
  for (let i = 0; i < n; i++) {
    const u = (i + 0.5) / n, x = Math.round(x0 + (x1 - x0) * u), y = y0 + Math.round(sag * 4 * u * (1 - u));
    lantern(c, x, y, t, cols[i % cols.length]);
    if (out) out.push([x, y + 7]);
  }
}
// additive warm glow
export function glow(c, x, y, r, a = 0.12, col = "255,170,80") {
  c.save(); c.globalCompositeOperation = "lighter";
  for (let k = 3; k >= 1; k--) { c.fillStyle = `rgba(${col},${a / k})`; c.beginPath(); c.arc(Math.round(x), Math.round(y), r * k / 3, 0, TAU); c.fill(); }
  c.restore();
}

// ---------- water ----------
export function nightWater(c, y0, y1, t, lights = [], moonX = null) {
  const h = y1 - y0;
  const cols = ["#1a2650", "#121c40", "#0b1330", "#070c22"];
  for (let i = 0; i < 4; i++) R(c, 0, y0 + Math.round(h * i / 4), W, Math.ceil(h / 4) + 1, cols[i]);
  c.fillStyle = "rgba(160,190,255,.18)";
  for (let i = 0; i < 46; i++) {
    const x = ((i * 59 + t * (5 + (i % 4) * 3)) % (W + 30)) - 15, y = y0 + 2 + ((i * 17) % Math.max(1, h - 3));
    c.fillRect(Math.round(x), Math.round(y), 2 + (i % 4), 1);
  }
  if (moonX != null) for (let y = y0 + 2, k = 0; y < y1; y += 3, k++) {
    const w = 3 + ((k * 7 + Math.floor(t * 3)) % 5); R(c, moonX - w / 2 + Math.round(Math.sin(t * 2 + k) * 2), y, w, 1, "rgba(246,241,214,.35)");
  }
  for (const [lx, top, len] of lights) for (let y = Math.max(y0, top) + 1, k = 0; y < Math.min(y1, top + len); y += 2, k++) {
    const w = 2 + ((k * 3 + Math.floor(t * 4 + lx)) % 4); R(c, lx - w / 2 + Math.round(Math.sin(t * 3 + k + lx) * 1.5), y, w, 1, `rgba(255,170,80,${0.45 - k * 0.03})`);
  }
}

// ---------- deck ----------
export function deck(c, xl, xr, yBack, yFront, t) {
  let y = yBack, row = 0;
  while (y < yFront) {
    const h = Math.min(6, 3 + Math.floor((y - yBack) / 18));
    R(c, xl, y, xr - xl, h, row % 2 ? "#a87a48" : "#b8874f");
    R(c, xl, y + h - 1, xr - xl, 1, "#7a5230");
    for (let k = xl + ((row * 23) % 41); k < xr; k += 41) R(c, k, y, 1, h - 1, "#7a5230");
    y += h; row++;
  }
  // warm wash
  c.fillStyle = "rgba(255,170,90,.06)"; c.fillRect(xl, yBack, xr - xl, yFront - yBack);
  // front beam + floats
  R(c, xl - 2, yFront, xr - xl + 4, 6, "#5e3a20"); R(c, xl - 2, yFront, xr - xl + 4, 1, P.woodL);
  for (let x = xl + 6; x < xr - 4; x += 30) R(c, x, yFront + 2, 2, 2, "#2a1a12");
  for (let x = xl + 2; x < xr - 10; x += 26) {
    R(c, x, yFront + 6, 22, 6, "#4a5a3a"); R(c, x, yFront + 6, 22, 1, "#6a7a4a"); R(c, x + 7, yFront + 6, 1, 6, "#2f3826"); R(c, x + 15, yFront + 6, 1, 6, "#2f3826");
  }
}
export function backRail(c, x0, x1, y) {
  R(c, x0, y - 12, x1 - x0, 2, P.woodD); R(c, x0, y - 12, x1 - x0, 1, P.wood);
  for (let x = x0 + 2; x < x1; x += 10) R(c, x, y - 10, 2, 10, P.woodD);
}
// gangway + mooring post at the right edge
export function landing(c, x, y, t) {
  R(c, x, y - 2, 16, 3, P.woodL); R(c, x, y + 1, 16, 1, P.woodD);
  R(c, x + 12, y - 22, 3, 26, P.woodD); R(c, x + 12, y - 22, 3, 1, P.woodL);
  R(c, x + 10, y - 10, 7, 1, P.straw);
  lantern(c, x + 13, y - 34, t, P.orange);
}
// small sampan; face -1 = bow pointing left
export function sampan(c, x, y, face, t, s = 0.7, o = {}) {
  c.save(); c.translate(Math.round(x), 0); if (face < 0) c.scale(-1, 1);
  ghe(c, 0, y, s, { roof: o.roof || null, hull: o.hull, beo: o.beo });
  c.restore();
  ripple(c, x - 14, y + 2, t, 0.3); ripple(c, x + 12, y + 2, t, 0.7);
}

// ---------- tiny bits ----------
export function steam(c, x, y, t, n = 3, h = 12) {
  for (let i = 0; i < n; i++) {
    const k = (t * 0.7 + i / n) % 1;
    c.globalAlpha = 0.55 * (1 - k);
    R(c, x - n + i * 2 + Math.round(Math.sin(k * 8 + i * 2) * 1.5), y - k * h, 1, 2, "#f4f0ff");
  }
  c.globalAlpha = 1;
}
export function smoke(c, x, y, t, n = 4) {
  for (let i = 0; i < n; i++) {
    const k = (t * 0.35 + i / n) % 1, r = 2 + k * 5;
    c.fillStyle = `rgba(150,140,160,${0.35 * (1 - k)})`;
    c.beginPath(); c.arc(Math.round(x + Math.sin(k * 5 + i) * 4 + k * 6), Math.round(y - k * 42), r, 0, TAU); c.fill();
  }
}
export function coin(c, x, y, spin) {
  const w = Math.max(1, Math.round(5 * Math.abs(Math.cos(spin))));
  R(c, x - w / 2, y - 2, w, 5, P.yellow); R(c, x - w / 2, y + 2, w, 1, P.yellowD);
  if (w > 2) R(c, x - 0.5, y - 1, 1, 3, P.yellowD);
}
export function moon(c, x, y) {
  c.fillStyle = "rgba(246,241,214,.08)"; c.beginPath(); c.arc(x, y, 16, 0, TAU); c.fill();
  c.fillStyle = "rgba(246,241,214,.12)"; c.beginPath(); c.arc(x, y, 11, 0, TAU); c.fill();
  c.fillStyle = "#f6f1d6"; c.beginPath(); c.arc(x, y, 7, 0, TAU); c.fill();
  R(c, x - 3, y - 2, 2, 2, "#ddd6b4"); R(c, x + 2, y + 2, 2, 1, "#ddd6b4");
}
