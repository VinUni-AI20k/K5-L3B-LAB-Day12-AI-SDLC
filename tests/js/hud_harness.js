"use strict";
/*
 * Harness cho tests/test_warnings.py: nạp script của chonoi/web/index.html với canvas giả, chạy các tình huống
 * cảnh báo (Ticket-04, AC-P4-04/05) rồi in JSON ra stdout. Dùng: node hud_harness.js <đường dẫn index.html>
 */
const fs = require("fs");

const html = fs.readFileSync(process.argv[2], "utf8");
const src = html.split("<script>")[1].split("</script>")[0]
  .replace("poll();", "").replace(/requestAnimationFrame\(frame\);\s*$/, "");

let drawn = [], fonts = [], strokes = 0, last = null;
const mockCtx = new Proxy({}, {
  get: (t, k) => {
    // `last` ghi lại kiểu của lần vẽ chữ gần nhất: viền (strokeStyle) và màu chữ (fillStyle)
    if (k === "fillText") return (s) => { drawn.push(String(s)); if (last) last.fill = t.fillStyle; };
    if (k === "strokeText") return () => { strokes++; last = { stroke: t.strokeStyle, fill: null }; };
    if (k === "createLinearGradient") return () => ({ addColorStop() {} });
    if (k === "measureText") return (s) => ({ width: String(s).length * 10 });
    return t[k] !== undefined ? t[k] : () => {};
  },
  set: (t, k, v) => { if (k === "font") fonts.push(v); t[k] = v; return true; },
});
global.document = { getElementById: () => ({ getContext: () => mockCtx, width: 0, height: 0 }) };
global.Image = class { get complete() { return false; } set src(v) {} };  // sprite chưa tải -> dùng phương án dự phòng
global.addEventListener = () => {}; global.requestAnimationFrame = () => {}; global.setTimeout = () => {};
global.fetch = () => new Promise(() => {}); global.innerWidth = 1280; global.innerHeight = 720; global.window = {};

const hud = new Function(src + `
return { warningList, drawGather, drawQuan, drawWarnings, toggleHC, text,
  setSnap: (s) => { snap = s; }, hc: () => HC };`)();

const META_G = { monsters: { species: { ca_sau: { detect_radius: 10 } } } };
const gather = (o) => Object.assign({
  mode: "gather", tick: 5, time_left_ticks: 9000, money: 0, score: 300, reputation: 3, hold: [], hold_capacity: 12,
  nodes: [], fish: [], events: [], meta: META_G,
  player: { pos: [20, 10], oxygen_ticks: 1800, oxygen_max_ticks: 1800, hp: 3, hp_max: 3, at_surface: false },
  monsters: [{ id: "M1", kind: "ca_sau", pos: [60, 24], state: "patrol", waypoints: [[60, 24], [64, 24]], target_idx: 1 }],
}, o || {});
const withPlayer = (p, extra) => gather(Object.assign({ player: Object.assign({}, gather().player, p) }, extra || {}));
const ids = (s) => hud.warningList(s).map((w) => w.id);
const texts = (s) => hud.warningList(s).map((w) => w.text);
const customer = (id, table, ticks, state) => ({ id, table_id: table, dish_id: "ca_loc_nuong_trui", state: state || "waiting", patience_ticks_left: ticks });
const quan = (cs) => ({ mode: "quan", tick: 5, time_left_ticks: 9000, money: 0, score: 300, reputation: 3, stock: [], stoves: [], tables: [],
  customers: cs, hand: null, events: [], meta: { patience_s: 60 } });

const out = {};

// 1. thủy quái: gần (cách 15 m = 1.5 × bán kính phát hiện) / xa / đang đuổi
out.monster_near = ids(gather({ monsters: [{ id: "M1", kind: "ca_sau", pos: [35, 10], state: "patrol" }] }));
out.monster_edge = ids(gather({ monsters: [{ id: "M1", kind: "ca_sau", pos: [35.1, 10], state: "patrol" }] }));
out.monster_far = ids(gather());
out.monster_chase_far = ids(gather({ monsters: [{ id: "M1", kind: "ca_sau", pos: [90, 28], state: "chase" }] }));

// 2. oxy: ranh giới 25% của 1800 = 450 (dưới 450 mới báo), cạn = "Hết hơi!", ở mặt nước không báo
out.oxygen = {};
[1800, 450, 449, 300, 1, 0].forEach((o) => { out.oxygen[o] = texts(withPlayer({ oxygen_ticks: o }, { monsters: [] })); });
out.oxygen_surface = texts(withPlayer({ oxygen_ticks: 0, at_surface: true, pos: [20, 0] }, { monsters: [] }));

// 3. khách sắp giận: 25% của 3600 = 900
out.angry = {};
[3600, 900, 899, 1].forEach((t) => { out.angry[t] = texts(quan([customer("C1", "T1", t)])); });
out.angry_eating = texts(quan([customer("C1", "T1", 100, "eating")]));
out.angry_tables = texts(quan([customer("C1", "T3", 10), customer("C2", "T1", 20), customer("C3", "T2", 3000)]));
out.angry_not_in_gather = ids(gather());

// 4. vẽ thật: cảnh báo hiện chữ; phương án dự phòng "⚠" khi sprite chưa tải
drawn = [];
hud.setSnap(withPlayer({ oxygen_ticks: 0 }, { monsters: [{ id: "M1", kind: "ca_sau", pos: [30, 10], state: "chase" }] }));
hud.drawWarnings(1280, 720);
out.drawn_gather = drawn.slice();
drawn = [];
hud.setSnap(quan([customer("C1", "T1", 100)]));
hud.drawWarnings(1280, 720);
out.drawn_quan = drawn.slice();

// 5. tương phản cao: bật/tắt, chữ đậm, viền đen cho chữ
fonts = []; strokes = 0; drawn = [];
hud.setSnap(gather());
hud.drawGather(1280, 720);
out.normal_has_bold = fonts.some((f) => f.startsWith("bold ") && !f.includes("20px"));
out.normal_strokes = strokes;
hud.toggleHC();
out.hc_on = hud.hc();
fonts = []; strokes = 0;
hud.drawGather(1280, 720);
out.hc_all_bold = fonts.length > 0 && fonts.every((f) => f.startsWith("bold "));
out.hc_strokes = strokes;
// chữ tối (vd nhãn bếp #111 trên nền sáng) -> đen + viền TRẮNG; chữ mờ -> trắng + viền đen; chữ sáng giữ màu + viền đen
out.hc_style = {};
[["dark", "#111"], ["dark_brown", "#2a1a0a"], ["dim_rgba", "rgba(255,255,255,.4)"], ["dim_grey", "#9fb3c0"], ["light_red", "#ff6b81"]].forEach(([k, c]) => {
  last = null;
  hud.text("x", 0, 0, { color: c });
  out.hc_style[k] = last;
});
hud.toggleHC();
out.hc_off = !hud.hc();
last = null;
hud.text("x", 0, 0, { color: "#111" });
out.normal_style_dark = last;  // bình thường: không viền, nên không ghi gì

console.log(JSON.stringify(out));
