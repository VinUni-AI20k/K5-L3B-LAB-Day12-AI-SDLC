"use strict";
/* HUD buổi tối (Ticket-02 §2): đồng hồ ca, tiền ca, uy tín, món đang cầm, kho khả dụng. Món + kiên nhẫn từng bàn và bếp vẽ trong cảnh. */
(function (CN) {
  const { text, ui, COLOR, fmtTime, dname } = CN;

  function stars(rep) {
    let s = "";
    for (let i = 1; i <= 5; i++) s += rep >= i ? "★" : "☆";
    return s;
  }

  CN.hud.quan = function (w, h, snap) {
    const low = (snap.time_left_ticks || 0) <= 30 * 60;
    ui.panel(10, 8, 560, 52);
    text("⏱ " + fmtTime(snap.time_left_ticks), 24, 35, { size: 24, base: "middle", weight: "800", color: low ? COLOR.danger : COLOR.text });
    const shift = snap.shift_earned ?? snap.money ?? 0;
    text("Tiền ca " + shift + "k", 150, 35, { size: 20, base: "middle", weight: "700", color: COLOR.gold });
    const rep = snap.reputation ?? 0;
    text(stars(rep) + " " + rep.toFixed(1), 320, 35, { size: 20, base: "middle", color: COLOR.gold });
    // Chế độ day: điểm/tiền tổng chỉ cộng khi đóng ca (DaySim), nên trong ca chỉ hiện tiền ca để khỏi hiểu nhầm.
    if (snap.day === undefined) text("Điểm " + (snap.score ?? 0), 556, 35, { size: 18, base: "middle", align: "right" });
    else text("Ví " + (snap.money ?? 0) + "k", 556, 35, { size: 18, base: "middle", align: "right", color: COLOR.muted });
    if (snap.day !== undefined) { ui.panel(w - 130, 8, 120, 52); text("Ngày " + snap.day, w - 70, 35, { size: 20, align: "center", base: "middle", weight: "800", color: COLOR.gold }); }

    // kho khả dụng
    const stock = snap.stock || {}, kinds = Object.keys(stock).filter((k) => stock[k] > 0);
    const pw = Math.max(220, 90 + kinds.length * 84), y0 = h - 76;
    ui.panel(10, y0, pw, 66);
    text("Kho", 24, y0 + 40, { size: 20, weight: "800" });
    if (!kinds.length) text("(trống)", 80, y0 + 40, { size: 18, color: COLOR.muted });
    kinds.forEach((k, i) => {
      const x0 = 80 + i * 84;
      CN.ui.icon(k, x0 + 18, y0 + 33, 32);
      text("×" + stock[k], x0 + 38, y0 + 40, { size: 20, weight: "700" });
    });

    // món đang cầm
    const hx = 10 + pw + 12;
    ui.panel(hx, y0, 280, 66);
    text("Tay", hx + 14, y0 + 40, { size: 20, weight: "800" });
    if (snap.hand) {
      const id = typeof snap.hand === "string" ? snap.hand : snap.hand.dish_id;
      ui.dish(id, hx + 82, y0 + 32, 40);
      text(dname(id), hx + 110, y0 + 40, { size: 18, weight: "600" });
    } else text("(trống)", hx + 66, y0 + 40, { size: 18, color: COLOR.muted });

    text("Esc tạm dừng", w - 14, h - 16, { size: 18, align: "right", color: COLOR.muted });
  };
})(window.CN);
