// Day-loop screens of Test Contract v1.1 §2 ("Vòng ngày", "Shop và nâng cấp", "Menu, pause và HUD"):
//   DayIntro → (gather) → EveningIntro → (quán) → DayResult → Shop → next DayIntro … Summary after the last day.
// Every number comes from the contract (tuning.day_plan, tuning.menu, tuning.shop, tuning.score) or progress.js.
// All text is sans-serif ≥ size 7 (≈ 18.7 px at 1280×720 since the UI layer scales with the window).
import { W, H, screen, input, clamp, txt, panel, measure, wrap } from "./engine.js";
import { sfx, voiceLine } from "./audio.js";
import { portrait, icon, dishIcon, DISH_NAME, KIND_NAME } from "./art.js";
import { riverWorld } from "./story.js";
import * as progress from "./progress.js";

const GOLD = "#ffd23f", BORDER = "#f3d27a";
export const planFor = (contract, day) => (contract.tuning.day_plan || []).find((p) => p.day === day) || null;
export const planDays = (contract) => (contract.tuning.day_plan || []).length || Infinity; // no plan (old contract) = endless days
const kindName = (k) => KIND_NAME[k] || k;
const dishName = (k) => DISH_NAME[k] || k;
const ucfirst = (s) => s.charAt(0).toUpperCase() + s.slice(1);

class Base {
  constructor(tod = "dawn") { this.t = 0; this.tod = tod; this.cam = { x: 0, y: 40 }; this.done = false; }
  bg() {
    const c = screen.px;
    try { riverWorld(c, { t: this.t, cam: this.cam, v: { school: true, sunUp: this.tod === "dawn" ? 0.8 : 0.3 } }, this.tod); } catch (e) { c.fillStyle = "#0e2a44"; c.fillRect(0, 0, W, H); }
    const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, "rgba(6,12,28,.35)"); g.addColorStop(1, "rgba(6,12,28,.85)"); c.fillStyle = g; c.fillRect(0, 0, W, H);
  }
  tick(dt) { this.t += dt; this.cam.x += dt * 6; }
  finish(arg) { if (this.done) return; this.done = true; sfx("select"); this.onDone?.(arg); }
}

// ---------- DayIntro: "Ngày N" + Má Tư reads the plan (auto-continue after 4 s or any key) ----------
export class DayIntro extends Base {
  constructor(contract, day, st, onDone) {
    super("dawn"); this.onDone = onDone; this.day = day; this.plan = planFor(contract, day); this.st = st;
    const p = this.plan;
    const dishes = p ? Object.entries(p.dishes).map(([k, n]) => `${dishName(k)} ×${n}`).join(", ") : "món nào cũng được";
    const total = p ? Object.values(p.ingredients).reduce((a, b) => a + b, 0) : 0;
    this.line = p ? `Hôm nay quán nấu ${dishes}. Con lặn lấy đủ ${total} nguyên liệu nghen!` : "Hôm nay con cứ lặn kiếm thật nhiều đồ nghen!";
    this.autoS = 4;
    try { voiceLine("ba", this.line); } catch (e) {}
    sfx("whoosh");
  }
  update(dt) {
    this.tick(dt);
    if (this.t >= this.autoS || (this.t > 0.35 && input.anyKey() && !input.hit("pause") && !input.hit("mute"))) this.finish();
  }
  draw() {
    this.bg(); const u = screen.ui, t = this.t, k = clamp(t / 0.4, 0, 1);
    txt(`NGÀY ${this.day}`, W / 2, 42, { size: 30 * (1.4 - 0.4 * k), align: "center", color: GOLD, weight: 900, italic: true, stroke: "#3a1410", sw: 6, rot: -0.03 });
    txt(`Đồ nghề hôm nay: O₂ ${this.st.oxygenMax} s · Máu ${this.st.hpMax}`, W / 2, 58, { size: 8, align: "center", color: "#bff3ff", weight: 800, stroke: "#06101e", sw: 2 });
    // Má Tư dialogue box (portrait + typewriter line)
    const bx = 20, by = 66, bw = W - 40, bh = 58;
    panel(bx, by, bw, bh, { fill: "rgba(20,10,24,.9)", border: BORDER, r: 8, bw: 1.5 });
    u.imageSmoothingEnabled = false;
    try { u.drawImage(portrait("ba"), bx + 6, by + 6, 46, 46); } catch (e) {}
    txt("MÁ TƯ", bx + 60, by + 13, { size: 8, color: GOLD, weight: 900 });
    const shown = this.line.slice(0, Math.floor(t * 60));
    wrap(shown, bw - 70, 8).slice(0, 4).forEach((l, i) => txt(l, bx + 60, by + 25 + i * 10, { size: 8, color: "#fff", weight: 700 }));
    // needed list
    if (this.plan) {
      const ing = Object.entries(this.plan.ingredients), cols = 3, rw = (W - 40) / cols, ly = by + bh + 8;
      panel(bx, ly, bw, 16 + Math.ceil(ing.length / cols) * 13, { fill: "rgba(8,20,38,.85)", border: "#7ac0ff", r: 6 });
      txt("CẦN LẤY", bx + bw / 2, ly + 10, { size: 7, align: "center", color: "#9fd8ff", weight: 900 });
      ing.forEach(([kk, n], i) => { const x = bx + 8 + (i % cols) * rw, y = ly + 14 + Math.floor(i / cols) * 13; u.drawImage(icon(kk), x, y, 10, 10); txt(`${ucfirst(kindName(kk))} ×${n}`, x + 14, y + 8, { size: 8, color: "#fff", weight: 800 }); });
    }
    const left = Math.max(0, Math.ceil(this.autoS - t));
    txt(`Phím bất kỳ: xuống nước · tự đi sau ${left} s`, W / 2, H - 8, { size: 7, align: "center", color: "rgba(255,255,255,.65)", weight: 700 });
  }
}

// how many servings of a dish the stock covers
export function servings(recipe, stock) { let n = Infinity; for (const [k, q] of Object.entries(recipe)) n = Math.min(n, Math.floor((stock[k] || 0) / q)); return n === Infinity ? 0 : n; }

// ---------- EveningIntro: stock received + which plan dishes can be cooked ----------
export class EveningIntro extends Base {
  // items (v1.2): the gather handover [{ id, kind, fresh }] — listed with fresh %; servings count usable (≥ spoiled_below) only
  constructor(contract, day, stock, onDone, items = null) {
    super("dusk"); this.onDone = onDone; this.day = day; this.stock = stock || {}; this.menu = contract.tuning.menu;
    this.below = { spoiled_below: 30, ...contract.freshness }.spoiled_below;
    this.items = Array.isArray(items) ? items : null;
    if (this.items) { this.usable = {}; for (const it of this.items) if (it.fresh >= this.below) this.usable[it.kind] = (this.usable[it.kind] || 0) + 1; }
    this.plan = planFor(contract, day);
    this.ids = this.plan ? Object.keys(this.plan.dishes) : Object.keys(this.menu);
  }
  update(dt) { this.tick(dt); if (this.t > 0.6 && (input.hit("confirm") || input.hit("interact") || input.hit("catch"))) this.finish(this.ids); }
  draw() {
    this.bg(); const u = screen.ui; u.imageSmoothingEnabled = false;
    txt(`NGÀY ${this.day} · MỞ QUÁN`, W / 2, 26, { size: 18, align: "center", color: "#ff8a3d", weight: 900, italic: true, stroke: "#3a1410", sw: 5 });
    // stock received
    const ks = Object.entries(this.stock).filter(([, n]) => n > 0), its = this.items, rh = its ? 22 : 13;
    panel(16, 38, 170, 22 + Math.max(1, ks.length) * rh, { fill: "rgba(8,20,38,.88)", border: "#7ac0ff", r: 6 });
    txt("NHẬP KHO" + (its ? " · ĐỘ TƯƠI" : ""), 101, 49, { size: 8, align: "center", color: "#9fd8ff", weight: 900 });
    if (!ks.length) txt("Kho trống — giỏ đã mất", 101, 64, { size: 8, align: "center", color: "#ffb0b0", weight: 800 });
    ks.forEach(([k, n], i) => { const y = 54 + i * rh; u.drawImage(icon(k), 24, y, 10, 10); txt(ucfirst(kindName(k)), 38, y + 8, { size: 8, color: "#fff", weight: 800 }); txt("×" + n, 178, y + 8, { size: 8, align: "right", color: "#cfe", weight: 900 });
      if (!its) return; // v1.2: each item id with its fresh % (spoiled = "ươn" in red); clipped to the panel width
      let line = "", spoiled = false;
      for (const it of its.filter((q) => q.kind === k)) { const bad = it.fresh < this.below; spoiled ||= bad; const part = `${it.id} ${bad ? "ươn" : Math.floor(it.fresh) + "%"}`; const next = line ? line + " · " + part : part; if (measure(next, 7, 700) > 150) { line += " …"; break; } line = next; }
      txt(line, 24, y + 18, { size: 7, color: spoiled ? "#ffb0a0" : "rgba(220,245,255,.8)", weight: 700 }); });
    // plan dishes
    const x0 = 196, w0 = W - x0 - 16;
    panel(x0, 38, w0, 22 + this.ids.length * 24, { fill: "rgba(30,12,16,.88)", border: BORDER, r: 6 });
    txt("THỰC ĐƠN KẾ HOẠCH", x0 + w0 / 2, 49, { size: 8, align: "center", color: GOLD, weight: 900 });
    this.ids.forEach((id, i) => {
      const y = 54 + i * 24, m = this.menu[id]; if (!m) return;
      const can = servings(m.recipe, this.usable || this.stock), want = this.plan?.dishes[id];
      u.drawImage(dishIcon(id), x0 + 6, y, 18, 18);
      txt(dishName(id), x0 + 28, y + 8, { size: 8, color: "#fff", weight: 800 });
      txt(Object.entries(m.recipe).map(([k, q]) => `${kindName(k)} ×${q}`).join(" + ") + ` · ${m.price}k`, x0 + 28, y + 18, { size: 7, color: "rgba(255,230,200,.75)", weight: 700 });
      txt(can > 0 ? `nấu được ×${can}` + (want ? `/${want}` : "") : "thiếu đồ", x0 + w0 - 6, y + 8, { size: 7, align: "right", color: can > 0 ? "#7dffb0" : "#ff8a8a", weight: 900 });
    });
    if (this.t > 0.6) txt("Enter / E: mở quán ▶", W / 2, H - 10, { size: 9, align: "center", color: "#fff", weight: 900, alpha: 0.7 + 0.3 * Math.sin(this.t * 5) });
  }
}

// ---------- DayResult: served / left, money, tips, reputation change ----------
export class DayResult extends Base {
  constructor(sum, onDone) { super("night"); this.s = sum; this.onDone = onDone; sfx("fanfare"); }
  update(dt) { this.tick(dt); if (this.t > 0.8 && (input.hit("confirm") || input.hit("interact") || input.hit("catch"))) this.finish(); }
  draw() {
    this.bg(); const s = this.s;
    if (s.closedEarly) txt("Đóng sớm", W / 2 + 118, 44, { size: 8, align: "right", color: "#ffb36b", weight: 900 });
    txt(`KẾT SỔ NGÀY ${s.day}`, W / 2, 34, { size: 20, align: "center", color: GOLD, weight: 900, italic: true, stroke: "#3a1410", sw: 5 });
    panel(W / 2 - 130, 46, 260, 166, { fill: "rgba(8,20,38,.9)", border: BORDER, r: 8 });
    const d = (s.rep ?? 0) - (s.rep0 ?? s.rep ?? 0);
    const rows = [
      ["Khách đã phục vụ", String(s.served ?? 0), "#7dffb0"],
      ["Khách bỏ đi", String(s.left ?? 0), (s.left || 0) ? "#ff8a8a" : "#fff"],
      ["Khách về vì hết món", String(s.missed ?? 0), (s.missed || 0) ? "#ffb36b" : "#fff"],
      ["Tiền thu (gồm boa)", `${s.earned ?? 0}k`, GOLD],
      ["Tiền boa", `${s.tips ?? 0}k`, "#ffe14d"],
      ...(progress.huntIncome?.(s.day) ? [["Săn cá bán thương lái", `+${progress.huntIncome(s.day)}k`, "#ffb36b"]] : []),
      ["Uy tín", `${(s.rep0 ?? 0).toFixed(1)} → ${(s.rep ?? 0).toFixed(1)} (${d >= 0 ? "+" : ""}${d.toFixed(1)})`, d >= 0 ? "#7dffb0" : "#ff8a8a"],
      ["Điểm ngày", String(s.score ?? 0), "#fff"],
      ["Ví hiện có", `${progress.save.money}k`, GOLD],
    ];
    const rh = rows.length > 8 ? 16.5 : 18;
    rows.forEach(([a, b, col], i) => { const y = 66 + i * rh; txt(a, W / 2 - 118, y, { size: 8, color: "rgba(255,255,255,.8)", weight: 700 }); txt(b, W / 2 + 118, y, { size: 9, align: "right", color: col, weight: 900 }); });
    if (this.t > 0.8) txt("Enter: vào Shop ▶", W / 2, H - 12, { size: 9, align: "center", color: "#fff", weight: 900, alpha: 0.7 + 0.3 * Math.sin(this.t * 5) });
  }
}

// ---------- Shop: contract upgrades first, creative extras after; auto-closes after shop.max_ticks ----------
const CU = { oxygen: { name: "Bình oxy", eff: (l) => `O₂ ${l.oxygen_max_s} s` }, hp: { name: "Áo phao (thêm Máu)", eff: (l) => `${l.hp_max} Máu` } };
export class Shop extends Base {
  constructor(contract, nextLabel, onDone) {
    super("night"); this.c = contract; this.onDone = onDone; this.nextLabel = nextLabel;
    const ups = contract.tuning.shop?.upgrades || {};
    this.rows = [{ head: "NÂNG CẤP CHUẨN" }];
    for (const id of Object.keys(ups)) this.rows.push({ core: id });
    this.rows.push({ head: "ĐỒ THÊM (SÁNG TẠO)" });
    for (const id of [...(progress.GEAR_UPGRADES || []), ...(progress.HUNT_UPGRADES || []), ...(progress.QUAN_UPGRADES || [])]) if (progress.UPGRADES[id]) this.rows.push({ extra: id });
    this.rows.push({ done: true });
    this.items = this.rows.map((r, i) => (r.head ? -1 : i)).filter((i) => i >= 0);
    this.sel = 0; this.msg = null;
    this.left = (contract.tuning.shop?.max_ticks ?? 600) / (contract.tuning.tick_hz || 60); // frozen while paused (main.js skips update)
  }
  update(dt) {
    this.tick(dt); this.left -= dt;
    if (this.msg) { this.msg.life -= dt; if (this.msg.life <= 0) this.msg = null; }
    if (this.left <= 0) { this.left = 0; return this.finish("time"); }
    if (input.hit("up")) { this.sel = (this.sel + this.items.length - 1) % this.items.length; sfx("click"); }
    if (input.hit("down")) { this.sel = (this.sel + 1) % this.items.length; sfx("click"); }
    if (this.t > 0.3 && (input.hit("confirm") || input.hit("interact") || input.hit("catch"))) this.activate(this.rows[this.items[this.sel]]);
  }
  activate(r) {
    if (r.done) return this.finish("done");
    let ok = false;
    if (r.core) ok = progress.buyContract(this.c, r.core);
    else if (r.extra) ok = progress.buy(r.extra);
    if (ok) { sfx("coin"); this.msg = { text: "Đã mua! Có hiệu lực từ ngày mai", col: "#7dffb0", life: 1.6 }; }
    else { sfx("hurt"); this.msg = { text: "Không mua được (thiếu tiền hoặc đã tối đa)", col: "#ff8a8a", life: 1.6 }; }
  }
  rowText(r) {
    if (r.core) {
      const lv = this.c.tuning.shop.upgrades[r.core], cur = progress.save.cu[r.core] || 0, nx = lv[cur], d = CU[r.core] || { name: r.core, eff: () => "" };
      const curTxt = cur ? `đã có cấp ${cur} (${d.eff(lv[cur - 1])})` : "chưa có";
      return { name: d.name, sub: curTxt, price: nx ? `${nx.price}k → ${d.eff(nx)}` : "TỐI ĐA", can: !!nx && progress.save.money >= nx.price };
    }
    if (r.extra) {
      const u = progress.UPGRADES[r.extra], cost = progress.upgradeCost(r.extra), lv = progress.save.up[r.extra] || 0;
      return { name: u.name, sub: `${u.desc} · cấp ${lv}`, price: cost == null ? "TỐI ĐA" : `${cost}k`, can: cost != null && progress.save.money >= cost };
    }
    return { name: this.nextLabel, sub: "", price: "", can: true };
  }
  draw() {
    this.bg(); const s = progress.save;
    txt("SHOP CHỢ NỔI", W / 2, 22, { size: 16, align: "center", color: GOLD, weight: 900, italic: true, stroke: "#3a1410", sw: 4 });
    txt(`Ví ${s.money}k · Tổng thu ${s.totalEarned}k`, 16, 22, { size: 8, color: GOLD, weight: 900 });
    txt(`Tự đóng sau ${Math.ceil(this.left)} s`, W - 16, 22, { size: 8, align: "right", color: this.left < 4 ? "#ff8a8a" : "#cfe", weight: 800 });
    const x0 = 24, w0 = W - 48; let y = 32;
    this.rows.forEach((r, i) => {
      if (r.head) { txt(r.head, x0 + 2, y + 9, { size: 7, color: r.head.includes("SÁNG") ? "#c9a6ff" : "#9fd8ff", weight: 900 }); y += 12; return; }
      const sel = this.items[this.sel] === i, rt = this.rowText(r), h = r.done ? 16 : 17;
      panel(x0, y, w0, h - 2, { fill: sel ? "rgba(255,160,60,.25)" : "rgba(8,20,38,.82)", border: sel ? GOLD : "rgba(243,210,122,.35)", r: 5 });
      txt((sel ? "▶ " : "") + rt.name, x0 + 6, y + 10, { size: 8, color: "#fff", weight: 900 });
      if (rt.sub) txt(rt.sub, x0 + 150, y + 10, { size: 7, color: "rgba(255,255,255,.65)", weight: 700 });
      if (rt.price) txt(rt.price, x0 + w0 - 6, y + 10, { size: 8, align: "right", color: rt.price === "TỐI ĐA" ? "#9fd8ff" : rt.can ? "#7dffb0" : "#ff8a8a", weight: 900 });
      y += h;
    });
    if (this.msg) txt(this.msg.text, W / 2, H - 20, { size: 9, align: "center", color: this.msg.col, weight: 900, stroke: "#1a1220", sw: 2 });
    txt("↑↓ chọn · Enter mua · Esc/P tạm dừng · nâng cấp có hiệu lực từ ngày kế tiếp", W / 2, H - 6, { size: 7, align: "center", color: "rgba(255,255,255,.6)", weight: 700 });
  }
}

// ---------- Summary after the last day ----------
export class Summary extends Base {
  constructor(contract, onDone) {
    super("night"); this.onDone = onDone; const s = progress.save;
    this.rep = progress.repNow(contract);
    this.score = s.totalEarned + (contract.tuning.score?.reputation_multiplier ?? 100) * Math.floor(this.rep);
    const best = Object.entries(s.sold || {}).sort((a, b) => b[1] - a[1])[0];
    this.best = best ? `${dishName(best[0])} (${best[1]} suất)` : "chưa bán được món nào";
    this.bestId = best?.[0];
    sfx("fanfare");
  }
  update(dt) { this.tick(dt); if (this.t > 1 && (input.hit("confirm") || input.hit("interact") || input.hit("catch"))) this.finish(); }
  draw() {
    this.bg(); const s = progress.save;
    txt("TỔNG KẾT MÙA NƯỚC NỔI", W / 2, 36, { size: 20, align: "center", color: GOLD, weight: 900, italic: true, stroke: "#3a1410", sw: 5 });
    panel(W / 2 - 130, 50, 260, 120, { fill: "rgba(8,20,38,.9)", border: BORDER, r: 8 });
    [["Tổng tiền thu", `${s.totalEarned}k`], ["Ví còn lại", `${s.money}k`], ["Tổng điểm", String(this.score)], ["Uy tín", this.rep.toFixed(1) + " ★"], ["Món bán chạy", this.best]].forEach(([a, b], i) => {
      const y = 72 + i * 20; txt(a, W / 2 - 118, y, { size: 8, color: "rgba(255,255,255,.8)", weight: 700 }); txt(b, W / 2 + 118, y, { size: 9, align: "right", color: GOLD, weight: 900 });
    });
    if (this.bestId) { screen.ui.imageSmoothingEnabled = false; screen.ui.drawImage(dishIcon(this.bestId), W / 2 - 12, 176, 24, 24); }
    if (this.t > 1) txt("Enter: về màn hình chính", W / 2, H - 12, { size: 9, align: "center", color: "#fff", weight: 900, alpha: 0.7 + 0.3 * Math.sin(this.t * 5) });
  }
}

// ---------- pause overlay (drawn by main.js over the frozen scene) ----------
export const PAUSE_ITEMS = ["Tiếp tục", "Về menu"];
export const PAUSE_ITEMS_QUAN = ["Tiếp tục", "Đóng quán sớm", "Về menu"];
export function drawPause(sel, items = PAUSE_ITEMS) {
  const u = screen.ui;
  u.save(); u.fillStyle = "rgba(4,8,20,.66)"; u.fillRect(0, 0, W, H); u.restore();
  const extra = (items.length - 2) * 20;
  panel(W / 2 - 80, H / 2 - 46, 160, 92 + extra, { fill: "rgba(14,22,40,.95)", border: BORDER, r: 10, bw: 1.5 });
  txt("TẠM DỪNG", W / 2, H / 2 - 24, { size: 14, align: "center", color: GOLD, weight: 900 });
  items.forEach((s, i) => {
    const y = H / 2 - 4 + i * 20, on = i === sel;
    if (on) panel(W / 2 - 60, y - 11, 120, 16, { fill: "rgba(255,160,60,.25)", border: GOLD, r: 6 });
    txt((on ? "▶ " : "") + s, W / 2, y + 1, { size: 10, align: "center", color: on ? "#fff" : "rgba(255,255,255,.7)", weight: 900 });
  });
  txt("Esc/P: tiếp tục · ↑↓ Enter", W / 2, H / 2 + 40 + extra, { size: 7, align: "center", color: "rgba(255,255,255,.55)", weight: 700 });
}
