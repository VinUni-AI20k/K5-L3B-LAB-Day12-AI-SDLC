// Ingredient freshness (Test Contract v1.2 §1 "Độ tươi"): items {id, kind, fresh}; ids I1, I2, … continue across
// the whole campaign (progress.save.itemSeq). Numbers come from contract.freshness, defaults below if the key is missing.
import { save } from "./progress.js";

export const FRESH_DEFAULT = { initial: 100, gather_decay_per_s: 0.5, quan_decay_per_s: 0.25, spoiled_below: 30 };
export function freshCfg(contract) { return { ...FRESH_DEFAULT, ...(contract && contract.freshness) }; }

// next campaign-wide item id (demo mode never persists, so demo ids are thrown away with the demo save)
export function nextItemId() { save.itemSeq = (save.itemSeq || 0) + 1; return "I" + save.itemSeq; }
export function newItem(kind, cfg = FRESH_DEFAULT) { return { id: nextItemId(), kind, fresh: cfg.initial, spoiled: false }; }
export const idNum = (id) => +String(id).replace(/\D/g, "") || 0;
export const byId = (a, b) => idNum(a.id) - idNum(b.id);
// freshest first, tie by id (contract reservation / sell order)
export const freshestFirst = (a, b) => b.fresh - a.fresh || byId(a, b);

// decay every item by rate*dt (floor 0); returns the items that crossed from ≥ threshold to < threshold, by id
export function decay(items, rate, dt, below) {
  const out = [];
  for (const it of items) {
    it.fresh = Math.max(0, it.fresh - rate * dt);
    if (!it.spoiled && it.fresh < below) { it.spoiled = true; out.push(it); }
  }
  return out.sort(byId);
}
export const isSpoiled = (it, below = FRESH_DEFAULT.spoiled_below) => it.spoiled || it.fresh < below;
// plain contract item (what crosses the handover)
export const plain = (it) => ({ id: it.id, kind: it.kind, fresh: it.fresh });

// green → yellow → red by fresh %, grey when spoiled
export function freshColor(f, spoiled) {
  if (spoiled) return "#7a7a7a";
  return f >= 70 ? "#5ee07a" : f >= 45 ? "#ffd23a" : "#ff6b4a";
}
// tiny horizontal bar (dark track + fill)
export function freshBar(u, x, y, w, h, f, spoiled) {
  u.fillStyle = "rgba(0,0,0,.55)"; u.fillRect(x, y, w, h);
  u.fillStyle = freshColor(f, spoiled); u.fillRect(x, y, Math.max(spoiled ? 0 : 1, w * Math.max(0, Math.min(100, f)) / 100), h);
}
