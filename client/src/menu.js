// Premium dishes ("Đặc sản") — GUI-only "Sáng tạo của nhóm". The headless sim, game.contract.json and the kho file
// contract never see these: the premium ingredient kinds only exist in the client (gather → quán handover is in-memory).
// Every client read of the menu goes through menuAll(contract) = contract tuning.menu + GUI_MENU_EXTRA.

// premium ingredient kinds (drops from hunted monsters and deep fish); not sold / bought by Chú Sáu
export const PREMIUM_KINDS = ["thit_ca_sau", "thit_ran", "ca_loc_bong", "ca_loc_kl", "ca_linh_lon", "ca_tra_dau"];
const PK = new Set(PREMIUM_KINDS);
export const isPremiumKind = (k) => PK.has(k);

// deep species / boss id → the premium kind it drops (1 item on top of its contract-kind yield)
export const SPECIES_PREMIUM = { ca_loc_bong: "ca_loc_bong", dan_ca_linh_lon: "ca_linh_lon", ca_loc_khong_lo: "ca_loc_kl", ca_tra_dau: "ca_tra_dau" };
// defeated monsters → premium kind dropped into the basket
export const MONSTER_DROP = { ca_sau: "thit_ca_sau", ran_nuoc: "thit_ran" };

// same shape as contract tuning.menu entries (recipe / cook_s / price in k), plus premium: true
export const GUI_MENU_EXTRA = {
  ca_sau_nuong_sa_ot: { recipe: { thit_ca_sau: 1, keo_neo: 1 }, cook_s: 9, price: 320, premium: true },
  ran_xao_sa_ot: { recipe: { thit_ran: 1, bong_dien_dien: 1 }, cook_s: 7, price: 180, premium: true },
  ca_loc_bong_hap_bau: { recipe: { ca_loc_bong: 1, bong_sung: 1 }, cook_s: 8, price: 210, premium: true },
  ca_loc_kl_nuong_trui: { recipe: { ca_loc_kl: 1 }, cook_s: 10, price: 300, premium: true },
  goi_ca_linh_lon: { recipe: { ca_linh_lon: 1, keo_neo: 1 }, cook_s: 6, price: 160, premium: true },
  lau_ca_tra_dau: { recipe: { ca_tra_dau: 1, bong_sung: 2, bong_dien_dien: 1 }, cook_s: 14, price: 480, premium: true },
};
export const isPremiumDish = (id) => Object.prototype.hasOwnProperty.call(GUI_MENU_EXTRA, id);

// contract menu + premium extras (contract entries win on an id clash); cached per contract menu object
const memo = new WeakMap();
export function menuAll(contract) {
  const base = (contract && contract.tuning && contract.tuning.menu) || {};
  if (memo.has(base)) return memo.get(base);
  const all = { ...base };
  for (const [k, m] of Object.entries(GUI_MENU_EXTRA)) if (!all[k]) all[k] = m;
  memo.set(base, all);
  return all;
}
// how many times a recipe fits in a { kind: n } stock
export function servingsOf(recipe, stock) {
  let n = Infinity;
  for (const [k, q] of Object.entries(recipe || {})) n = Math.min(n, Math.floor((stock[k] || 0) / q));
  return Number.isFinite(n) ? n : 0;
}
// recipe lines for the phone's Sổ tay / Bà Tư (names resolved by the caller)
export const PREMIUM_HINT = "Đặc sản: hạ cá sấu, rắn nước, cá lớn vùng sâu hay Cá Tra Dầu là có thịt quý để nấu món giá cao.";
