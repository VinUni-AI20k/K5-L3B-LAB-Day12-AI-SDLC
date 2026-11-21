"use strict";
/*
 * Cảnh buổi sáng (gather): mặt cắt sông nhìn ngang, camera bám theo Út Sen.
 * Chỉ vẽ. Gợi ý phím ("E Hái", "Space Bắt") chỉ để HIỂN THỊ theo snapshot; sim mới quyết định có tác dụng.
 */
(function (CN) {
  const { ctx, text, ui, COLOR } = CN;
  const SKY = 5;                       // khoảng trời phía trên mặt nước (đơn vị thế giới)
  CN.layout.gather = { top: 64, bottom: 76 };
  const bubbles = [];                  // bọt khí: thuần hình ảnh
  let lastBubble = 0;

  function view(w, h, snap) {
    const meta = snap.meta || {};
    const b = meta.bounds || { x: [0, 100], d: [0, 30] };
    const X0 = b.x[0], X = b.x[1], D = b.d[1];
    const { top, bottom } = CN.layout.gather;
    const s = Math.max(4, (h - top - bottom) / (D + SKY));
    const p = (snap.player && snap.player.pos) || [X0, 0];
    const camX = CN.camera.follow(p[0], w / s, X0 - 4, X + 4);
    const oy = top + SKY * s;
    return { meta, X0, X, D, s, camX, oy, top, w, h, sx: (x) => (x - camX) * s, sy: (d) => oy + d * s };
  }

  function drawSky(v) {
    const g = ctx.createLinearGradient(0, 0, 0, v.oy);
    g.addColorStop(0, "#f6d7a7"); g.addColorStop(1, "#cfe9f2");
    ctx.fillStyle = g; ctx.fillRect(0, 0, v.w, v.oy);
    // bờ xa: nhà sàn và ghe (parallax chậm hơn camera)
    const par = 0.45;
    for (let k = -2; k < 12; k++) {
      const wx = k * 13 + 4 - v.camX * par + v.camX;
      const x = v.sx(wx), base = v.oy;
      if (x < -6 * v.s || x > v.w + 6 * v.s) continue;
      ctx.fillStyle = "rgba(96,122,118,.55)";
      ctx.fillRect(x, base - 2.6 * v.s, 3.2 * v.s, 1.6 * v.s);
      ctx.beginPath(); ctx.moveTo(x - 0.4 * v.s, base - 2.6 * v.s); ctx.lineTo(x + 1.6 * v.s, base - 3.7 * v.s); ctx.lineTo(x + 3.6 * v.s, base - 2.6 * v.s); ctx.fill();
      ctx.fillRect(x + 0.3 * v.s, base - 1 * v.s, 0.15 * v.s, 1 * v.s);
      ctx.fillRect(x + 2.7 * v.s, base - 1 * v.s, 0.15 * v.s, 1 * v.s);
    }
  }

  function drawWater(v) {
    const { w, oy, s, D } = v;
    const bed = v.sy(D);
    const g = ctx.createLinearGradient(0, oy, 0, bed);
    g.addColorStop(0, "#5aa9b8"); g.addColorStop(0.35, "#2d7a96"); g.addColorStop(1, "#0b2a44");
    ctx.fillStyle = g; ctx.fillRect(0, oy, w, bed - oy);
    // tia nắng
    ctx.fillStyle = "rgba(255,255,255,.05)";
    for (let k = 0; k < 4; k++) {
      const x = ((k * 23 - v.camX * 0.3) * s) % (w + 200) - 100;
      ctx.beginPath(); ctx.moveTo(x, oy); ctx.lineTo(x + 3 * s, oy); ctx.lineTo(x + 9 * s, oy + 14 * s); ctx.lineTo(x + 5 * s, oy + 14 * s); ctx.fill();
    }
    // mặt nước gợn
    const t = CN.now();
    ctx.strokeStyle = "rgba(240,250,255,.85)"; ctx.lineWidth = 2; ctx.beginPath();
    for (let x = 0; x <= w; x += 8) {
      const y = oy + Math.sin((x + v.camX * s) * 0.04 + t * 2) * 1.5;
      if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
    // đáy sông + rong
    ctx.fillStyle = "#3a2a1a"; ctx.fillRect(0, bed, w, v.h - bed);
    ctx.strokeStyle = "#4f7a3a"; ctx.lineWidth = 3;
    const k0 = Math.floor(v.camX / 3) - 1, k1 = k0 + Math.ceil(w / s / 3) + 2;
    for (let k = k0; k <= k1; k++) {
      const wx = k * 3 + ((k * 7) % 5) * 0.4, x = v.sx(wx);
      const hgt = (1.2 + (Math.abs(k) % 3) * 0.7) * s, sway = Math.sin(t * 1.5 + k) * 0.4 * s;
      ctx.beginPath(); ctx.moveTo(x, bed); ctx.quadraticCurveTo(x + sway, bed - hgt / 2, x + sway * 1.6, bed - hgt); ctx.stroke();
    }
    // ngoài biên: tối lại
    ctx.fillStyle = "rgba(0,0,0,.35)";
    const l = v.sx(v.X0), r = v.sx(v.X);
    if (l > 0) ctx.fillRect(0, oy, l, bed - oy);
    if (r < w) ctx.fillRect(r, oy, w - r, bed - oy);
    // vùng độ sâu theo ticket: nông d < 10, giữa 10 ≤ d < 20, sâu d ≥ 20
    ctx.setLineDash([10, 8]); ctx.strokeStyle = "rgba(255,255,255,.18)"; ctx.lineWidth = 1;
    for (const d of [10, 20]) if (d < D) { ctx.beginPath(); ctx.moveTo(0, v.sy(d)); ctx.lineTo(w, v.sy(d)); ctx.stroke(); }
    ctx.setLineDash([]);
    [["Nông", 0, 10], ["Giữa", 10, 20], ["Sâu", 20, D]].forEach(([name, a, b]) => {
      if (a < D) text(name, 12, v.sy((a + Math.min(b, D)) / 2) + 6, { size: 18, color: "rgba(255,255,255,.35)", weight: "600" });
    });
  }

  // Cá Sấu Năm Chèo (và các loài quái của mở rộng): hướng mặt suy ra từ chuyển động giữa hai khung hình.
  const lastX = {}, facing = {};
  function drawMonsters(v, monsters) {
    const { s } = v, t = CN.now();
    (monsters || []).forEach((m) => {
      const x = v.sx(m.pos[0]), y = v.sy(m.pos[1]);
      if (lastX[m.id] !== undefined && Math.abs(m.pos[0] - lastX[m.id]) > 1e-4) facing[m.id] = m.pos[0] > lastX[m.id] ? 1 : -1;
      lastX[m.id] = m.pos[0];
      if (x < -4 * s || x > v.w + 4 * s) return;
      const chase = m.state === "chase", snake = m.kind === "ran";
      ctx.save(); ctx.translate(x, y); ctx.scale(facing[m.id] || 1, 1);
      ctx.globalAlpha = m.state === "recoil" ? 0.55 : 1;
      const sway = Math.sin(t * (chase ? 9 : 4)) * 0.25 * s;
      ctx.fillStyle = snake ? "#6b5a2a" : "#4f6b3a";
      ctx.beginPath(); ctx.moveTo(-1.3 * s, -0.2 * s); ctx.lineTo(-2.9 * s, sway); ctx.lineTo(-1.3 * s, 0.25 * s); ctx.fill();   // đuôi
      ctx.beginPath(); ctx.ellipse(0, 0, 1.5 * s, 0.42 * s, 0, 0, Math.PI * 2); ctx.fill();                                 // thân
      ctx.fillRect(1.1 * s, -0.22 * s, 1.4 * s, 0.36 * s);                                                                // mõm
      ctx.fillStyle = "rgba(0,0,0,.25)";
      for (let i = -1; i <= 1; i++) { ctx.beginPath(); ctx.arc(i * 0.5 * s, -0.38 * s, 0.13 * s, Math.PI, 0); ctx.fill(); } // gai lưng
      ctx.fillStyle = chase ? "#ff3b3b" : "#f2e14b";
      ctx.beginPath(); ctx.arc(1.05 * s, -0.3 * s, 0.13 * s, 0, Math.PI * 2); ctx.fill();                                  // mắt
      if (chase) { ctx.fillStyle = "#fff"; for (let i = 0; i < 4; i++) { const tx = 1.3 * s + i * 0.3 * s; ctx.beginPath(); ctx.moveTo(tx, 0.14 * s); ctx.lineTo(tx + 0.12 * s, 0.3 * s); ctx.lineTo(tx + 0.24 * s, 0.14 * s); ctx.fill(); } }
      ctx.restore();
      if (chase) text("!", x, y - 0.9 * s, { size: 24, align: "center", color: COLOR.danger, weight: "800" });
      if (m.state === "stunned") text("✦ ✦", x, y - 0.9 * s, { size: 18, align: "center", color: COLOR.gold });
    });
  }

  function drawDock(v) {
    const { meta, s } = v;
    const dp = meta.dock_pos || [2, 0], dr = meta.dock_radius || 3;
    const x = v.sx(dp[0]), y = v.sy(0);
    ctx.fillStyle = "#6b4a2b";                                      // cột cầu tàu
    for (const dx of [-1.6, 1.6]) ctx.fillRect(x + dx * s - 0.12 * s, y - 0.6 * s, 0.24 * s, 2.4 * s);
    ctx.fillStyle = "#8d6e4b"; ctx.fillRect(x - 2 * s, y - 0.8 * s, 4 * s, 0.3 * s);
    ctx.fillStyle = "#7a4b2a";                                      // ghe
    ctx.beginPath(); ctx.moveTo(x - 2.4 * s, y - 0.7 * s); ctx.lineTo(x + 2.4 * s, y - 0.7 * s); ctx.lineTo(x + 1.7 * s, y + 0.25 * s); ctx.lineTo(x - 1.7 * s, y + 0.25 * s); ctx.closePath(); ctx.fill();
    ctx.fillStyle = "#c98f4a"; ctx.beginPath(); ctx.arc(x, y - 0.75 * s, 1.1 * s, Math.PI, 0); ctx.fill();
    ctx.strokeStyle = "rgba(255,230,150,.6)"; ctx.lineWidth = 1; ctx.setLineDash([5, 4]);
    ctx.beginPath(); ctx.arc(x, v.sy(dp[1]), dr * s, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]);
  }

  function drawNodes(v, nodes) {
    const { s } = v;
    (nodes || []).forEach((n) => {
      const x = v.sx(n.pos[0]), y = v.sy(n.pos[1]);
      if (x < -3 * s || x > v.w + 3 * s) return;
      const ready = n.ready !== false;
      ctx.fillStyle = ready ? "#3f8f4a" : "rgba(63,143,74,.45)";        // lá súng
      ctx.beginPath(); ctx.ellipse(x, y, 1.1 * s, 0.32 * s, 0, 0.25, Math.PI * 2 - 0.25); ctx.lineTo(x, y); ctx.fill();
      if (ready) ui.icon(n.kind, x, y - 0.45 * s, 1.3 * s);
      else if (n.regrow_ticks) text(Math.ceil(n.regrow_ticks / 60) + "s", x, y - 0.6 * s, { size: 18, align: "center", color: "#23402a", weight: "700" });
    });
  }

  function drawFish(v, fish) {
    const { s } = v, t = CN.now();
    (fish || []).forEach((f, i) => {
      const x = v.sx(f.pos[0]), y = v.sy(f.pos[1]) + Math.sin(t * 2 + i) * 0.12 * s;  // nhấp nhô: chỉ hình ảnh
      if (x < -3 * s || x > v.w + 3 * s) return;
      ui.icon(f.kind, x, y, 2 * s, Math.cos(((f.heading_deg || 0) * Math.PI) / 180) < 0);
    });
  }

  function drawPlayer(v, snap) {
    const p = snap.player;
    if (!p || !p.pos) return null;
    const { s } = v, t = CN.now();
    const x = v.sx(p.pos[0]), y = v.sy(p.pos[1]);
    const under = p.at_surface === undefined ? p.pos[1] > (v.meta.surface_depth ?? 0.5) : !p.at_surface;
    if (under && t - lastBubble > 0.35) { bubbles.push({ x: p.pos[0], d: p.pos[1], born: t }); lastBubble = t; }
    for (let i = bubbles.length - 1; i >= 0; i--) {
      const b = bubbles[i], age = t - b.born, d = b.d - age * 2.2;
      if (d < 0 || age > 4) { bubbles.splice(i, 1); continue; }
      ctx.strokeStyle = "rgba(230,248,255,.7)"; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(v.sx(b.x + Math.sin(age * 3) * 0.2), v.sy(d), 0.18 * s, 0, Math.PI * 2); ctx.stroke();
    }
    if (p.invuln_ticks > 0 && Math.floor((snap.tick || 0) / 5) % 2) return [x, y];  // nhấp nháy khi vừa mất Máu
    const a = ((p.heading_deg || 0) * Math.PI) / 180;
    ctx.save(); ctx.translate(x, y);
    ctx.rotate(under ? a : 0);
    if (Math.cos(a) < 0 && !under) ctx.scale(-1, 1);
    ctx.fillStyle = "#2f5d7c"; ctx.beginPath(); ctx.ellipse(-0.25 * s, 0, 0.75 * s, 0.32 * s, 0, 0, Math.PI * 2); ctx.fill();   // thân
    ctx.fillStyle = "#f2c230"; ctx.fillRect(-0.7 * s, -0.48 * s, 0.6 * s, 0.22 * s);                                       // bình oxy
    ctx.fillStyle = "#f1c9a0"; ctx.beginPath(); ctx.arc(0.55 * s, 0, 0.32 * s, 0, Math.PI * 2); ctx.fill();               // đầu
    ctx.fillStyle = "#7fe0f5"; ctx.fillRect(0.6 * s, -0.16 * s, 0.24 * s, 0.18 * s);                                       // kính lặn
    ctx.restore();
    return [x, y];
  }

  function nearest(list, pos, r, ok) {
    let best = null, bd = r;
    (list || []).forEach((e) => {
      if (!ok(e)) return;
      const d = Math.hypot(e.pos[0] - pos[0], e.pos[1] - pos[1]);
      if (d <= bd) { bd = d; best = e; }
    });
    return best;
  }

  function drawHints(v, snap) {
    const p = snap.player;
    if (!p || !p.pos || snap.finished) return;
    const { meta, s } = v;
    const under = p.at_surface === undefined ? p.pos[1] > (meta.surface_depth ?? 0.5) : !p.at_surface;
    const dp = meta.dock_pos || [2, 0];
    if (Math.hypot(p.pos[0] - dp[0], p.pos[1] - dp[1]) <= (meta.dock_radius || 3)) {
      ui.hint(v.sx(dp[0]), v.sy(-1.6), "E", "Về ghe"); return;
    }
    if (!under) {
      const n = nearest(snap.nodes, p.pos, meta.interact_radius || 2, (n) => n.ready !== false);
      if (n) ui.hint(v.sx(n.pos[0]), v.sy(n.pos[1]) - 1.2 * s, "E", "Hái");
    } else if (!(p.catch_cd_ticks > 0)) {
      const f = nearest(snap.fish, p.pos, meta.catch_radius || 2, () => true);
      if (f) ui.hint(v.sx(f.pos[0]), v.sy(f.pos[1]) - 1.2 * s, "Space", "Bắt");
    }
  }

  CN.scenes.gather = {
    draw(w, h, snap) {
      const v = view(w, h, snap);
      CN.lastView = v;
      drawSky(v);
      drawWater(v);
      drawDock(v);
      drawNodes(v, snap.nodes);
      drawFish(v, snap.fish);
      drawMonsters(v, snap.monsters);
      const at = drawPlayer(v, snap);
      drawHints(v, snap);
      CN.fx.anchor = at ? { x: at[0], y: at[1] - 1.4 * v.s } : null;
      ctx.fillStyle = COLOR.bg; // trả màu mặc định cho HUD
    },
  };
})(window.CN);
