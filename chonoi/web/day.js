"use strict";
/*
 * Mode `day` cho cửa sổ chơi (python3 -m chonoi.live --mode day [--days N]) — trongnghia2304, Phase 4 (AC-P4-11).
 * File riêng để không đụng phần vẽ của index.html (Tiệp giữ). index.html chỉ nạp: <script src="day.js"></script>.
 *
 * Phong cách "Sạp đêm chợ nổi" (pixel art indie, vẽ hoàn toàn bằng code, không dùng asset ngoài — khớp CREDITS.md):
 * trời đêm + sông ngả màu theo dải, dây đèn lồng, mái sạp sọc đỏ-kem, quầy gỗ, thẻ giấy có viền pixel, đồng xu.
 *
 * Vẽ ĐÈ lên canvas sau khung của index.html (requestAnimationFrame đăng ký sau nên chạy sau):
 *   - HUD Ngày: "Ngày N/T", pha, tiến độ thu gom đã lấy/cần theo kế hoạch (Ticket-02 mục 2).
 *   - Màn chuyển pha (tự tắt sau 4 s hoặc khi nhấn phím): DayIntro (day_plan), EveningIntro (phase_start quan),
 *     DayResult (quan_end), Summary (hết --days).
 *   - Shop: tiền, cấp đã mua / đang áp dụng, mua oxy / Máu, đóng Shop, đồng hồ Shop, thông báo bought / buy_failed.
 *   - Tạm dừng: P hoặc Esc (nút `pause`, cạnh lên), mờ nền.
 * Chỉ ĐỌC snapshot và gửi nút qua POST /input như index.html; không có luật ở đây.
 * Không phải mode day thì file này không vẽ gì.
 */
(function () {
  const cv = document.getElementById("c");
  const g = cv.getContext("2d");

  const KIND = { ca_loc: "cá lóc", ca_linh: "cá linh", ca_keo: "cá kèo", bong_dien_dien: "bông điên điển",
                 bong_sung: "bông súng", keo_neo: "kèo nèo" };
  const DISH = { ca_loc_nuong_trui: "Cá lóc nướng trui", goi_bong_sung: "Gỏi bông súng",
                 lau_ca_linh_dien_dien: "Lẩu cá linh bông điên điển", canh_chua_ca_loc: "Canh chua cá lóc",
                 ca_keo_nuong: "Cá kèo nướng muối ớt", lau_mam: "Lẩu mắm miền Tây" };
  const UPG = { oxygen: { name: "Bình oxy", stat: "oxygen_max_s", unit: "s oxy", key: "1", sprite: "tank",
                          blurb: "Lặn lâu hơn trước khi hết hơi." },
                hp: { name: "Áo phao", stat: "hp_max", unit: " Máu", key: "2", sprite: "vest",
                      blurb: "Chịu thêm một cú cắn hay một lần ngạt." } };
  const FAIL = { funds: "không đủ tiền", max_level: "đã tối đa", unknown: "không hỗ trợ", out_of_stock: "hết hàng" };
  const kn = (k) => KIND[k] || k;
  const dn = (d) => DISH[d] || d;
  const BANNER_MS = 4000;

  // ---------- bảng màu "Sạp đêm chợ nổi" ----------
  const C = {
    ink: "#1b1420", night0: "#141c33", night1: "#1d2a48", night2: "#283a5c", river0: "#18324a", river1: "#1f4560",
    wood0: "#4a2c1d", wood1: "#6b3f26", wood2: "#8a5534", wood3: "#a96d40", paper: "#f3e3c3", paper2: "#e2cba0",
    paperEdge: "#b8925e", red: "#c8402f", red2: "#8f2a22", cream: "#f2e6c9", gold: "#f6c445", gold2: "#c98f1e",
    green: "#5fae4e", green2: "#3c7a33", grey: "#8a8f99", grey2: "#5b5f68", text: "#2a1e16", light: "#fff4d6",
    lamp: "#ff9a3c", lampGlow: "rgba(255,170,80,.18)", teal: "#7fd6d0",
  };
  const FONT = '"Trebuchet MS", "Segoe UI", system-ui, sans-serif';

  // ---------- sprite pixel (lưới chữ + bảng màu), vẽ sắc nét ----------
  const SPR = {
    coin: { pal: { o: C.ink, y: C.gold, Y: "#ffe08a", d: C.gold2 }, rows: [
      "..oooo..", ".oyyyyo.", "oyYYyyyo", "oyYddyyo", "oyyddyyo", "oyyyyydo", ".oyyyddo", "..oooo.."] },
    tank: { pal: { o: C.ink, b: "#5bb8e6", B: "#a9e3ff", d: "#2f6f9a", g: "#cfd6de", G: "#8a95a3" }, rows: [
      "...oooo...", "...oGGo...", "..oggggo..", ".oooooooo.", ".obBBbbdo.", ".obBbbbdo.", ".obBbbbdo.", ".obbbbbdo.",
      ".obbbbbdo.", ".obbbbbdo.", ".obbbbddo.", ".odddddoo.", "..oooooo.."] },
    vest: { pal: { o: C.ink, r: "#ff7a3d", R: "#ffb27a", d: "#c4521f", w: C.cream }, rows: [
      ".oo....oo.", "orRo..oRro", "orrRooRrro", "orrrrrrrro", "owwwwwwwwo", "orrrrrrrro", "orrrrrrrro", "owwwwwwwwo",
      "orrrrrrrdo", "orrrrrrddo", ".oooooooo."] },
    lantern: { pal: { o: C.ink, r: C.red, R: "#ff6b4a", y: C.gold }, rows: [
      "..oo..", ".oyyo.", "oRrrRo", "orRRro", "orRRro", "oRrrRo", ".oyyo.", "..oo.."] },
    star: { pal: { o: C.ink, y: C.gold, Y: "#ffe08a" }, rows: [
      "..o..", ".oYo.", "oyYyo", ".oyo.", "o.o.o"] },
    starOff: { pal: { o: "#3b3346", y: "#5b5068" }, rows: [
      "..o..", ".oyo.", "oyyyo", ".oyo.", "o.o.o"] },
  };
  function sprite(name, x, y, px) {
    const s = SPR[name];
    s.rows.forEach((row, j) => {
      for (let i = 0; i < row.length; i++) {
        const c = s.pal[row[i]];
        if (!c) continue;
        g.fillStyle = c; g.fillRect(Math.round(x + i * px), Math.round(y + j * px), px, px);
      }
    });
  }

  // ---------- trạng thái: dùng snapshot của index.html nếu có, không thì tự poll ----------
  let own = null;
  const S = () => { try { if (typeof snap !== "undefined" && snap) return snap; } catch (e) { /* bỏ qua */ } return own; };
  (async function selfPoll() {
    let shared = false;
    try { shared = typeof snap !== "undefined"; } catch (e) { shared = false; }
    if (shared) return; // index.html đã poll
    try { own = await (await fetch("/state", { cache: "no-store" })).json(); } catch (e) { /* mất kết nối */ }
    setTimeout(selfPoll, 33);
  })();

  // ---------- gửi nút ----------
  function post(body) {
    return fetch("/input", { method: "POST", body: JSON.stringify(body), headers: { "Content-Type": "application/json" } })
      .catch(() => {});
  }
  async function tap(button) { await post({ [button]: true }); await post({ [button]: false }); }  // một cạnh lên
  const buy = (kind) => post({ buy: kind });
  const isDay = () => { const s = S(); return !!(s && s.day_mode); };

  // ---------- theo dõi sự kiện (dedupe theo tick + tên + data) ----------
  const seen = new Set();
  let lastTick = -1;
  let banner = null;                 // {title, lines, until}
  let toast = null;                  // {text, color, until}
  let dayStats = null;               // thống kê Ngày đang chạy
  const results = [];                // kết quả từng Ngày (DayResult / Summary)
  const sold = {};                   // món bán chạy

  function resetTracking() {
    seen.clear(); banner = null; toast = null; dayStats = null; results.length = 0;
    Object.keys(sold).forEach((k) => delete sold[k]);
  }
  function newDayStats(day) { return { day, served: 0, left: 0, tips: 0, startEarned: null, startRep: null }; }

  function onEvent(e, s) {
    const d = e.data || {};
    switch (e.name) {
      case "day_start":
        dayStats = newDayStats(e.day);
        dayStats.startEarned = s.earned || 0; dayStats.startRep = s.reputation;
        break;
      case "day_plan": {
        const dishes = Object.entries(d.dishes || {}).map(([k, n]) => dn(k) + " ×" + n);
        const need = Object.entries(d.ingredients || {}).map(([k, n]) => kn(k) + " ×" + n);
        showBanner("Ngày " + e.day + (s.days_total ? " / " + s.days_total : ""), "Sáng sớm trên sông",
                   ["Má Tư định nấu: " + dishes.join(", "), "Cần lấy: " + need.join(", "),
                    "Lặn & hái rồi cập bến (E ở bến) để mở quán."]);
        break;
      }
      case "phase_start":
        if (e.phase === "quan") {
          const stock = countItems(s.stock);
          showBanner("Mở quán", "Tối Ngày " + e.day + " trên nhà bè",
                     ["Kho mang về: " + (stock.length ? stock.join(", ") : "(trống)"),
                      "Nấu ở bếp (E), bưng ra bàn, phục vụ trước khi khách hết kiên nhẫn."]);
        }
        break;
      case "served":
        if (dayStats) { dayStats.served++; dayStats.tips += d.tip || 0; }
        sold[d.dish_id] = (sold[d.dish_id] || 0) + 1;
        break;
      case "customer_left":
        if (dayStats) dayStats.left++;
        break;
      case "quan_end": {
        const st = dayStats || newDayStats(e.day);
        const repDelta = st.startRep == null ? null : (d.reputation - st.startRep);
        const r = { day: e.day, served: st.served, left: st.left, shift: d.shift_earned, tips: st.tips,
                    money: d.money, reputation: d.reputation, repDelta };
        results.push(r);
        showBanner("Dọn quán", "Kết thúc Ngày " + e.day,
                   ["Khách đã phục vụ: " + r.served + " · bỏ đi: " + r.left,
                    "Thu trong ca: " + r.shift + " (boa " + r.tips + ") · tiền hiện có: " + r.money,
                    "Uy tín: " + fmtRep(r.reputation) + (repDelta == null ? "" : " (" + (repDelta >= 0 ? "+" : "") + repDelta.toFixed(1) + ")"),
                    "Ghé sạp nâng cấp cho lần lặn sau."]);
        break;
      }
      case "bought":
        showToast("Đã mua " + (UPG[d.upgrade] ? UPG[d.upgrade].name : d.upgrade) + " cấp " + d.level +
                  " (−" + d.price + ") · có hiệu lực từ Ngày sau", C.green);
        break;
      case "buy_failed":
        showToast("Không mua được: " + (FAIL[d.reason] || d.reason), C.red);
        break;
      case "shop_end":
        banner = null;
        break;
      default:
        break;
    }
  }
  function track(s) {
    if (s.tick < lastTick) resetTracking();   // R: chơi lại
    lastTick = s.tick;
    for (const e of s.events || []) {
      const key = e.tick + "|" + e.name + "|" + JSON.stringify(e.data);
      if (seen.has(key)) continue;
      seen.add(key);
      onEvent(e, s);
    }
    if (seen.size > 2000) { const keep = [...seen].slice(-500); seen.clear(); keep.forEach((k) => seen.add(k)); }
  }
  function showBanner(title, sub, lines) { banner = { title, sub, lines, until: performance.now() + BANNER_MS }; }
  function showToast(textValue, color) { toast = { text: textValue, color, until: performance.now() + 2500 }; }

  // ---------- tiện ích vẽ ----------
  function t(s, x, y, o = {}) {
    g.font = (o.bold ? "700 " : "500 ") + (o.size || 18) + "px " + FONT;
    g.textAlign = o.align || "left";
    g.textBaseline = "alphabetic";
    if (o.outline) {               // chữ viền tối kiểu game pixel
      g.lineJoin = "round"; g.lineWidth = o.outlineW || 4; g.strokeStyle = o.outline; g.strokeText(s, x, y);
    }
    g.fillStyle = o.color || C.light;
    g.fillText(s, x, y);
  }
  function measure(s, size, bold) { g.font = (bold ? "700 " : "500 ") + size + "px " + FONT; return g.measureText(s).width; }
  // khung pixel: viền mực 3 px, mép sáng trên-trái, bóng dưới-phải, bóng đổ khối
  function box(x, y, w, h, fill, o = {}) {
    x = Math.round(x); y = Math.round(y); w = Math.round(w); h = Math.round(h);
    const p = o.px || 3;
    if (o.drop !== false) { g.fillStyle = "rgba(0,0,0,.35)"; g.fillRect(x + p * 2, y + p * 2, w, h); }
    g.fillStyle = C.ink; g.fillRect(x, y, w, h);
    g.fillStyle = fill; g.fillRect(x + p, y + p, w - 2 * p, h - 2 * p);
    g.fillStyle = o.light || "rgba(255,255,255,.22)"; g.fillRect(x + p, y + p, w - 2 * p, p); g.fillRect(x + p, y + p, p, h - 2 * p);
    g.fillStyle = o.dark || "rgba(0,0,0,.22)"; g.fillRect(x + p, y + h - 2 * p, w - 2 * p, p); g.fillRect(x + w - 2 * p, y + p, p, h - 2 * p);
  }
  // tấm gỗ: các ván ngang + đinh ở góc
  function plank(x, y, w, h) {
    box(x, y, w, h, C.wood2, { light: "rgba(255,220,170,.18)" });
    g.fillStyle = C.wood1;
    for (let yy = y + 3 + 18; yy < y + h - 6; yy += 18) g.fillRect(x + 6, Math.round(yy), w - 12, 2);
    g.fillStyle = "rgba(0,0,0,.12)";
    for (let i = 0; i < 6; i++) g.fillRect(Math.round(x + 20 + ((i * 97) % (w - 40))), Math.round(y + 10 + ((i * 53) % (h - 20))), 14, 2);
    [[x + 9, y + 9], [x + w - 15, y + 9], [x + 9, y + h - 15], [x + w - 15, y + h - 15]].forEach(([nx, ny]) => {
      g.fillStyle = C.ink; g.fillRect(Math.round(nx), Math.round(ny), 6, 6);
      g.fillStyle = "#c9b28a"; g.fillRect(Math.round(nx) + 1, Math.round(ny) + 1, 3, 3);
    });
  }
  function paperCard(x, y, w, h) {
    box(x, y, w, h, C.paper, { light: "rgba(255,255,255,.45)", dark: "rgba(120,80,30,.18)" });
    g.fillStyle = C.paperEdge; g.fillRect(Math.round(x) + 9, Math.round(y) + 9, Math.round(w) - 18, 2);
  }
  // nút khối: bóng đổ cứng, trạng thái tắt màu xám
  function chunkyButton(x, y, w, h, label, on, color, color2, sub) {
    const c1 = on ? color : C.grey, c2 = on ? color2 : C.grey2;
    g.fillStyle = C.ink; g.fillRect(Math.round(x), Math.round(y) + 6, Math.round(w), Math.round(h));
    g.fillStyle = c2; g.fillRect(Math.round(x) + 3, Math.round(y) + 3, Math.round(w) - 6, Math.round(h));
    box(x, y, w, h, c1, { drop: false, light: "rgba(255,255,255,.3)" });
    t(label, x + w / 2, y + h / 2 + (sub ? 1 : 7), { size: 19, bold: true, align: "center", color: on ? C.light : "#e6e6e6",
                                                     outline: on ? "rgba(0,0,0,.45)" : null, outlineW: 3 });
    if (sub) t(sub, x + w / 2, y + h / 2 + 19, { size: 13, align: "center", color: on ? "rgba(255,244,214,.9)" : "#d0d0d0" });
  }
  function countItems(list) {
    const by = {};
    if (Array.isArray(list)) list.forEach((x) => { const k = typeof x === "string" ? x : x.kind; by[k] = (by[k] || 0) + 1; });
    else Object.entries(list || {}).forEach(([k, n]) => { if (n > 0) by[k] = n; });
    return Object.keys(by).sort().map((k) => kn(k) + " ×" + by[k]);
  }
  const fmtRep = (r) => (typeof r === "number" ? r.toFixed(1) : "?");
  const fmtSec = (ticks) => Math.ceil((ticks || 0) / 60) + "s";

  // ---------- cảnh đêm chợ nổi (nền Shop / tổng kết) ----------
  function nightScene(w, h, now) {
    const bands = [C.night0, C.night1, C.night2];
    const skyH = h * 0.62;
    for (let i = 0; i < 3; i++) { g.fillStyle = bands[i]; g.fillRect(0, Math.round(skyH * i / 3), w, Math.ceil(skyH / 3) + 1); }
    // sao lấp lánh (vị trí cố định theo chỉ số)
    for (let i = 0; i < 46; i++) {
      const sx = (i * 137.5) % w, sy = ((i * 61.3) % (skyH * 0.7));
      const on = ((now / 600 + i) | 0) % 5 !== 0;
      g.fillStyle = on ? "rgba(255,244,214,.75)" : "rgba(255,244,214,.25)";
      g.fillRect(Math.round(sx), Math.round(sy), 2, 2);
    }
    // trăng pixel
    g.fillStyle = "#fff1c9"; g.fillRect(Math.round(w * 0.82), Math.round(skyH * 0.16), 30, 30);
    g.fillStyle = C.night1; g.fillRect(Math.round(w * 0.82) + 18, Math.round(skyH * 0.16), 12, 12);
    // bóng dừa nước + nhà sàn xa
    g.fillStyle = "#0f1526";
    for (let x = 0; x < w; x += 22) {
      const hh = 18 + ((x * 7) % 26);
      g.fillRect(x, Math.round(skyH - hh), 18, hh);
    }
    g.fillRect(Math.round(w * 0.1), Math.round(skyH - 56), 90, 56); g.fillRect(Math.round(w * 0.1) - 8, Math.round(skyH - 64), 106, 10);
    // sông
    g.fillStyle = C.river0; g.fillRect(0, Math.round(skyH), w, h - skyH);
    g.fillStyle = C.river1;
    for (let r = 0; r < 9; r++) {
      const yy = skyH + 10 + r * ((h - skyH) / 9);
      const off = (now / 40 + r * 37) % 80;
      for (let x = -80 + off; x < w; x += 80) g.fillRect(Math.round(x), Math.round(yy), 34, 2);
    }
    // phản chiếu đèn trên mặt nước
    g.fillStyle = "rgba(255,170,80,.22)";
    for (let r = 0; r < 6; r++) g.fillRect(Math.round(w / 2 - 60 + ((r * 23) % 40)), Math.round(skyH + 14 + r * 16), 120 - r * 14, 3);
  }
  function lanternString(x0, x1, y, now) {
    g.fillStyle = C.ink;
    for (let x = x0; x <= x1; x += 4) {
      const sag = Math.sin(((x - x0) / (x1 - x0)) * Math.PI) * 18;
      g.fillRect(Math.round(x), Math.round(y + sag), 3, 2);
    }
    const n = Math.max(3, Math.floor((x1 - x0) / 110));
    for (let i = 0; i < n; i++) {
      const lx = x0 + (i + 0.5) * (x1 - x0) / n;
      const sag = Math.sin(((lx - x0) / (x1 - x0)) * Math.PI) * 18;
      const bob = Math.round(Math.sin(now / 500 + i) * 2);
      const gy = y + sag + 20 + bob;
      const glow = g.createRadialGradient(lx, gy, 2, lx, gy, 34);
      glow.addColorStop(0, "rgba(255,190,100,.55)"); glow.addColorStop(1, "rgba(255,150,60,0)");
      g.fillStyle = glow; g.fillRect(lx - 34, gy - 34, 68, 68);
      sprite("lantern", lx - 9, y + sag + 8 + bob, 3);
    }
  }
  function awning(x, y, w) {
    const h = 30, n = Math.max(6, Math.round(w / 36)), stripe = w / n;   // số sọc nguyên -> không tràn mép
    for (let i = 0; i < n; i++) {
      g.fillStyle = i % 2 ? C.cream : C.red;
      g.fillRect(Math.round(x + i * stripe), Math.round(y), Math.ceil(stripe), h);
      // mép lượn sóng
      g.beginPath(); g.arc(x + i * stripe + stripe / 2, y + h, stripe / 2, 0, Math.PI); g.fill();
    }
    g.fillStyle = C.ink; g.fillRect(Math.round(x), Math.round(y) - 4, Math.round(w), 6);
    g.fillStyle = "rgba(0,0,0,.18)"; g.fillRect(Math.round(x), Math.round(y) + h - 4, Math.round(w), 4);
  }
  function stars(x, y, rep, max) {
    for (let i = 0; i < max; i++) sprite(i < Math.floor(rep + 1e-9) ? "star" : "starOff", x + i * 24, y - 2, 4);
  }

  // ---------- Shop ----------
  const buttons = [];   // vùng bấm chuột của khung hình hiện tại
  function drawShop(s, w, h, now) {
    buttons.length = 0;
    nightScene(w, h, now);
    lanternString(-20, w + 20, 6, now);
    const pw = Math.min(820, w - 28), x = (w - pw) / 2;
    const top = Math.max(70, h * 0.11), maxBottom = h - 18;
    const ch = Math.max(200, Math.min(250, maxBottom - (top + 154) - 120));   // chiều cao thẻ
    const bottom = Math.min(maxBottom, top + 154 + ch + 120);               // quầy vừa khít nội dung
    // mái sạp + quầy gỗ
    awning(x - 10, top, pw + 20);
    plank(x, top + 40, pw, bottom - top - 40);
    // bảng hiệu treo
    const title = "SẠP NÂNG CẤP · NGÀY " + (s.day || "?");
    const tw = measure(title, 24, true) + 56;
    box(x + (pw - tw) / 2, top + 54, tw, 46, C.wood0, { light: "rgba(255,220,170,.2)" });
    t(title, x + pw / 2, top + 86, { size: 24, bold: true, align: "center", color: C.gold, outline: C.ink });
    // dòng ví: xu, tổng thu, uy tín sao, đồng hồ
    const wy = top + 132;
    sprite("coin", x + 26, wy - 21, 3);
    t(String(s.money ?? 0), x + 58, wy, { size: 24, bold: true, color: C.gold, outline: C.ink });
    t("tổng thu " + (s.earned ?? 0), x + 58 + measure(String(s.money ?? 0), 24, true) + 14, wy,
      { size: 16, color: C.paper, outline: "rgba(0,0,0,.5)", outlineW: 3 });
    const rmax = 5;
    t("uy tín", x + pw / 2 + 40, wy, { size: 16, color: C.paper, outline: "rgba(0,0,0,.5)", outlineW: 3 });
    stars(x + pw / 2 + 92, wy - 16, s.reputation || 0, rmax);
    const clock = "⏳ " + fmtSec(s.time_left_ticks);
    t(clock, x + pw - 26, wy, { size: 18, bold: true, align: "right", color: C.light, outline: C.ink });
    // 2 thẻ nâng cấp
    const ups = (s.shop_tuning && s.shop_tuning.upgrades) || {};
    const bought = s.upgrades || {}, active = s.active_upgrades || {};
    const cardsY = wy + 22, gap = 18, cw = (pw - 52 - gap) / 2;
    ["oxygen", "hp"].forEach((kind, idx) => {
      const info = UPG[kind], levels = ups[kind] || [];
      const lv = bought[kind] || 0, act = active[kind] || 0, next = levels[lv];
      const cx = x + 26 + idx * (cw + gap);
      paperCard(cx, cardsY, cw, ch);
      // ô icon
      box(cx + 18, cardsY + 22, 66, 66, kind === "oxygen" ? "#d9eef7" : "#fde0cf", { drop: false });
      sprite(info.sprite, cx + 18 + (66 - SPR[info.sprite].rows[0].length * 4) / 2, cardsY + 22 + (66 - SPR[info.sprite].rows.length * 4) / 2, 4);
      t(info.name, cx + 98, cardsY + 46, { size: 22, bold: true, color: C.text });
      t(info.blurb, cx + 98, cardsY + 70, { size: 13, color: "#6b5236" });
      // vạch cấp
      t("Cấp", cx + 98, cardsY + 96, { size: 13, bold: true, color: "#6b5236" });
      for (let i = 0; i < levels.length; i++) {
        const filled = i < lv, live = i < act;
        g.fillStyle = C.ink; g.fillRect(Math.round(cx + 132 + i * 26), Math.round(cardsY + 84), 20, 14);
        g.fillStyle = filled ? (live ? C.green : C.gold) : C.paper2;
        g.fillRect(Math.round(cx + 134 + i * 26), Math.round(cardsY + 86), 16, 10);
      }
      t(lv > act ? "cấp mới chờ Ngày sau" : "", cx + 140 + levels.length * 26, cardsY + 96, { size: 12, color: C.gold2 });
      // dòng giá / hiệu lực
      const inner = cardsY + 112;
      g.fillStyle = C.paperEdge; g.fillRect(Math.round(cx + 18), Math.round(inner), Math.round(cw - 36), 2);
      if (next) {
        t("→ " + next[info.stat] + info.unit, cx + 22, inner + 30, { size: 18, bold: true, color: C.text });
        sprite("coin", cx + cw - 92, inner + 12, 3);
        t(String(next.price), cx + cw - 64, inner + 33, { size: 20, bold: true, color: (s.money ?? 0) >= next.price ? C.text : C.red });
      } else {
        t("Đã nâng tối đa", cx + 22, inner + 30, { size: 18, bold: true, color: C.green2 });
      }
      const canBuy = !!next && (s.money ?? 0) >= next.price;
      const bw = cw - 36, bh = 46, bx = cx + 18, by = cardsY + ch - bh - 22;
      const sub = !next ? "tối đa" : canBuy ? "phím " + info.key : "thiếu " + (next.price - (s.money ?? 0)) + " xu";
      chunkyButton(bx, by, bw, bh, next ? "MUA CẤP " + (lv + 1) : "ĐÃ ĐỦ", canBuy, C.green, C.green2, sub);
      buttons.push({ x: bx, y: by, w: bw, h: bh + 6, act: () => buy(kind) });
    });
    // kho dư + nút đóng sạp
    const fy = cardsY + ch + 30;
    const stock = countItems(s.stock);
    t("Kho dư (bỏ khi đóng sạp): " + (stock.length ? stock.join(", ") : "trống"), x + 26, fy,
      { size: 14, color: C.paper, outline: "rgba(0,0,0,.55)", outlineW: 3 });
    const cw2 = 300, ch2 = 50, cx2 = x + (pw - cw2) / 2, cy2 = Math.min(bottom - ch2 - 18, fy + 14);
    chunkyButton(cx2, cy2, cw2, ch2, "ĐÓNG SẠP  ⏎", true, C.red, C.red2, "Enter · sang Ngày kế");
    buttons.push({ x: cx2, y: cy2, w: cw2, h: ch2 + 6, act: () => tap("shop_done") });
  }

  // ---------- màn chuyển pha, tạm dừng, tổng kết, HUD Ngày ----------
  function plaque(x, y, w, h, title, sub) {
    plank(x, y, w, h);
    const tw = Math.min(w - 40, measure(title, 30, true) + 60);
    box(x + (w - tw) / 2, y - 18, tw, 50, C.red, { light: "rgba(255,255,255,.25)" });
    t(title, x + w / 2, y + 17, { size: 30, bold: true, align: "center", color: C.light, outline: C.ink, outlineW: 5 });
    if (sub) t(sub, x + w / 2, y + 58, { size: 16, align: "center", color: C.gold, outline: C.ink, outlineW: 3 });
  }
  function drawBanner(w, h) {
    if (!banner || performance.now() > banner.until) { banner = null; return; }
    const lines = banner.lines || [];
    const pw = Math.min(760, w - 32), cardH = 30 + lines.length * 30, ph = 72 + cardH + 34;
    const x = (w - pw) / 2, y = Math.max(40, h * 0.2);
    plaque(x, y, pw, ph, banner.title, banner.sub);
    paperCard(x + 22, y + 72, pw - 44, cardH);
    lines.forEach((l, i) => t(l, x + pw / 2, y + 72 + 32 + i * 30, { size: 17, align: "center", color: C.text }));
    // thanh thời gian tự tắt, nằm dưới thẻ giấy
    const left = Math.max(0, banner.until - performance.now()) / BANNER_MS;
    g.fillStyle = C.ink; g.fillRect(Math.round(x + 22), Math.round(y + ph - 22), Math.round(pw - 44), 8);
    g.fillStyle = C.gold; g.fillRect(Math.round(x + 24), Math.round(y + ph - 20), Math.round((pw - 48) * left), 4);
  }
  function drawToast(w) {
    if (!toast || performance.now() > toast.until) { toast = null; return; }
    const tw = Math.min(w - 32, measure(toast.text, 18, true) + 48);
    box((w - tw) / 2, 78, tw, 42, C.paper, { light: "rgba(255,255,255,.4)" });
    g.fillStyle = toast.color; g.fillRect(Math.round((w - tw) / 2) + 3, 81, 8, 36);
    t(toast.text, w / 2 + 4, 106, { size: 18, bold: true, align: "center", color: C.text });
  }
  function drawPaused(w, h) {
    g.fillStyle = "rgba(14,18,32,.7)"; g.fillRect(0, 0, w, h);
    const pw = Math.min(520, w - 32), x = (w - pw) / 2, y = h / 2 - 60;
    plaque(x, y, pw, 120, "TẠM DỪNG", "P hoặc Esc để chơi tiếp");
    t("Đồng hồ và mọi bộ đếm đứng yên", x + pw / 2, y + 96, { size: 15, align: "center", color: C.paper, outline: "rgba(0,0,0,.5)", outlineW: 3 });
  }
  function drawSummary(s, w, h, now) {
    nightScene(w, h, now);
    lanternString(-20, w + 20, 6, now);
    const pw = Math.min(720, w - 32), x = (w - pw) / 2;
    const best = Object.entries(sold).sort((a, b) => b[1] - a[1])[0];
    const rows = results.map((r) => "Ngày " + r.day + ": phục vụ " + r.served + ", bỏ đi " + r.left + ", thu " + r.shift);
    const ph = 260 + rows.length * 26, y = Math.max(70, (h - ph) / 2);
    plaque(x, y, pw, ph, "TỔNG KẾT", (s.days_completed ?? results.length) + (s.days_total ? " / " + s.days_total : "") + " Ngày ở chợ nổi");
    paperCard(x + 22, y + 74, pw - 44, ph - 96);
    const cx = x + 50;
    sprite("coin", cx, y + 96, 3);
    t((s.money ?? 0) + " xu", cx + 32, y + 117, { size: 22, bold: true, color: C.text });
    t("tổng thu " + (s.earned ?? 0), cx + 32 + measure((s.money ?? 0) + " xu", 22, true) + 14, y + 117, { size: 16, color: "#6b5236" });
    t("Điểm " + (s.score ?? "?"), x + pw - 50, y + 117, { size: 26, bold: true, align: "right", color: C.red2 });
    t("Uy tín", cx, y + 152, { size: 16, bold: true, color: "#6b5236" });
    stars(cx + 62, y + 136, s.reputation || 0, 5);
    t(fmtRep(s.reputation), cx + 62 + 5 * 24 + 8, y + 152, { size: 16, color: C.text });
    t("Món bán chạy: " + (best ? dn(best[0]) + " ×" + best[1] : "chưa bán món nào"), cx, y + 186, { size: 16, color: C.text });
    rows.forEach((l, i) => t(l, cx, y + 218 + i * 26, { size: 15, color: "#4a3a2a" }));
    t("R để chơi lại", x + pw / 2, y + ph - 30, { size: 15, align: "center", color: "#6b5236" });
  }
  function drawDayHud(s, w, h) {
    const plan = (s.day_plan && s.day_plan.ingredients) || {};
    const have = {};
    (s.hold || []).forEach((x) => { const k = typeof x === "string" ? x : x.kind; have[k] = (have[k] || 0) + 1; });
    const phase = { gather: "Lặn & Hái", quan: "Mở Quán", shop: "Sạp nâng cấp" }[s.phase] || s.phase;
    // Góc TRÁI DƯỚI: góc phải trên là chỗ index.html xếp cảnh báo (y >= 36) và dòng âm thanh / phụ đề / tương phản.
    // Gather: trên hàng ô giỏ (h-40 .. h-15). Quán: dưới phòng, bên trái dòng phím tắt canh phải ở h-14.
    const label = "NGÀY " + (s.day || "?") + (s.days_total ? "/" + s.days_total : "") + " · " + phase;
    const lw = measure(label, 16, true) + 26;
    const gather = s.phase === "gather";
    const by = gather ? h - 104 : h - 36;
    box(10, by, lw, 28, C.wood1, { px: 2, light: "rgba(255,220,170,.2)" });
    t(label, 23, by + 20, { size: 16, bold: true, color: C.gold, outline: C.ink, outlineW: 3 });
    if (gather) {
      const need = Object.entries(plan).map(([k, n]) => kn(k) + " " + Math.min(have[k] || 0, n) + "/" + n);
      t("Cần lấy: " + need.join(" · "), 12, h - 56, { size: 15, color: C.light, outline: "rgba(0,0,0,.6)", outlineW: 3 });
    }
  }
  // Chế độ tương phản cao của index.html (biến toàn cục `HC`, phím H): áp cùng bộ lọc cho các màn của day.js
  function highContrast() { try { return typeof HC !== "undefined" && !!HC; } catch (e) { return false; } }

  function frame(now) {
    requestAnimationFrame(frame);
    const s = S();
    if (!s || !s.day_mode) return;
    track(s);
    const w = innerWidth, h = innerHeight;
    g.imageSmoothingEnabled = false;
    g.filter = highContrast() ? "contrast(1.35) saturate(1.25)" : "none";   // khớp index.html
    try {
      if (s.finished && s.reason === "days_complete") { drawSummary(s, w, h, now); return; }
      if (s.phase === "shop") drawShop(s, w, h, now); else buttons.length = 0;
      if (s.phase !== "shop") drawDayHud(s, w, h);
      drawBanner(w, h);
      drawToast(w);
      if (s.state === "paused") drawPaused(w, h);
    } finally {
      g.filter = "none";
    }
  }
  requestAnimationFrame(frame);

  // ---------- phím + chuột (chỉ khi mode day) ----------
  addEventListener("keydown", (e) => {
    if (!isDay() || e.repeat) return;
    const k = e.key.toLowerCase();
    const s = S();
    if (k === "p" || k === "escape") { tap("pause"); e.preventDefault(); return; }
    if (banner && k !== "r") banner = null;            // nhấn phím để tắt màn giới thiệu sớm
    if (s && s.phase === "shop") {
      if (k === "1") buy("oxygen");
      else if (k === "2") buy("hp");
      else if (k === "enter") tap("shop_done");
    }
  });
  cv.addEventListener("click", (e) => {
    if (!isDay()) return;
    const r = cv.getBoundingClientRect(), px = e.clientX - r.left, py = e.clientY - r.top;
    const b = buttons.find((b) => px >= b.x && px <= b.x + b.w && py >= b.y && py <= b.y + b.h);
    if (b) b.act();
  });
})();
