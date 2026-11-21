"use strict";
/*
 * Cảnh buổi tối (quan): quán nhìn từ trên xuống, x sang phải, z lên (bắc).
 * Chỉ vẽ. Tên trường của khách theo docs/contracts/ (đang giả định: table_id, dish_id, state, patience_ticks_left).
 * Gợi ý "E Nấu / Bưng / Dọn món" chỉ để hiển thị; sim chọn đối tượng tương tác thật.
 */
(function (CN) {
  const { ctx, text, ui, COLOR } = CN;
  CN.layout.quan = { top: 70, bottom: 84 };

  const dishOf = (c) => c.dish_id || c.dish || (c.order && c.order.dish_id) || null;
  const patienceLeft = (c) => (c.patience_ticks_left !== undefined ? c.patience_ticks_left : c.patience_ticks);

  function view(w, h, snap) {
    const meta = snap.meta || {};
    const b = meta.bounds || { x: [0, 16], z: [0, 10] };
    const X = b.x[1], Z = b.z[1];
    const { top, bottom } = CN.layout.quan;
    const s = Math.max(10, Math.min((w - 40) / X, (h - top - bottom) / Z));
    const ox = (w - s * X) / 2, oy = top;
    return { meta, X, Z, s, w, h, sx: (x) => ox + x * s, sy: (z) => oy + (Z - z) * s };
  }

  function drawRoom(v) {
    const { X, Z, s } = v, x0 = v.sx(0), y0 = v.sy(Z);
    ctx.fillStyle = "#c9a36b"; ctx.fillRect(x0, y0, X * s, Z * s);
    ctx.strokeStyle = "rgba(90,60,30,.18)"; ctx.lineWidth = 1;
    for (let z = 1; z < Z; z++) { ctx.beginPath(); ctx.moveTo(x0, v.sy(z)); ctx.lineTo(x0 + X * s, v.sy(z)); ctx.stroke(); }
    ctx.fillStyle = "rgba(60,40,20,.18)"; ctx.fillRect(x0, y0, 7 * s, 3.2 * s);                       // góc bếp
    ctx.strokeStyle = "#6b4a2b"; ctx.lineWidth = 6; ctx.strokeRect(x0, y0, X * s, Z * s);
    ctx.fillStyle = "#e9d3a8"; ctx.fillRect(v.sx(X / 2 - 1.2), v.sy(0) - 3, 2.4 * s, 6);           // lối vào
  }

  function drawStoves(v, snap) {
    const { s } = v, t = CN.now(), menu = snap.menu || {};
    (snap.stoves || []).forEach((st) => {
      const x = v.sx(st.pos[0]), y = v.sy(st.pos[1]);
      ctx.fillStyle = "#4a4a50"; CN.rrect(x - 1.1 * s, y - 0.8 * s, 2.2 * s, 1.6 * s, 6); ctx.fill();
      ctx.fillStyle = "#2b2b30"; ctx.beginPath(); ctx.arc(x, y, 0.55 * s, 0, Math.PI * 2); ctx.fill();     // nồi
      if (st.state === "cooking") {
        const total = ((menu[st.dish] || {}).cook_s || 0) * 60;
        if (total > 0 && st.cook_ticks_left !== undefined) ui.ring(x, y, 0.75 * s, 1 - st.cook_ticks_left / total, "#ffb347", 5);
        for (let i = 0; i < 3; i++) {                                                                     // hơi nước
          const a = (t * 0.8 + i / 3) % 1;
          ctx.fillStyle = `rgba(255,255,255,${(0.5 * (1 - a)).toFixed(2)})`;
          ctx.beginPath(); ctx.arc(x + Math.sin(t * 2 + i) * 0.2 * s, y - 0.6 * s - a * 1.2 * s, 0.18 * s, 0, Math.PI * 2); ctx.fill();
        }
        if (st.cook_ticks_left !== undefined) text(Math.ceil(st.cook_ticks_left / 60) + " s", x, y + 1.3 * s, { size: 18, align: "center", color: "#2a1a0a", weight: "700" });
      } else if (st.state === "ready") {
        ui.ring(x, y, 0.75 * s, 1, COLOR.ok, 5);
        const [bx, by] = ui.bubble(x, y - 0.9 * s, 86, 34);
        text("Chín!", bx, by + 1, { size: 18, align: "center", base: "middle", color: "#2f6b2f", weight: "800" });
      }
      if (st.dish && st.state !== "idle") ui.dish(st.dish, x, y, 0.8 * s);
    });
  }

  function drawTables(v, snap) {
    const { meta, s } = v;
    const patMax = (meta.patience_s || 60) * 60;
    const byTable = {};
    (snap.customers || []).forEach((c) => { if (c.table_id) byTable[c.table_id] = c; });
    (snap.tables || []).forEach((tb) => {
      const x = v.sx(tb.pos[0]), y = v.sy(tb.pos[1]);
      ctx.fillStyle = "#7a4b2a";
      for (const dx of [-1.2, 1.2]) { ctx.beginPath(); ctx.arc(x + dx * s, y, 0.3 * s, 0, Math.PI * 2); ctx.fill(); }  // ghế
      ctx.fillStyle = "#8a5a2e"; ctx.beginPath(); ctx.arc(x, y, 0.85 * s, 0, Math.PI * 2); ctx.fill();
      text(tb.id, x, y + 6, { size: 18, align: "center", color: "#f3e3c3", weight: "700" });
      const c = byTable[tb.id];
      if (!c) return;
      const cx = x - 1.2 * s, cy = y;
      ctx.fillStyle = c.state === "eating" ? "#7bc67b" : "#f4b6c2";
      ctx.beginPath(); ctx.arc(cx, cy, 0.42 * s, 0, Math.PI * 2); ctx.fill();
      const [bx, by] = ui.bubble(x, y - 1 * s, 64, 54);                                                   // bong bóng order
      if (c.state === "eating") {
        text("Đang ăn", bx, by + 1, { size: 18, align: "center", base: "middle", color: "#2f6b2f", weight: "700" });
        return;
      }
      ui.dish(dishOf(c), bx, by, 36);
      const left = patienceLeft(c);
      if (left !== undefined) { const f = left / patMax; ui.ring(bx, by, 24, f, f < 0.25 ? COLOR.danger : f < 0.5 ? COLOR.gold : COLOR.ok, 4); }
    });
  }

  function drawPlayer(v, snap) {
    const p = snap.player;
    if (!p || !p.pos) return null;
    const { s } = v, x = v.sx(p.pos[0]), y = v.sy(p.pos[1]);
    if (v.meta.interact_radius) {
      ctx.strokeStyle = "rgba(255,255,255,.45)"; ctx.lineWidth = 1; ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.arc(x, y, v.meta.interact_radius * s, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]);
    }
    ctx.fillStyle = COLOR.player; ctx.beginPath(); ctx.arc(x, y, 0.5 * s, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(x, y - 0.35 * s, 0.32 * s, Math.PI, 0); ctx.fill();   // mũ đầu bếp
    if (snap.hand) ui.dish(typeof snap.hand === "string" ? snap.hand : snap.hand.dish_id, x + 0.6 * s, y - 0.6 * s, 0.9 * s);
    return [x, y];
  }

  function drawHint(v, snap) {
    const p = snap.player, r = v.meta.interact_radius || 1.5;
    if (!p || !p.pos || snap.finished) return;
    const near = (e) => Math.hypot(e.pos[0] - p.pos[0], e.pos[1] - p.pos[1]);
    const byTable = {};
    (snap.customers || []).forEach((c) => { if (c.table_id) byTable[c.table_id] = c; });
    const cands = [];
    (snap.stoves || []).forEach((st) => {
      if (near(st) > r) return;
      // bếp sát tường trên: gợi ý vẽ BÊN DƯỚI bếp để không đè bong bóng "Chín!" và thanh HUD
      if (st.state === "ready" && !snap.hand) cands.push([near(st), 0, st, "Bưng", -1.9]);
      else if (st.state === "idle" && !snap.hand) cands.push([near(st), 0, st, "Nấu", -1.9]);
    });
    (snap.tables || []).forEach((tb) => {
      const c = byTable[tb.id];
      if (near(tb) <= r && c && c.state !== "eating" && snap.hand) cands.push([near(tb), 1, tb, "Dọn món", 2.4]);
    });
    cands.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    if (cands.length) { const [, , e, label, up] = cands[0]; ui.hint(v.sx(e.pos[0]), v.sy(e.pos[1]) - up * v.s, "E", label); }
  }

  CN.scenes.quan = {
    draw(w, h, snap) {
      const v = view(w, h, snap);
      CN.lastView = v;
      drawRoom(v);
      drawStoves(v, snap);
      drawTables(v, snap);
      const at = drawPlayer(v, snap);
      drawHint(v, snap);
      CN.fx.anchor = at ? { x: at[0], y: at[1] - v.s } : null;
    },
  };
})(window.CN);
