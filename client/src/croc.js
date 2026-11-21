// Cá Sấu Năm Chèo (Test Contract v1.1 §1.2) — client mirror of the monster rules, every number from
// tuning.gather.monsters. States: patrol (waypoint ↔ waypoint at patrol_speed) → chase (diver at d ≥ 10 within
// detect_radius, chase_speed) → patrol again (beyond exit_radius or diver d < 10); recoil after a hit
// (recoil_ticks steps of recoil_dist/60 m away from the diver). Clamped to the map and its depth band.
import { R } from "./art.js";

const CORE_D = 10; // the monster only detects / hits the diver at d ≥ 10

// spawns active for this day: from_day ≤ day (standalone gather = day 1)
export function makeCrocs(mon, day = 1) {
  if (!mon) return [];
  return (mon.spawns || []).filter((s) => (s.from_day || 1) <= day && mon.species?.[s.kind]).map((s) => ({
    id: s.id, kind: s.kind, sp: mon.species[s.kind], x: s.pos[0], d: s.pos[1],
    wps: s.waypoints.map((w) => [...w]), wi: 1 % s.waypoints.length, state: "patrol", recoil: 0, rdx: 1, rdd: 0, face: 1, jaw: 0, t: Math.random() * 6,
  }));
}

function moveToward(m, tx, td, dist) {
  const dx = tx - m.x, dd = td - m.d, r = Math.hypot(dx, dd);
  if (r <= dist || r < 1e-9) { m.x = tx; m.d = td; return true; }
  m.x += dx / r * dist; m.d += dd / r * dist; if (Math.abs(dx) > 0.01) m.face = dx > 0 ? 1 : -1;
  return false;
}

// env: { px, pd, bx:[x0,x1] }. Returns nothing; positions/states updated in place.
export function updateCrocs(list, dt, env) {
  for (const m of [...list].sort((a, b) => (a.id < b.id ? -1 : 1))) {
    const sp = m.sp; m.t += dt;
    const dist = Math.hypot(env.px - m.x, env.pd - m.d);
    if (m.state === "recoil") {
      m.x += m.rdx * sp.recoil_dist * dt; m.d += m.rdd * sp.recoil_dist * dt; m.recoil -= dt;
      if (m.recoil <= 0) m.state = "patrol";
    } else {
      if (m.state === "patrol" && env.pd >= CORE_D && dist <= sp.detect_radius) m.state = "chase";
      else if (m.state === "chase" && (dist > sp.exit_radius || env.pd < CORE_D)) m.state = "patrol";
      if (m.state === "chase") moveToward(m, env.px, env.pd, sp.chase_speed * dt);
      else { const w = m.wps[m.wi]; if (moveToward(m, w[0], w[1], sp.patrol_speed * dt)) m.wi = (m.wi + 1) % m.wps.length; }
    }
    m.x = Math.max(env.bx[0], Math.min(env.bx[1], m.x));
    m.d = Math.max(sp.depths[0], Math.min(sp.depths[1], m.d));
    m.jaw += ((m.state === "chase" ? 1 : 0) - m.jaw) * Math.min(1, dt * 8);
  }
}

// nearest croc in hit range (ties by id), or null. Caller checks d ≥ 10 and invulnerability.
export function crocHit(list, px, pd) {
  let best = null, bd = 1e9;
  for (const m of [...list].sort((a, b) => (a.id < b.id ? -1 : 1))) {
    if (m.state === "recoil") continue;
    const r = Math.hypot(px - m.x, pd - m.d);
    if (r <= m.sp.hit_radius && r < bd) { bd = r; best = m; }
  }
  return best;
}
export function startRecoil(m, px, pd, tickHz = 60) {
  const dx = m.x - px, dd = m.d - pd, r = Math.hypot(dx, dd);
  if (r < 1e-9) { m.rdx = 1; m.rdd = 0; } else { m.rdx = dx / r; m.rdd = dd / r; }
  m.state = "recoil"; m.recoil = m.sp.recoil_ticks / tickHz;
}
// nearest distance from the diver to any croc (for the "Thủy quái!" warning)
export function crocNear(list, px, pd) { let bd = 1e9, m0 = null; for (const m of list) { const r = Math.hypot(px - m.x, pd - m.d); if (r < bd) { bd = r; m0 = m; } } return m0 ? { m: m0, dist: bd } : null; }

// Big original pixel crocodile: long snout, ridged back, dark olive, yellow eyes, jaws open while chasing.
const OL = "#3f4a26", OLD = "#2a3218", OLL = "#5e6b34", BELLY = "#a8a070", EYE = "#ffd23a", TOOTH = "#f4efd8", MOUTH = "#7a2a2a";
export function drawCroc(c, m, x, y, t) {
  c.save(); c.translate(Math.round(x), Math.round(y)); if (m.face < 0) c.scale(-1, 1);
  const sw = Math.sin(t * (m.state === "chase" ? 9 : 4));
  const jaw = Math.round(m.jaw * 4);
  // tail (segments wave)
  for (let i = 0; i < 6; i++) { const yy = Math.round(sw * (i / 2)); R(c, -18 - i * 4, -2 + yy + Math.floor(i / 3), 5, 4 - Math.floor(i / 2), OL); R(c, -18 - i * 4, -3 + yy, 2, 1, OLD); }
  // body
  R(c, -18, -5, 26, 9, OL); R(c, -16, -6, 22, 1, OLL); R(c, -17, 3, 24, 2, BELLY);
  for (let i = -16; i < 6; i += 3) R(c, i, -7, 2, 2, OLD); // ridged back
  for (let i = -15; i < 6; i += 4) R(c, i, -3, 2, 1, OLD);
  // legs
  const lg = Math.round(sw * 1.5);
  R(c, -14 + lg, 4, 4, 3, OLD); R(c, 2 - lg, 4, 4, 3, OLD);
  // head + long snout: upper jaw lifts while chasing
  R(c, 8, -5, 8, 7, OL); R(c, 9, -7, 3, 2, OLL);
  R(c, 10, -8, 2, 2, EYE); R(c, 11, -8, 1, 1, "#1a1220");
  R(c, 16, -4 - jaw, 14, 3, OL); R(c, 16, -5 - jaw, 12, 1, OLL); R(c, 28, -5 - jaw, 2, 1, OLD);
  R(c, 16, 0, 14, 2, OL); R(c, 16, 2, 13, 1, BELLY);
  if (jaw > 0) { R(c, 16, -1 - jaw, 13, jaw + 1, MOUTH); for (let i = 17; i < 29; i += 3) { R(c, i, -1 - jaw, 1, 1, TOOTH); R(c, i + 1, -1, 1, 1, TOOTH); } }
  else for (let i = 17; i < 29; i += 4) R(c, i, -1, 1, 1, TOOTH);
  c.restore();
}
