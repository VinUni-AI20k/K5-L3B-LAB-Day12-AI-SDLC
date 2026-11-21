"use strict";
/*
 * Hiệu ứng từ sự kiện mới (CN.events.fresh): chữ nổi ("+3 cá linh", "-1 Máu"), rung màn hình.
 * Tên trường trong `data` theo Test Contract v1.1; trường nào thiếu thì hiện chữ chung.
 */
(function (CN) {
  const { ctx, text, COLOR, kname, dname } = CN;
  const pops = [];
  let shakeAt = -10;

  const num = (v, d) => (typeof v === "number" ? v : d);
  const UPGRADE_NAME = { oxygen: "Bình oxy", hp: "Áo phao", weapon: "Lao xua", net: "Vợt hút cá" };
  const FAIL = { funds: "Không đủ tiền", max_level: "Đã tối đa", out_of_stock: "Hết hàng", unknown: "Không mua được" };
  // tên sự kiện -> [chữ, màu, rung?]
  const LABEL = {
    gather: (d) => ["+" + num(d.count, 1) + " " + kname(d.kind || d.item || "?"), COLOR.gold],
    fish_caught: (d) => ["+" + num(d.count, 1) + " " + kname(d.kind || "cá"), COLOR.oxy],
    hold_full: () => ["Giỏ đầy!", COLOR.danger],
    oxygen_empty: () => ["Hết hơi!", COLOR.danger, true],
    choke: () => ["-1 Máu", COLOR.hp, true],
    monster_hit: (d) => ["-1 Máu" + (d.lost && d.lost.length ? " · rơi " + d.lost.length + " món" : ""), COLOR.hp, true],
    faint: () => ["Ngất!", COLOR.danger, true],
    cook_started: (d) => ["Nấu " + dname(d.dish_id || d.dish), COLOR.text],
    dish_ready: () => ["Món chín!", COLOR.ok],
    dish_picked: () => ["Bưng món", COLOR.text],
    served: () => ["Đã dọn món", COLOR.ok],
    paid: (d) => ["+" + (num(d.price, 0) + num(d.tip, 0)) + "k", COLOR.gold],
    customer_left: () => ["Khách bỏ đi!", COLOR.danger, true],
    no_dish: () => ["Thiếu nguyên liệu", COLOR.danger],
    bought: (d) => ["Đã mua " + (UPGRADE_NAME[d.upgrade] || d.upgrade) + " cấp " + d.level, COLOR.ok],
    buy_failed: (d) => [FAIL[d.reason] || "Không mua được", COLOR.danger],
  };

  CN.fx = {
    anchor: null, // cảnh đặt mỗi khung hình: điểm trên màn hình để chữ nổi xuất hiện (thường là người chơi)
    ingest(fresh) {
      if (CN.events.restarted) pops.length = 0;
      for (const e of fresh) {
        const f = LABEL[e.name];
        const r = f && f(e.data || {});
        if (!r) continue;
        const a = CN.fx.anchor || { x: innerWidth / 2, y: innerHeight / 2 };
        pops.push({ text: r[0], color: r[1], x: a.x, y: a.y - (pops.length % 3) * 22, born: CN.now() });
        if (r[2]) shakeAt = CN.now();
      }
    },
    shake() {
      const dt = CN.now() - shakeAt;
      if (dt > 0.3) return [0, 0];
      const m = (1 - dt / 0.3) * 6;
      return [Math.sin(dt * 95) * m, Math.cos(dt * 83) * m];
    },
    draw() {
      const now = CN.now();
      for (let i = pops.length - 1; i >= 0; i--) {
        const p = pops[i], age = now - p.born;
        if (age > 1.5) { pops.splice(i, 1); continue; }
        ctx.globalAlpha = 1 - age / 1.5;
        text(p.text, p.x + 1, p.y - age * 36 + 1, { size: 20, align: "center", color: "rgba(0,0,0,.6)", weight: "700" });
        text(p.text, p.x, p.y - age * 36, { size: 20, align: "center", color: p.color, weight: "700" });
        ctx.globalAlpha = 1;
      }
    },
  };
})(window.CN);
