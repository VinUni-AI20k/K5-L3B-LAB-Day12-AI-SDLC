// Meta progression (GUI-only "Sáng tạo của nhóm", not part of Test Contract v1.0):
// day counter, wallet, upgrades, species catalog, save/load. Scenes read stats(contract) and report back
// through the record* helpers; only main.js / the shop scene advance days or spend money.

const KEY = "chonoi.save.v1";

// Each upgrade has levels; `eff` is the bonus at each level (index 0 = not bought).
export const UPGRADES = {
  oxy:   { name: "Bình dưỡng khí",   desc: "+O₂ tối đa",              cost: [0, 150, 350, 700],  eff: [0, 10, 20, 35] },        // +s
  cap:   { name: "Giỏ lưới lớn",     desc: "+sức chứa giỏ",           cost: [0, 120, 300, 600],  eff: [0, 4, 8, 14] },          // +items
  fins:  { name: "Chân vịt",         desc: "bơi nhanh hơn",           cost: [0, 100, 260, 520],  eff: [1, 1.15, 1.3, 1.5] },    // × swim speed
  net:   { name: "Vợt bắt cá",       desc: "+tầm bắt cá",             cost: [0, 90, 220, 450],   eff: [0, 0.6, 1.2, 2.0] },     // +m catch radius
  stove: { name: "Bếp than hồng",    desc: "nấu nhanh hơn",           cost: [0, 140, 320],       eff: [1, 0.75, 0.5] },         // × cook time
  decor: { name: "Đèn lồng & bàn ghế", desc: "khách kiên nhẫn hơn",   cost: [0, 120, 300],       eff: [1, 1.15, 1.3] },         // × customer patience
  table2: { name: "Thêm bàn",        desc: "thêm chỗ cho khách",      cost: [0, 250, 600],       eff: [1, 2, 3] },              // tables (for a 1-table contract)
};
// which screen sells which track: morning prep (dive gear) vs evening prep (restaurant)
export const GEAR_UPGRADES = ["oxy", "cap", "fins", "net"];
export const QUAN_UPGRADES = ["stove", "decor", "table2"];

export function freshSave() {
  return { v: 1, day: 1, money: 0, totalEarned: 0, best: 0, up: { oxy: 0, cap: 0, fins: 0, net: 0, stove: 0, decor: 0, table2: 0 }, catalog: {}, history: [] };
}

export let save = load() || freshSave();

export function load() {
  try { const raw = localStorage.getItem(KEY); if (!raw) return null; const s = JSON.parse(raw); if (s && s.v === 1) return { ...freshSave(), ...s, up: { ...freshSave().up, ...s.up } }; } catch (e) {}
  return null;
}
// Demo mode (title-menu shortcuts): scenes still read stats()/recordCatch() but nothing is written to storage;
// main.js calls setDemo(false) on the way back, which reloads the real save and drops demo-only changes.
let demo = false;
export function setDemo(on) { demo = !!on; if (!demo) resume(); }
export const isDemo = () => demo;
export function persist() { if (demo) return; try { localStorage.setItem(KEY, JSON.stringify(save)); } catch (e) {} }
export function hasSave() { const s = load(); return !!(s && (s.day > 1 || s.money > 0)); }
export function newGame() { save = freshSave(); persist(); return save; }
export function resume() { save = load() || freshSave(); return save; }

// Effective tuning = contract values + upgrades. Scenes must read numbers from here, never hard-code.
export function stats(contract) {
  const g = contract.tuning.gather, q = contract.tuning.quan, u = save.up;
  return {
    oxygenMax: g.oxygen_max_s + UPGRADES.oxy.eff[u.oxy],
    holdCap: g.hold_capacity + UPGRADES.cap.eff[u.cap],
    swimSpeed: g.swim_speed * UPGRADES.fins.eff[u.fins],
    catchRadius: g.catch_radius + UPGRADES.net.eff[u.net],
    cookMul: UPGRADES.stove.eff[u.stove],
    patienceS: q.patience_s,
    patienceMul: UPGRADES.decor.eff[u.decor || 0],                          // × customer patience
    tables: (q.tables?.length || 1) - 1 + UPGRADES.table2.eff[u.table2 || 0], // contract tables + extra ones bought
  };
}

export function upgradeCost(id) { const up = UPGRADES[id], lv = save.up[id]; return lv + 1 < up.cost.length ? up.cost[lv + 1] : null; }
export function buy(id) {
  const c = upgradeCost(id); if (c == null || save.money < c) return false;
  save.money -= c; save.up[id]++; persist(); return true;
}

// catalog: species id -> { name, caught, firstDay }
export function recordCatch(speciesId, name) {
  const e = save.catalog[speciesId] || { name, caught: 0, firstDay: save.day };
  e.caught++; save.catalog[speciesId] = e; persist();
  return e.caught === 1; // true = new discovery
}

// called once per finished day by main.js
export function finishDay(summary) {
  // summary: { haulCount, earned, rep, served, left, score }
  save.money += summary.earned; save.totalEarned += summary.earned; save.best = Math.max(save.best, summary.score || 0);
  save.history.push({ day: save.day, ...summary }); if (save.history.length > 30) save.history.shift();
  save.day++; persist();
}
