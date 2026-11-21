"use strict";
/*
 * Cảnh nền cho hai buổi chơi (trongnghia2304, Phase 4 — "Tự do sáng tạo": đồ họa). Vẽ hoàn toàn bằng code, không asset ngoài.
 * Bối cảnh theo PRD-0 mục 3: "Sông nước màu phù sa, bờ dừa nước, nhà sàn và ánh hồng buổi sớm. Tối có đèn dây vàng và khói bếp."
 *
 *   Buổi sáng (gather, mặt cắt ngang, CAMERA ZOOM theo Út Sen): trời hồng bình minh, bờ dừa nước + nhà sàn, nước phù sa nhiều tầng,
 *   tia nắng xiên, bụi phù sa, bong bóng, lục bình trôi, rễ dừa nước, đáy bùn có đá / gỗ chìm / rong. Thêm bản đồ nhỏ + thước độ sâu.
 *   Buổi tối (quan, ISOMETRIC 2.5D): nhà bè trên sông đêm — sàn gạch bông, khu bếp gạch nung + quầy, hai vách tre / gỗ có cửa sổ
 *   nhìn ra sông, dây đèn vàng, đèn lồng, chiếu và ghế đẩu quanh bàn, bàn tròn nhìn nghiêng, bong bóng gọi món, khói bếp.
 *
 * index.html (Tiệp giữ) gọi qua window.SCENE; thiếu file này thì index.html vẽ như cũ (nhìn thẳng, vừa khít):
 *   gatherBack / gatherFront / gatherHud(ctx, geo)   quanBack / quanFront(ctx, geo), isoTable, speechBubble, quanIso
 *   showIds (phím I: hiện nhãn F1/N1/M1 + log sự kiện)
 * Chỉ ĐỌC snapshot, không có luật. Phần tĩnh vẽ một lần vào canvas phụ (cache) để giữ FPS cho bench (AC-P4-02).
 */
(function () {
  const TAU = Math.PI * 2;
  const cache = new Map();
  const rnd = (i, k = 1) => { const x = Math.sin(i * 127.1 + k * 311.7) * 43758.5453; return x - Math.floor(x); };

  // canvas phụ vẽ một lần; độ phân giải tối đa 1.5× để canvas thế giới lớn không tốn bộ nhớ
  function layer(key, w, h, draw) {
    const dpr = Math.min(1.5, window.devicePixelRatio || 1);
    const k = key + "|" + Math.round(w) + "x" + Math.round(h) + "@" + dpr;
    let c = cache.get(k);
    if (!c) {
      if (cache.size > 6) cache.clear();
      c = document.createElement("canvas");
      c.width = Math.max(1, Math.round(w * dpr)); c.height = Math.max(1, Math.round(h * dpr));
      const g = c.getContext("2d");
      g.setTransform(dpr, 0, 0, dpr, 0, 0);
      draw(g);
      cache.set(k, c);
    }
    return c;
  }
  function roundRect(g, x, y, w, h, r) {
    g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r);
    g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath();
  }
  function hudPanel(g, x, y, w, h) {   // nền mờ sau chữ HUD để đọc được trên mọi cảnh
    g.fillStyle = "rgba(14,18,26,.66)"; roundRect(g, x, y, w, h, 10); g.fill();
    g.strokeStyle = "rgba(255,226,170,.2)"; g.lineWidth = 1.5; g.stroke();
  }
  function poly(g, pts, fill, stroke, lw) {
    g.beginPath(); g.moveTo(pts[0][0], pts[0][1]);
    for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]);
    g.closePath();
    if (fill) { g.fillStyle = fill; g.fill(); }
    if (stroke) { g.strokeStyle = stroke; g.lineWidth = lw || 1; g.stroke(); }
  }

  // ============================ BUỔI SÁNG — sông phù sa (toạ độ thế giới) ============================
  function palm(g, x, base, size, color) {
    g.strokeStyle = color; g.lineCap = "round";
    for (let i = 0; i < 7; i++) {
      const a = -Math.PI / 2 + (i - 3) * 0.32, len = size * (0.75 + rnd(i, x) * 0.35);
      g.lineWidth = Math.max(2, size * 0.09);
      g.beginPath(); g.moveTo(x, base);
      g.quadraticCurveTo(x + Math.cos(a) * len * 0.5, base + Math.sin(a) * len * 0.75 - size * 0.12,
                         x + Math.cos(a) * len, base + Math.sin(a) * len + size * 0.18);
      g.stroke();
    }
  }
  function stiltHouse(g, x, base, sz, color) {
    g.fillStyle = color; g.strokeStyle = color; g.lineWidth = Math.max(1.5, sz * 0.05);
    for (let i = 0; i < 4; i++) { g.beginPath(); g.moveTo(x + i * sz * 0.33, base); g.lineTo(x + i * sz * 0.33, base - sz * 0.45); g.stroke(); }
    g.fillRect(x - sz * 0.05, base - sz * 0.85, sz * 1.1, sz * 0.42);
    g.beginPath(); g.moveTo(x - sz * 0.2, base - sz * 0.82); g.lineTo(x + sz * 0.5, base - sz * 1.3); g.lineTo(x + sz * 1.2, base - sz * 0.82); g.fill();
  }
  function boat(g, x, base, sz, color) {
    g.fillStyle = color;
    g.beginPath(); g.moveTo(x - sz, base - sz * 0.08); g.quadraticCurveTo(x, base + sz * 0.28, x + sz, base - sz * 0.08);
    g.lineTo(x + sz * 0.8, base - sz * 0.18); g.lineTo(x - sz * 0.8, base - sz * 0.18); g.fill();
    g.beginPath(); g.arc(x + sz * 0.15, base - sz * 0.42, sz * 0.13, 0, TAU); g.fill();
    g.beginPath(); g.moveTo(x - sz * 0.05, base - sz * 0.46); g.lineTo(x + sz * 0.35, base - sz * 0.46); g.lineTo(x + sz * 0.15, base - sz * 0.62); g.fill();
  }

  function gatherWorld(geo) {
    const { s, X, D, SKY, WORLD } = geo;
    const WW = (WORLD.R - WORLD.L) * s, WH = (WORLD.B - WORLD.T) * s;
    const canvas = layer("gather|" + s.toFixed(3) + "|" + X + "|" + D + "|" + SKY, WW, WH, (g) => {
      const wx = (x) => (x - WORLD.L) * s, wy = (d) => (d - WORLD.T) * s;
      const surf = wy(0), skyTop = 0, bed = wy(D), L = wx(0), R = wx(X), skyH = surf - skyTop;
      // trời hồng bình minh + mặt trời
      const sky = g.createLinearGradient(0, skyTop, 0, surf);
      sky.addColorStop(0, "#f2b29f"); sky.addColorStop(0.55, "#ffd7b2"); sky.addColorStop(1, "#fff0cf");
      g.fillStyle = sky; g.fillRect(0, skyTop, WW, skyH);
      [[0.18, 0.22], [0.72, 0.35]].forEach(([fx, fy], i) => {
        const cx = L + (R - L) * fx, cy = surf - skyH * fy;
        const sun = g.createRadialGradient(cx, cy, 2, cx, cy, skyH * (i ? 1.1 : 0.7));
        sun.addColorStop(0, "rgba(255,250,220," + (i ? 0.95 : 0.45) + ")"); sun.addColorStop(1, "rgba(255,200,150,0)");
        g.fillStyle = sun; g.fillRect(cx - skyH * 1.2, skyTop, skyH * 2.4, skyH);
      });
      g.fillStyle = "#fff6dc"; g.beginPath(); g.arc(L + (R - L) * 0.72, surf - skyH * 0.35, skyH * 0.12, 0, TAU); g.fill();
      // mây hồng
      g.fillStyle = "rgba(255,236,225,.55)";
      for (let i = 0; i < 14; i++) {
        const cx = rnd(i, 81) * WW, cy = skyTop + skyH * (0.12 + rnd(i, 82) * 0.35), r = s * (0.8 + rnd(i, 83) * 1.4);
        for (let k = 0; k < 4; k++) { g.beginPath(); g.ellipse(cx + k * r * 0.9, cy + (k % 2) * r * 0.2, r, r * 0.45, 0, 0, TAU); g.fill(); }
      }
      // bờ xa: dừa nước, nhà sàn, xuồng
      const hz = surf - 1;
      g.fillStyle = "#c79a9e"; g.fillRect(0, hz - skyH * 0.12, WW, skyH * 0.12);
      for (let x = 0, i = 0; x < WW; x += s * 2.2, i++) palm(g, x + rnd(i) * s, hz, skyH * (0.35 + rnd(i, 2) * 0.25), "#a77e88");
      for (let i = 0; i < Math.ceil(X / 22); i++) stiltHouse(g, L + (i * 22 + 6 + rnd(i, 5) * 6) * s, hz, skyH * (0.45 + rnd(i, 6) * 0.15), "#8d6a78");
      for (let x = 0, i = 0; x < WW; x += s * 4, i++) palm(g, x + rnd(i, 7) * s * 2, hz + 2, skyH * (0.45 + rnd(i, 3) * 0.3), "#7a5b6c");
      for (let i = 0; i < Math.ceil(X / 30); i++) boat(g, L + (i * 30 + 15) * s, hz, skyH * 0.3, "#5d4558");
      // nước phù sa: xanh lục đục -> nâu xanh -> tối
      const water = g.createLinearGradient(0, surf, 0, bed + s * 2);
      water.addColorStop(0, "#7fb7a4"); water.addColorStop(0.18, "#5f9c8e"); water.addColorStop(0.5, "#3d7178");
      water.addColorStop(0.8, "#24485a"); water.addColorStop(1, "#142838");
      g.fillStyle = water; g.fillRect(0, surf, WW, bed - surf + s * 2);
      for (let i = 1; i <= 5; i++) { g.fillStyle = "rgba(10,30,40," + (0.025 * i).toFixed(3) + ")"; g.fillRect(0, surf + ((bed - surf) * i) / 6, WW, (bed - surf) / 6); }
      // bờ đất ngầm xa (lớp sau)
      g.fillStyle = "rgba(30,60,64,.45)";
      g.beginPath(); g.moveTo(0, bed);
      for (let x = 0; x <= WW; x += 20) g.lineTo(x, bed - s * (5 + 3 * Math.sin(x / (s * 4)) + 2 * Math.sin(x / (s * 1.6) + 1)));
      g.lineTo(WW, bed); g.fill();
      // rễ dừa nước rủ từ hai bờ
      g.strokeStyle = "rgba(30,48,40,.4)"; g.lineCap = "round";
      [[L - s * 2.2, 1], [R + s * 2.2, -1]].forEach(([bx, dir], side) => {
        for (let i = 0; i < 7; i++) {
          const y0 = surf + rnd(i, side + 4) * s * 2, len = s * (4 + rnd(i, side + 9) * 7);
          g.lineWidth = Math.max(1, s * (0.05 + rnd(i, 2) * 0.06));
          g.beginPath(); g.moveTo(bx, y0);
          g.bezierCurveTo(bx + dir * s * (1 + i * 0.5), y0 + len * 0.3, bx + dir * s * (0.2 + i * 0.4), y0 + len * 0.7, bx + dir * s * (1.5 + rnd(i, 5) * 2), y0 + len);
          g.stroke();
        }
      });
      // đáy bùn, đá, gỗ chìm
      g.fillStyle = "#3a3024";
      g.beginPath(); g.moveTo(0, WH);
      for (let x = 0; x <= WW; x += 10) g.lineTo(x, bed - s * (0.6 + 0.5 * Math.sin(x / (s * 2.3)) + 0.3 * Math.sin(x / (s * 0.8) + 2)));
      g.lineTo(WW, WH); g.fill();
      const deep = bed + s * 3.5;
      const mud = g.createLinearGradient(0, bed - s, 0, deep);
      mud.addColorStop(0, "rgba(90,70,48,.55)"); mud.addColorStop(0.35, "rgba(46,38,30,.9)"); mud.addColorStop(1, "#10161c");
      g.fillStyle = mud; g.fillRect(0, bed - s, WW, deep - bed + s);
      g.fillStyle = "#10161c"; g.fillRect(0, deep, WW, WH - deep);
      for (let i = 0; i < Math.ceil(X * 0.6); i++) {
        const rx = L + rnd(i, 11) * (R - L), rs = s * (0.4 + rnd(i, 12) * 0.9);
        g.fillStyle = i % 3 ? "#4a4136" : "#5a5044";
        g.beginPath(); g.ellipse(rx, bed - rs * 0.35, rs, rs * 0.55, 0, 0, TAU); g.fill();
        g.fillStyle = "rgba(255,255,255,.08)"; g.beginPath(); g.ellipse(rx - rs * 0.3, bed - rs * 0.6, rs * 0.4, rs * 0.18, 0, 0, TAU); g.fill();
      }
      for (let i = 0; i < 3; i++) {
        g.save(); g.translate(L + (R - L) * (0.2 + i * 0.3), bed - s * 0.7); g.rotate((i % 2 ? 0.1 : -0.12));
        g.fillStyle = "#4d3826"; roundRect(g, -s * 4, -s * 0.45, s * 8, s * 0.9, s * 0.45); g.fill();
        g.strokeStyle = "rgba(0,0,0,.25)"; g.lineWidth = 1;
        for (let k = -3; k <= 3; k++) { g.beginPath(); g.moveTo(k * s, -s * 0.3); g.lineTo(k * s + s * 0.6, s * 0.3); g.stroke(); }
        g.restore();
      }
    });
    return { canvas, WW, WH };
  }

  const LUC_BINH = [0.05, 0.17, 0.3, 0.42, 0.55, 0.68, 0.8, 0.93];
  function lucBinh(g, x, y, s, k) {
    g.strokeStyle = "rgba(40,50,40,.55)"; g.lineWidth = 1.2;
    for (let i = 0; i < 6; i++) {
      g.beginPath(); g.moveTo(x + (i - 2.5) * s * 0.25, y + s * 0.1);
      g.quadraticCurveTo(x + (i - 2.5) * s * 0.3, y + s * 0.8, x + (i - 2.5) * s * 0.2 + Math.sin(k + i) * s * 0.2, y + s * 1.4); g.stroke();
    }
    for (let i = 0; i < 5; i++) {
      g.fillStyle = i % 2 ? "#4f8f3a" : "#62a548";
      g.beginPath(); g.ellipse(x + (i - 2) * s * 0.32, y - s * 0.12 - (i % 2) * s * 0.12, s * 0.34, s * 0.22, (i - 2) * 0.35, 0, TAU); g.fill();
    }
    g.fillStyle = "#b48ad8"; g.beginPath(); g.arc(x + s * 0.05, y - s * 0.55, s * 0.17, 0, TAU); g.fill();
    g.fillStyle = "#d9c2f2"; g.beginPath(); g.arc(x + s * 0.05, y - s * 0.58, s * 0.07, 0, TAU); g.fill();
  }
  const visible = (x, w, m) => x > -m && x < w + m;

  function gatherBack(g, geo) {
    const { now, sx, sy, X, D, s, w, WORLD } = geo;
    const wd = gatherWorld(geo);
    g.drawImage(wd.canvas, sx(WORLD.L), sy(WORLD.T), wd.WW, wd.WH);
    const surf = sy(0), bed = sy(D);
    // tia nắng xiên (rải khắp sông, chỉ vẽ tia trong khung nhìn)
    g.save(); g.globalCompositeOperation = "lighter";
    for (let i = 0; i < Math.ceil(X / 5.5); i++) {
      const xm = i * 5.5 + rnd(i, 20) * 3, x0 = sx(xm) + Math.sin(now / 2600 + i * 1.7) * s * 1.2;
      const wTop = s * (1.2 + rnd(i, 21) * 1.6), len = (bed - surf) * (0.5 + rnd(i, 22) * 0.35);
      if (!visible(x0, w, len)) continue;
      const gr = g.createLinearGradient(0, surf, 0, surf + len);
      gr.addColorStop(0, "rgba(255,240,200,.17)"); gr.addColorStop(1, "rgba(255,240,200,0)");
      g.fillStyle = gr;
      g.beginPath(); g.moveTo(x0, surf); g.lineTo(x0 + wTop, surf); g.lineTo(x0 + wTop * 2.6 + len * 0.25, surf + len); g.lineTo(x0 + len * 0.25, surf + len); g.fill();
    }
    g.restore();
    // rong lay theo nước
    g.lineCap = "round";
    for (let i = 0; i < Math.ceil(X * 1.1); i++) {
      const gx = sx(rnd(i, 31) * X);
      if (!visible(gx, w, s * 3)) continue;
      const hgt = s * (1.4 + rnd(i, 32) * 2.6), sway = Math.sin(now / 900 + i) * s * 0.45;
      g.strokeStyle = i % 3 ? "#3f6e3a" : "#5b8b48"; g.lineWidth = Math.max(1.5, s * 0.14);
      for (let k = -1; k <= 1; k++) {
        g.beginPath(); g.moveTo(gx + k * s * 0.18, bed - s * 0.2);
        g.quadraticCurveTo(gx + k * s * 0.3 + sway * 0.5, bed - hgt * 0.55, gx + k * s * 0.2 + sway, bed - hgt * (0.8 + 0.2 * Math.abs(k)));
        g.stroke();
      }
    }
    // gợn sáng mặt nước
    g.strokeStyle = "rgba(255,250,230,.75)"; g.lineWidth = 2;
    g.beginPath(); g.moveTo(0, surf);
    for (let x = 0; x <= w; x += 8) g.lineTo(x, surf + Math.sin((x - sx(0)) / 26 + now / 420) * 1.6);
    g.stroke();
    // lục bình trôi chậm
    LUC_BINH.forEach((b, i) => {
      const lx = sx(((b + now / 300000 * (1 + (i % 3) * 0.3)) % 1) * X);
      if (visible(lx, w, s * 2)) lucBinh(g, lx, surf + Math.sin(now / 700 + i) * 1.2, s * 1.0, now / 900 + i);
    });
    return true;
  }

  function gatherFront(g, geo) {
    const { now, sx, sy, X, D, s, w, top, viewH } = geo;
    const surf = sy(0), bed = sy(D), HH = bed - surf;
    // bụi phù sa (rải theo thế giới, vẽ phần trong khung)
    for (let i = 0; i < Math.ceil(X * 2.4); i++) {
      const xm = (rnd(i, 41) * X + now * (0.0002 + rnd(i, 42) * 0.0005)) % X;
      const px = sx(xm);
      if (!visible(px, w, 4)) continue;
      const py = surf + ((rnd(i, 43) * HH + Math.sin(now / 1800 + i) * s * 0.6 + HH) % HH);
      g.fillStyle = "rgba(235,225,190," + (0.12 + rnd(i, 44) * 0.25).toFixed(2) + ")";
      g.fillRect(px, py, 2, 2);
    }
    // bong bóng nổi lên từ đáy
    g.strokeStyle = "rgba(230,250,255,.55)"; g.lineWidth = 1.2;
    for (let i = 0; i < Math.ceil(X * 0.35); i++) {
      const period = 6000 + rnd(i, 51) * 5000, t = ((now + rnd(i, 52) * period) % period) / period;
      const bx = sx(rnd(i, 53) * X) + Math.sin(t * 9 + i) * s * 0.3, by = bed - t * HH;
      if (!visible(bx, w, 10)) continue;
      g.beginPath(); g.arc(bx, by, s * (0.1 + rnd(i, 54) * 0.12), 0, TAU); g.stroke();
    }
    // cây tối tiền cảnh dọc đáy (lớp gần nhất)
    g.fillStyle = "rgba(12,22,18,.88)";
    for (let i = 0; i < Math.ceil(X / 9); i++) {
      const bx = sx(i * 9 + 3 + rnd(i, 61) * 4);
      if (!visible(bx, w, s * 4)) continue;
      for (let k = 0; k < 4; k++) {
        const kx = bx + k * s * 0.55, hgt = s * (2.5 + rnd(i * 4 + k, 62) * 2.5), sw = Math.sin(now / 1100 + i + k) * s * 0.35;
        g.beginPath(); g.moveTo(kx - s * 0.2, bed + s);
        g.quadraticCurveTo(kx + sw + s * 0.4, bed - hgt * 0.6, kx + sw, bed - hgt);
        g.quadraticCurveTo(kx + s * 0.1, bed - hgt * 0.4, kx + s * 0.35, bed + s); g.fill();
      }
    }
    // tối dần ở rìa khung nhìn
    const cxv = w / 2, cyv = top + viewH / 2;
    const vg = g.createRadialGradient(cxv, cyv, Math.min(w, viewH) * 0.35, cxv, cyv, Math.max(w, viewH) * 0.72);
    vg.addColorStop(0, "rgba(8,16,24,0)"); vg.addColorStop(1, "rgba(8,16,24,.45)");
    g.fillStyle = vg; g.fillRect(0, Math.max(top, surf), w, viewH);
    return true;
  }

  // bản đồ nhỏ + thước độ sâu + nền HUD (vẽ ngoài vùng cắt, trước chữ HUD)
  function gatherHud(g, geo) {
    const { w, h, top, viewH, sx, sy, X, D, SKY, s, snap } = geo;
    hudPanel(g, 6, 4, Math.min(470, w - 12), 56);
    // thước độ sâu bên trái khung nhìn
    g.font = "11px system-ui, sans-serif"; g.textAlign = "left";
    for (let d = 5; d <= D; d += 5) {
      const y = sy(d);
      if (y < top + 8 || y > top + viewH - 8) continue;
      g.fillStyle = "rgba(10,20,26,.55)"; g.fillRect(4, y - 8, 36, 15);
      g.fillStyle = "rgba(230,245,240,.85)"; g.fillRect(4, y - 1, 6, 2); g.fillText(d + " m", 12, y + 4);
    }
    // bản đồ nhỏ góc phải dưới
    const mw = Math.min(200, w * 0.28), mh = mw * (D + SKY) / (X + 6), mx = w - mw - 10, my = top + viewH - mh - 10;
    const k = mw / (X + 6), mX = (x) => mx + (x + 3) * k, mY = (d) => my + (d + SKY) * k;
    g.fillStyle = "rgba(14,18,26,.72)"; roundRect(g, mx - 4, my - 4, mw + 8, mh + 8, 6); g.fill();
    g.fillStyle = "#f3cdb4"; g.fillRect(mx, my, mw, SKY * k);
    g.fillStyle = "#3d7178"; g.fillRect(mx, mY(0), mw, D * k);
    g.fillStyle = "#3a3024"; g.fillRect(mx, mY(D), mw, mh - (D + SKY) * k);
    const dot = (x, d, r, c) => { g.fillStyle = c; g.beginPath(); g.arc(mX(x), mY(d), r, 0, TAU); g.fill(); };
    const meta = snap.meta || {}, dp = meta.dock_pos || [2, 0];
    g.fillStyle = "#b9503a"; g.fillRect(mX(dp[0]) - 3, mY(0) - 6, 6, 6);
    (snap.nodes || []).forEach((n) => dot(n.pos[0], n.pos[1], 2.2, n.ready === false ? "#6a7a6a" : "#9be070"));
    (snap.fish || []).forEach((f) => dot(f.pos[0], f.pos[1], 1.6, "#e8f4ff"));
    (snap.monsters || []).forEach((m) => dot(m.pos[0], m.pos[1], 3, m.state === "chase" ? "#ff5252" : "#c58bff"));
    const p = snap.player;
    if (p && p.pos) dot(p.pos[0], p.pos[1], 3.2, "#ffd54f");
    // khung camera
    const vx0 = (0 - sx(0)) / s, vx1 = (w - sx(0)) / s, vy0 = (top - sy(0)) / s, vy1 = (top + viewH - sy(0)) / s;
    g.strokeStyle = "rgba(255,255,255,.8)"; g.lineWidth = 1;
    g.strokeRect(mX(Math.max(-3, vx0)), mY(Math.max(-SKY, vy0)), (Math.min(X + 3, vx1) - Math.max(-3, vx0)) * k, (Math.min(D + 4, vy1) - Math.max(-SKY, vy0)) * k);
    return true;
  }

  // ============================ BUỔI TỐI — nhà bè isometric ============================
  function quanStatic(geo, tables, stoves) {
    const { w, h, X, Z, P, kx, ky, wallPx } = geo;
    const key = "quan|" + kx.toFixed(3) + "|" + P(0, Z).map(Math.round).join(",") + "|" + JSON.stringify(tables) + JSON.stringify(stoves);
    return layer(key, w, h, (g) => {
      const up = wallPx / 3.2;                // px mỗi mét theo chiều cao
      const raise = (p, m) => [p[0], p[1] - m * up];
      const B = P(0, Z), Rr = P(X, Z), F = P(X, 0), Lf = P(0, 0);   // góc sau / phải / trước / trái
      // sông đêm
      const river = g.createLinearGradient(0, 0, 0, h);
      river.addColorStop(0, "#0d2430"); river.addColorStop(1, "#071219");
      g.fillStyle = river; g.fillRect(0, 0, w, h);
      g.strokeStyle = "rgba(120,170,180,.12)"; g.lineWidth = 2;
      for (let i = 0; i < 70; i++) {
        const x = rnd(i, 61) * w, y = rnd(i, 62) * h, l = 20 + rnd(i, 63) * 50;
        g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + l / 2, y - 3, x + l, y); g.stroke();
      }
      // lá sen / lục bình nổi quanh bè (toạ độ thế giới ngoài sàn)
      for (let i = 0; i < 16; i++) {
        const side = i % 2, t = rnd(i, 65) * (side ? X : Z);
        const pt = side ? P(t, -1.2 - rnd(i, 66) * 1.5) : P(X + 1.2 + rnd(i, 66) * 1.5, t);
        g.fillStyle = i % 3 ? "#2f5a35" : "#3b6e3f";
        g.beginPath(); g.ellipse(pt[0], pt[1], kx * 0.6, ky * 0.6, 0, 0.3, TAU - 0.2); g.lineTo(pt[0], pt[1]); g.fill();
        if (i % 4 === 0) { g.fillStyle = "#e8a7c3"; g.beginPath(); g.arc(pt[0] + kx * 0.2, pt[1] - ky * 0.2, kx * 0.16, 0, TAU); g.fill(); }
      }
      // phản chiếu ánh đèn trên nước trước bè
      g.fillStyle = "rgba(255,190,110,.10)";
      for (let i = 0; i < 6; i++) g.fillRect(F[0] - kx * (4 - i), F[1] + ky * (1.5 + i * 0.6), kx * (8 - i * 1.2), 3);
      // thân bè (hai mặt bên phía trước) + sàn
      const th = up * 0.45;
      poly(g, [Lf, F, [F[0], F[1] + th], [Lf[0], Lf[1] + th]], "#3b2618");
      poly(g, [F, Rr, [Rr[0], Rr[1] + th], [F[0], F[1] + th]], "#2c1c11");
      g.fillStyle = "rgba(0,0,0,.35)";
      g.beginPath(); g.ellipse(F[0], F[1] + th + ky * 0.6, kx * (X + Z) * 0.4, ky * 1.2, 0, 0, TAU); g.fill();
      // sàn: gạch bông ở phòng ăn, gạch nung ở khu bếp
      const kz = Math.min(...stoves.map((st) => st.pos[1])) - 1.2, kEnd = Math.min(X, Math.max(...stoves.map((st) => st.pos[0])) + 2.5);
      for (let x = 0; x < X; x++) {
        for (let z = 0; z < Z; z++) {
          const c = [P(x, z), P(x + 1, z), P(x + 1, z + 1), P(x, z + 1)];
          if (z + 0.5 >= kz && x + 0.5 <= kEnd) {
            poly(g, c, (x + z) % 2 ? "#b4613f" : "#c06d48", "rgba(60,28,16,.45)", 1);
          } else {
            poly(g, c, "#efe2c4", "rgba(90,70,40,.35)", 1);
            const cx = (c[0][0] + c[2][0]) / 2, cy = (c[0][1] + c[2][1]) / 2;
            const inner = c.map((q) => [cx + (q[0] - cx) * 0.62, cy + (q[1] - cy) * 0.62]);
            poly(g, inner, (x + z) % 2 ? "#2f6f7a" : "#3b7f6a");
            const core = c.map((q) => [cx + (q[0] - cx) * 0.3, cy + (q[1] - cy) * 0.3]);
            poly(g, core, "#efe2c4");
            g.fillStyle = "#c2453a"; g.beginPath(); g.arc(cx, cy, Math.max(1.5, kx * 0.07), 0, TAU); g.fill();
            [0, 1, 2, 3].forEach((j) => { g.fillStyle = "#c2453a"; g.beginPath(); g.arc(c[j][0] + (cx - c[j][0]) * 0.12, c[j][1] + (cy - c[j][1]) * 0.12, Math.max(1, kx * 0.05), 0, TAU); g.fill(); });
          }
        }
      }
      // chiếu + ghế đẩu quanh mỗi bàn
      tables.forEach((tb) => {
        const [x, z] = tb.pos;
        poly(g, [P(x - 1.2, z - 1.2), P(x + 1.2, z - 1.2), P(x + 1.2, z + 1.2), P(x - 1.2, z + 1.2)], "#c9a15b", "#7a4e22", 2);
        for (let k = -1; k <= 1; k++) {
          const a = P(x - 1.2, z + k * 0.7), b2 = P(x + 1.2, z + k * 0.7);
          g.strokeStyle = k ? "#b23a33" : "#2f7a5a"; g.lineWidth = Math.max(2, ky * 0.18);
          g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b2[0], b2[1]); g.stroke();
        }
        [[-1.05, 0.2], [1.05, -0.2], [0.2, 1.05]].forEach(([dx, dz]) => {
          const p0 = P(x + dx, z + dz);
          g.fillStyle = "#5a3620"; g.fillRect(p0[0] - kx * 0.08, p0[1] - up * 0.45, kx * 0.16, up * 0.45);
          g.fillStyle = "#8a5a34"; g.beginPath(); g.ellipse(p0[0], p0[1] - up * 0.45, kx * 0.32, ky * 0.32, 0, 0, TAU); g.fill();
          g.fillStyle = "#a8774a"; g.beginPath(); g.ellipse(p0[0], p0[1] - up * 0.47, kx * 0.25, ky * 0.25, 0, 0, TAU); g.fill();
        });
      });
      // hai vách: gỗ dưới, tre trên, cửa sổ nhìn ra sông đêm
      const wall = (a, b2, darker) => {
        const H = 3.2, lerp = (t, m) => [a[0] + (b2[0] - a[0]) * t, a[1] + (b2[1] - a[1]) * t - m * up];
        poly(g, [a, b2, raise(b2, H), raise(a, H)], darker ? "#c69a62" : "#d9ae72");
        poly(g, [a, b2, raise(b2, 1.0), raise(a, 1.0)], darker ? "#5b3620" : "#6b4026");
        g.strokeStyle = "rgba(90,60,30,.35)"; g.lineWidth = 1;
        for (let t = 0.02; t < 1; t += 0.035) { const p0 = lerp(t, 1.0), p1 = lerp(t, H); g.beginPath(); g.moveTo(p0[0], p0[1]); g.lineTo(p1[0], p1[1]); g.stroke(); }
        const len = Math.hypot(b2[0] - a[0], b2[1] - a[1]) / kx;
        const n = Math.max(2, Math.floor(len / 5));
        for (let i = 0; i < n; i++) {
          const t0 = (i + 0.3) / n, t1 = (i + 0.7) / n;
          const win = [lerp(t0, 1.35), lerp(t1, 1.35), lerp(t1, 2.65), lerp(t0, 2.65)];
          poly(g, win, "#122a3a", "#4a2a16", 3);
          const mid = lerp((t0 + t1) / 2, 2.2);
          g.fillStyle = "rgba(255,244,210,.85)"; g.beginPath(); g.arc(mid[0] + kx * 0.25, mid[1] - up * 0.1, kx * 0.14, 0, TAU); g.fill();
          const wl = [lerp(t0, 1.35), lerp(t1, 1.35), lerp(t1, 1.7), lerp(t0, 1.7)];
          poly(g, wl, "#1d4656");
          const m0 = lerp((t0 + t1) / 2, 1.35), m1 = lerp((t0 + t1) / 2, 2.65);
          g.strokeStyle = "#4a2a16"; g.lineWidth = 2; g.beginPath(); g.moveTo(m0[0], m0[1]); g.lineTo(m1[0], m1[1]); g.stroke();
        }
        poly(g, [raise(a, H), raise(b2, H), raise(b2, H + 0.15), raise(a, H + 0.15)], "#3b2618");
      };
      wall(Lf, B, true);
      wall(B, Rr, false);
      // quầy bếp dọc vách sau, chỉ trong khu bếp (vẽ sau vách để không bị che)
      const c0 = P(0, Z - 0.8), c1 = P(kEnd, Z - 0.8), hC = 1.0;
      poly(g, [c0, c1, raise(c1, hC), raise(c0, hC)], "#6b4026");
      poly(g, [c1, P(kEnd, Z), raise(P(kEnd, Z), hC), raise(c1, hC)], "#4f2f1b");
      poly(g, [raise(c0, hC), raise(c1, hC), raise(P(kEnd, Z), hC), raise(B, hC)], "#a7744a", "#4a2a16", 1);
      for (let i = 1; i < kEnd; i += 2) { const a = P(i, Z - 0.8); g.strokeStyle = "rgba(0,0,0,.25)"; g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(a[0], a[1] - hC * up); g.stroke(); }
      // nồi, rổ rau trên quầy
      for (let i = 0; i < Math.floor(kEnd / 2.6); i++) {
        const q = raise(P(1.5 + i * 2.6, Z - 0.4), hC);
        g.fillStyle = i % 2 ? "#3a3f44" : "#7a5230"; g.beginPath(); g.ellipse(q[0], q[1] - up * 0.12, kx * 0.32, ky * 0.32, 0, 0, TAU); g.fill();
        g.fillStyle = i % 2 ? "#59626a" : "#8fbf5a"; g.beginPath(); g.ellipse(q[0], q[1] - up * 0.2, kx * 0.26, ky * 0.22, 0, 0, TAU); g.fill();
      }
      // đèn lồng treo ở góc sau
      const lq = raise(B, 2.9);
      g.strokeStyle = "#2a1a10"; g.beginPath(); g.moveTo(lq[0], lq[1] - up * 0.25); g.lineTo(lq[0], lq[1]); g.stroke();
      g.fillStyle = "#c8402f"; g.beginPath(); g.ellipse(lq[0], lq[1] + up * 0.2, kx * 0.22, up * 0.25, 0, 0, TAU); g.fill();
      // chậu bông giấy ở góc trái và phải
      [P(0.6, 0.6), P(X - 0.6, Z - 1.6)].forEach((pt) => {
        g.fillStyle = "#7a3b22"; g.beginPath(); g.ellipse(pt[0], pt[1] - up * 0.2, kx * 0.32, ky * 0.32, 0, 0, TAU); g.fill();
        g.fillRect(pt[0] - kx * 0.3, pt[1] - up * 0.2, kx * 0.6, up * 0.2);
        for (let k = 0; k < 10; k++) {
          g.fillStyle = k % 3 ? "#3f7a3a" : "#d64f8f";
          g.beginPath(); g.arc(pt[0] + Math.cos(k) * kx * 0.3 * rnd(k, 71), pt[1] - up * (0.5 + rnd(k, 72) * 0.5), kx * (0.14 + rnd(k, 73) * 0.08), 0, TAU); g.fill();
        }
      });
      // nền HUD quán vẽ mỗi khung trong index.html (SCENE.hudPanel) vì cao theo số dòng kho
    });
  }

  function lightString(g, a, b2, up, now, kx) {   // dây đèn võng giữa hai điểm (đã nâng sẵn)
    const n = 12, pts = [];
    for (let i = 0; i <= n; i++) { const t = i / n; pts.push([a[0] + (b2[0] - a[0]) * t, a[1] + (b2[1] - a[1]) * t + Math.sin(t * Math.PI) * up * 0.35]); }
    g.strokeStyle = "rgba(20,14,10,.9)"; g.lineWidth = 1.5;
    g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); pts.forEach((p) => g.lineTo(p[0], p[1])); g.stroke();
    pts.forEach((p, i) => {
      if (!i || i === n) return;
      const on = 0.75 + 0.25 * Math.sin(now / 300 + i * 1.9);
      const r = kx * 0.5;
      const gl = g.createRadialGradient(p[0], p[1], 0, p[0], p[1], r);
      gl.addColorStop(0, "rgba(255,214,120," + (0.55 * on).toFixed(2) + ")"); gl.addColorStop(1, "rgba(255,190,90,0)");
      g.fillStyle = gl; g.fillRect(p[0] - r, p[1] - r, r * 2, r * 2);
      g.fillStyle = i % 3 === 0 ? "#ffe9a8" : i % 3 === 1 ? "#ffcf6e" : "#ffb35c";
      g.beginPath(); g.arc(p[0], p[1] + 2, Math.max(2.2, kx * 0.09), 0, TAU); g.fill();
    });
  }

  function quanBack(g, geo) {
    const snap = geo.snap || {};
    const tables = (snap.tables || []).map((t) => ({ id: t.id, pos: t.pos }));
    const stoves = (snap.stoves || []).map((t) => ({ id: t.id, pos: t.pos }));
    if (!stoves.length) stoves.push({ id: "_", pos: [0, geo.Z - 2] });
    g.drawImage(quanStatic(geo, tables, stoves), 0, 0, geo.w, geo.h);
    // gợn sóng phản chiếu đèn chuyển động trước bè
    const { now, P, X, kx, ky, w } = geo;
    const F = P(X, 0);
    g.strokeStyle = "rgba(255,200,120,.14)"; g.lineWidth = 2;
    for (let i = 0; i < 8; i++) {
      const y = F[1] + ky * (2 + i * 0.7), off = (now / 30 + i * 53) % 120;
      for (let x = -120 + off; x < w; x += 120) { g.beginPath(); g.moveTo(x, y); g.lineTo(x + 36, y); g.stroke(); }
    }
    return true;
  }

  function quanFront(g, geo) {
    const { now, P, X, Z, kx, ky, wallPx, w, h } = geo;
    const snap = geo.snap || {};
    const up = wallPx / 3.2, raise = (p, m) => [p[0], p[1] - m * up];
    // khói bếp
    (snap.stoves || []).forEach((st, si) => {
      if (st.state !== "cooking" && st.state !== "ready") return;
      const [cx, cy0] = P(st.pos[0], st.pos[1]), cy = cy0 - up * 1.4;
      for (let i = 0; i < 7; i++) {
        const t = ((now + i * (2400 / 7) + si * 400) % 2400) / 2400, r = kx * (0.25 + t * 0.6);
        g.fillStyle = "rgba(240,240,235," + (0.32 * (1 - t)).toFixed(3) + ")";
        g.beginPath(); g.arc(cx + Math.sin(t * 5 + i) * kx * 0.35, cy - t * up * 2.4, r, 0, TAU); g.fill();
      }
    });
    // dây đèn dọc mép trên hai vách
    lightString(g, raise(P(0, 0), 3.0), raise(P(0, Z), 3.0), up, now, kx);
    lightString(g, raise(P(0, Z), 3.0), raise(P(X, Z), 3.0), up, now + 700, kx);
    // ánh ấm giữa phòng, tối ở rìa
    const c = P(X / 2, Z / 2);
    const vg = g.createRadialGradient(c[0], c[1], kx * 3, c[0], c[1], Math.max(w, h) * 0.7);
    vg.addColorStop(0, "rgba(255,190,110,0.06)"); vg.addColorStop(1, "rgba(6,10,16,.5)");
    g.fillStyle = vg; g.fillRect(0, 96, w, h - 96);
    return true;
  }

  // bàn tròn nhìn nghiêng: chân + mặt bàn elip (chân bàn tại (px, py))
  function isoTable(g, px, py, s) {
    const top = py - s * 0.7, rx = s * 0.95, ry = s * 0.48;
    g.fillStyle = "rgba(0,0,0,.25)"; g.beginPath(); g.ellipse(px, py, rx * 0.8, ry * 0.8, 0, 0, TAU); g.fill();
    g.fillStyle = "#4a2c18"; g.fillRect(px - s * 0.09, top, s * 0.18, py - top);
    g.fillStyle = "#5a3620"; g.beginPath(); g.ellipse(px, top + s * 0.08, rx, ry, 0, 0, TAU); g.fill();
    g.fillStyle = "#9a6a3e"; g.beginPath(); g.ellipse(px, top, rx, ry, 0, 0, TAU); g.fill();
    g.strokeStyle = "rgba(255,230,190,.25)"; g.lineWidth = 2; g.beginPath(); g.ellipse(px, top, rx * 0.75, ry * 0.7, 0, Math.PI * 1.1, Math.PI * 1.7); g.stroke();
    return true;
  }
  // bong bóng thoại trắng có đuôi (món khách gọi)
  function speechBubble(g, x, y, r) {
    g.fillStyle = "rgba(0,0,0,.22)"; g.beginPath(); g.arc(x + 2, y + 3, r * 0.72, 0, TAU); g.fill();
    g.fillStyle = "#fffdf6"; g.strokeStyle = "#5a4632"; g.lineWidth = 2;
    g.beginPath(); g.arc(x, y, r * 0.72, 0, TAU); g.fill(); g.stroke();
    g.beginPath(); g.moveTo(x - r * 0.35, y + r * 0.55); g.lineTo(x - r * 0.75, y + r * 0.95); g.lineTo(x - r * 0.05, y + r * 0.68); g.closePath(); g.fill();
    g.strokeStyle = "#fffdf6"; g.beginPath(); g.moveTo(x - r * 0.34, y + r * 0.5); g.lineTo(x - r * 0.06, y + r * 0.62); g.stroke();
    return true;
  }

  const SCENE = { hudPanel, gatherBack, gatherFront, gatherHud, quanBack, quanFront, isoTable, speechBubble, quanIso: true, showIds: false };
  try { SCENE.showIds = localStorage.getItem("scene_ids") === "1"; } catch (e) { /* bỏ qua */ }
  addEventListener("keydown", (e) => {
    if (e.repeat || e.key.toLowerCase() !== "i") return;
    SCENE.showIds = !SCENE.showIds;
    try { localStorage.setItem("scene_ids", SCENE.showIds ? "1" : "0"); } catch (err) { /* bỏ qua */ }
  });
  window.SCENE = SCENE;
})();
