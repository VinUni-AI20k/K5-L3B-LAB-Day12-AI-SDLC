"use strict";
/*
 * Nét vẽ dùng chung (tự vẽ bằng canvas, không dùng ảnh ngoài): cá theo loài, bông/rau theo loài,
 * quầng sáng, khăn rằn. Chỉ là hình ảnh: KHÔNG dùng Math.random hay Streams của mô phỏng; mọi chi tiết
 * "ngẫu nhiên" (vị trí nhà sàn, hạt phù sa, màu áo khách) lấy từ hàm băm cố định CN.art.hash nên không
 * ảnh hưởng headless/JSONL.
 */
(function (CN) {
  const { ctx } = CN;
  const TAU = Math.PI * 2;

  // Băm số nguyên -> [0, 1). Cố định, không trạng thái.
  function hash(n) {
    n = Math.imul((n | 0) ^ 0x9e3779b9, 0x85ebca6b);
    n = Math.imul(n ^ (n >>> 13), 0xc2b2ae35);
    n ^= n >>> 16;
    return (n >>> 0) / 4294967296;
  }
  const strHash = (s) => { let h = 7; for (const ch of String(s)) h = Math.imul(h ^ ch.charCodeAt(0), 16777619); return hash(h); };

  // Quầng sáng vẽ sẵn một lần cho mỗi màu (drawImage rẻ hơn tạo gradient mỗi khung hình).
  const glowCache = {};
  function glowSprite(color) {
    if (glowCache[color]) return glowCache[color];
    const c = document.createElement("canvas");
    c.width = c.height = 128;
    const g = c.getContext("2d");
    const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    gr.addColorStop(0, color); gr.addColorStop(0.35, color.replace(/[\d.]+\)$/, (m) => (parseFloat(m) * 0.45).toFixed(3) + ")"));
    gr.addColorStop(1, color.replace(/[\d.]+\)$/, "0)"));
    g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
    return (glowCache[color] = c);
  }
  function glow(x, y, r, color, additive = true) {
    const prev = ctx.globalCompositeOperation;
    if (additive) ctx.globalCompositeOperation = "lighter";
    ctx.drawImage(glowSprite(color), x - r, y - r, r * 2, r * 2);
    ctx.globalCompositeOperation = prev;
  }

  // ---------- cá: vẽ quanh (0,0), đầu hướng +x, L = chiều dài toàn thân ----------
  function eye(x, y, r) {
    ctx.fillStyle = "#fffbe8"; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
    ctx.fillStyle = "#14181c"; ctx.beginPath(); ctx.arc(x + r * 0.2, y, r * 0.6, 0, TAU); ctx.fill();
  }

  // Cá linh: nhỏ, thân bạc, lưng xanh xám, đuôi chẻ, chấm đen gần đuôi.
  function caLinh(L) {
    const g = ctx.createLinearGradient(0, -L * 0.2, 0, L * 0.2);
    g.addColorStop(0, "#6f8799"); g.addColorStop(0.45, "#dfe8ee"); g.addColorStop(1, "#f7f4ea");
    ctx.fillStyle = "#9fb2c0";
    ctx.beginPath(); ctx.moveTo(-L * 0.28, 0); ctx.lineTo(-L * 0.5, -L * 0.2); ctx.lineTo(-L * 0.41, 0); ctx.lineTo(-L * 0.5, L * 0.2); ctx.closePath(); ctx.fill();
    ctx.beginPath(); ctx.moveTo(0, -L * 0.15); ctx.lineTo(-L * 0.1, -L * 0.28); ctx.lineTo(-L * 0.14, -L * 0.13); ctx.fill();      // vây lưng
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.moveTo(L * 0.5, 0);
    ctx.bezierCurveTo(L * 0.42, -L * 0.2, L * 0.0, -L * 0.2, -L * 0.3, -L * 0.04);
    ctx.lineTo(-L * 0.3, L * 0.04);
    ctx.bezierCurveTo(L * 0.0, L * 0.19, L * 0.42, L * 0.17, L * 0.5, 0); ctx.fill();
    ctx.fillStyle = "rgba(30,40,50,.55)"; ctx.beginPath(); ctx.arc(-L * 0.2, 0, L * 0.035, 0, TAU); ctx.fill();
    ctx.strokeStyle = "rgba(255,255,255,.6)"; ctx.lineWidth = Math.max(0.6, L * 0.02);
    ctx.beginPath(); ctx.moveTo(L * 0.3, L * 0.02); ctx.lineTo(-L * 0.18, L * 0.02); ctx.stroke();
    eye(L * 0.36, -L * 0.03, L * 0.05);
  }

  // Cá lóc: thân dài tròn, màu ô liu sẫm có đốm, vây lưng/vây hậu môn chạy dài, đầu dẹt miệng rộng.
  function caLoc(L) {
    ctx.fillStyle = "#3e4a2c";
    ctx.beginPath(); ctx.moveTo(L * 0.18, -L * 0.1); ctx.quadraticCurveTo(-L * 0.1, -L * 0.2, -L * 0.4, -L * 0.07); ctx.lineTo(-L * 0.38, -L * 0.04); ctx.lineTo(L * 0.18, -L * 0.07); ctx.fill(); // vây lưng
    ctx.beginPath(); ctx.moveTo(L * 0.0, L * 0.08); ctx.quadraticCurveTo(-L * 0.2, L * 0.17, -L * 0.4, L * 0.07); ctx.lineTo(-L * 0.38, L * 0.04); ctx.fill();                                  // vây hậu môn
    ctx.beginPath(); ctx.ellipse(-L * 0.44, 0, L * 0.09, L * 0.1, 0, 0, TAU); ctx.fill();                                                                                                          // đuôi tròn
    const g = ctx.createLinearGradient(0, -L * 0.1, 0, L * 0.1);
    g.addColorStop(0, "#4b5a33"); g.addColorStop(0.6, "#7c8a55"); g.addColorStop(1, "#c9c49a");
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.moveTo(L * 0.5, L * 0.01);
    ctx.quadraticCurveTo(L * 0.46, -L * 0.1, L * 0.3, -L * 0.1);
    ctx.lineTo(-L * 0.38, -L * 0.06); ctx.lineTo(-L * 0.38, L * 0.06); ctx.lineTo(L * 0.3, L * 0.1);
    ctx.quadraticCurveTo(L * 0.47, L * 0.08, L * 0.5, L * 0.01); ctx.fill();
    ctx.fillStyle = "rgba(25,30,15,.55)";
    for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.ellipse(L * (0.16 - i * 0.14), -L * 0.02, L * 0.045, L * 0.06, 0.4, 0, TAU); ctx.fill(); }
    ctx.strokeStyle = "rgba(20,20,10,.6)"; ctx.lineWidth = Math.max(0.6, L * 0.012);
    ctx.beginPath(); ctx.moveTo(L * 0.5, L * 0.02); ctx.lineTo(L * 0.38, L * 0.04); ctx.stroke();                   // miệng
    eye(L * 0.4, -L * 0.04, L * 0.035);
  }

  // Cá kèo: thân thon nâu xám có chấm, mắt lồi trên đỉnh đầu, vây lưng nhọn, vây ngực tròn.
  function caKeo(L) {
    ctx.fillStyle = "#7a6a4f";
    ctx.beginPath(); ctx.moveTo(L * 0.12, -L * 0.08); ctx.lineTo(L * 0.02, -L * 0.24); ctx.lineTo(-L * 0.06, -L * 0.07); ctx.fill();   // vây lưng 1
    ctx.beginPath(); ctx.moveTo(-L * 0.08, -L * 0.07); ctx.quadraticCurveTo(-L * 0.25, -L * 0.17, -L * 0.36, -L * 0.04); ctx.fill();  // vây lưng 2
    ctx.beginPath(); ctx.moveTo(-L * 0.34, 0); ctx.lineTo(-L * 0.5, -L * 0.09); ctx.quadraticCurveTo(-L * 0.54, 0, -L * 0.5, L * 0.09); ctx.closePath(); ctx.fill();
    const g = ctx.createLinearGradient(0, -L * 0.1, 0, L * 0.1);
    g.addColorStop(0, "#8a7656"); g.addColorStop(1, "#d8c9a4");
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.moveTo(L * 0.48, L * 0.03);
    ctx.quadraticCurveTo(L * 0.44, -L * 0.11, L * 0.24, -L * 0.09);
    ctx.lineTo(-L * 0.36, -L * 0.03); ctx.lineTo(-L * 0.36, L * 0.03);
    ctx.quadraticCurveTo(L * 0.2, L * 0.12, L * 0.48, L * 0.03); ctx.fill();
    ctx.fillStyle = "rgba(60,40,20,.6)";
    for (let i = 0; i < 6; i++) { ctx.beginPath(); ctx.arc(L * (0.18 - i * 0.09), -L * 0.02 + (i % 2) * L * 0.035, L * 0.018, 0, TAU); ctx.fill(); }
    ctx.fillStyle = "rgba(160,130,90,.85)";
    ctx.beginPath(); ctx.ellipse(L * 0.2, L * 0.07, L * 0.07, L * 0.04, 0.5, 0, TAU); ctx.fill();                       // vây ngực
    eye(L * 0.36, -L * 0.1, L * 0.05);
  }

  // ---------- bông / rau (icon nhỏ, tâm 0,0, cỡ S) ----------
  function dienDien(S) {               // chùm bông điên điển vàng rủ
    ctx.strokeStyle = "#5f8a3a"; ctx.lineWidth = Math.max(1, S * 0.06);
    ctx.beginPath(); ctx.moveTo(-S * 0.35, -S * 0.35); ctx.quadraticCurveTo(0, -S * 0.45, S * 0.35, -S * 0.2); ctx.stroke();
    const pts = [[-0.25, -0.15], [0.0, -0.05], [0.25, 0.0], [-0.12, 0.18], [0.14, 0.24], [-0.32, 0.12]];
    pts.forEach(([px, py], i) => {
      ctx.save(); ctx.translate(px * S, py * S); ctx.rotate(0.4 - i * 0.15);
      ctx.fillStyle = i % 2 ? "#f6c624" : "#ffd84a";
      ctx.beginPath(); ctx.ellipse(0, 0, S * 0.13, S * 0.18, 0, 0, TAU); ctx.fill();
      ctx.fillStyle = "#e09a12"; ctx.beginPath(); ctx.ellipse(0, S * 0.06, S * 0.06, S * 0.08, 0, 0, TAU); ctx.fill();
      ctx.restore();
    });
  }
  function bongSung(S, open = 1) {     // bông súng hồng tím, cánh nhọn hai lớp
    const layers = [[S * 0.48, "#c9579a", 8, 0], [S * 0.34, "#ee8fc0", 8, Math.PI / 8]];
    layers.forEach(([r, col, n, off]) => {
      ctx.fillStyle = col;
      for (let i = 0; i < n; i++) {
        const a = off + (i / n) * TAU;
        ctx.save(); ctx.rotate(a); ctx.scale(1, open);
        ctx.beginPath(); ctx.moveTo(0, 0); ctx.quadraticCurveTo(r * 0.35, -r * 0.3, r, 0); ctx.quadraticCurveTo(r * 0.35, r * 0.3, 0, 0); ctx.fill();
        ctx.restore();
      }
    });
    ctx.fillStyle = "#ffd54a"; ctx.beginPath(); ctx.arc(0, 0, S * 0.12, 0, TAU); ctx.fill();
  }
  function keoNeo(S) {                 // bó kèo nèo: lá tròn xanh trên cuống dài + bông vàng nhạt
    ctx.strokeStyle = "#6fae4a"; ctx.lineWidth = Math.max(1, S * 0.07);
    [[-0.3, -0.3], [0.05, -0.42], [0.32, -0.25]].forEach(([lx, ly]) => { ctx.beginPath(); ctx.moveTo(0, S * 0.45); ctx.lineTo(lx * S, ly * S); ctx.stroke(); });
    [[-0.3, -0.3, -0.5], [0.05, -0.42, 0.1], [0.32, -0.25, 0.6]].forEach(([lx, ly, rot]) => {
      ctx.fillStyle = "#4f9a3c"; ctx.beginPath(); ctx.ellipse(lx * S, ly * S, S * 0.2, S * 0.14, rot, 0, TAU); ctx.fill();
      ctx.strokeStyle = "rgba(220,255,200,.5)"; ctx.lineWidth = Math.max(0.6, S * 0.025);
      ctx.beginPath(); ctx.moveTo(lx * S - Math.cos(rot) * S * 0.16, ly * S - Math.sin(rot) * S * 0.16); ctx.lineTo(lx * S + Math.cos(rot) * S * 0.16, ly * S + Math.sin(rot) * S * 0.16); ctx.stroke();
    });
    ctx.fillStyle = "#fff2a0";
    for (let i = 0; i < 3; i++) { const a = (i / 3) * TAU; ctx.beginPath(); ctx.ellipse(Math.cos(a) * S * 0.08, S * 0.12 + Math.sin(a) * S * 0.08, S * 0.08, S * 0.06, a, 0, TAU); ctx.fill(); }
    ctx.fillStyle = "#c9a227"; ctx.beginPath(); ctx.arc(0, S * 0.12, S * 0.04, 0, TAU); ctx.fill();
  }

  const FISH = { ca_linh: caLinh, ca_loc: caLoc, ca_keo: caKeo };
  const PLANT = { bong_dien_dien: dienDien, bong_sung: bongSung, keo_neo: keoNeo };

  // Khăn rằn: dải ca rô đen trắng từ (x0,y0) đến (x1,y1), bề rộng wd.
  function khanRan(x0, y0, x1, y1, wd) {
    const len = Math.hypot(x1 - x0, y1 - y0), a = Math.atan2(y1 - y0, x1 - x0);
    ctx.save(); ctx.translate(x0, y0); ctx.rotate(a);
    ctx.fillStyle = "#1d1d22"; ctx.fillRect(0, -wd / 2, len, wd);
    ctx.fillStyle = "#f2efe6";
    const c = Math.max(1.5, wd / 3);
    for (let i = 0; i * c < len; i++) for (let j = 0; j < 3; j++) if ((i + j) % 2 === 0) ctx.fillRect(i * c, -wd / 2 + j * c, Math.min(c, len - i * c), Math.min(c, wd - j * c));
    ctx.restore();
  }

  CN.art = {
    TAU, hash, strHash, glow, khanRan,
    fish(kind, x, y, L, flip = false, rot = 0) {
      const f = FISH[kind];
      ctx.save(); ctx.translate(x, y); if (flip) ctx.scale(-1, 1); if (rot) ctx.rotate(rot);
      if (f) f(L); else caLinh(L);
      ctx.restore();
    },
    plant(kind, x, y, S, o = {}) {
      ctx.save(); ctx.translate(x, y);
      if (kind === "bong_sung") bongSung(S, o.open ?? 1); else (PLANT[kind] || dienDien)(S);
      ctx.restore();
    },
    hasFish: (k) => !!FISH[k],
  };
})(window.CN);
