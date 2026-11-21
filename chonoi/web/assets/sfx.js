"use strict";
/*
 * SFX tự tạo bằng Web Audio (không dùng file âm thanh ngoài => không vướng bản quyền, ghi ở CREDITS.md).
 * Chỉ chạy ở client; headless không đọc nên không ảnh hưởng tick, sự kiện, tiền, uy tín, snapshot.
 *
 *   SFX.handle(name, data) -> phát âm (nếu bật) và trả CHỮ PHỤ ĐỀ (hoặc null nếu sự kiện không có âm).
 *   Phụ đề luôn trả về dù đã tắt tiếng (Ticket-04 "Phụ đề SFX": thử với âm thanh tắt).
 *   SFX.unlock() gọi trong cú bấm phím đầu tiên (trình duyệt chỉ cho phát âm sau thao tác của người dùng).
 */
const SFX = (() => {
  let ac = null, master = null, muted = false;

  function unlock() {
    if (ac) { if (ac.state === "suspended") ac.resume(); return; }
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return;
    ac = new Ctx();
    master = ac.createGain();
    master.gain.value = 0.35;
    master.connect(ac.destination);
  }

  // Một nốt: tần số trượt f0 -> f1, bao biên giảm dần.
  function tone(f0, f1, dur, type, vol, delay) {
    if (!ac || muted) return;
    const t = ac.currentTime + (delay || 0);
    const o = ac.createOscillator(), g = ac.createGain();
    o.type = type || "sine";
    o.frequency.setValueAtTime(f0, t);
    if (f1 && f1 !== f0) o.frequency.exponentialRampToValueAtTime(Math.max(1, f1), t + dur);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(vol || 0.3, t + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(master);
    o.start(t); o.stop(t + dur + 0.02);
  }

  // Tiếng ồn lọc: nước, xèo xèo, va chạm.
  function noise(dur, vol, f0, f1, delay, q) {
    if (!ac || muted) return;
    const t = ac.currentTime + (delay || 0);
    const n = Math.floor(ac.sampleRate * dur), buf = ac.createBuffer(1, n, ac.sampleRate), d = buf.getChannelData(0);
    for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1;  // chỉ ở client, không dính RNG của sim
    const src = ac.createBufferSource(); src.buffer = buf;
    const f = ac.createBiquadFilter(); f.type = "bandpass"; f.Q.value = q || 1;
    f.frequency.setValueAtTime(f0, t);
    if (f1) f.frequency.exponentialRampToValueAtTime(Math.max(20, f1), t + dur);
    const g = ac.createGain();
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    src.connect(f); f.connect(g); g.connect(master);
    src.start(t);
  }

  const notes = (list, type, dur, vol, gap) => list.forEach((f, i) => tone(f, f, dur, type, vol, i * gap));

  // sự kiện -> { caption, play }. Tên khớp PRD-0 mục E, Ticket-02/03.
  const MAP = {
    dive:             { c: "[Tõm] Út Sen lặn xuống", p: () => noise(0.35, 0.5, 1400, 300) },
    surface:          { c: "[Ào] Út Sen nổi lên", p: () => noise(0.3, 0.45, 400, 1800) },
    gather:           { c: "[Cạch] hái được rau", p: () => notes([660, 880], "triangle", 0.09, 0.3, 0.07) },
    fish_caught:      { c: "[Bõm!] bắt được cá", p: () => { noise(0.2, 0.4, 900, 400); notes([523, 659, 784], "triangle", 0.12, 0.3, 0.08); } },
    hold_full:        { c: "[Bụp] giỏ đầy rồi", p: () => tone(150, 110, 0.22, "square", 0.25) },
    oxygen_empty:     { c: "[Píp píp] hết hơi!", p: () => { notes([880, 660, 880, 660], "square", 0.1, 0.22, 0.13); } },
    choke:            { c: "[Khụ] ngạt nước", p: () => { noise(0.25, 0.5, 600, 200); tone(180, 90, 0.3, "sawtooth", 0.25); } },
    faint:            { c: "[Hự…] Út Sen ngất", p: () => tone(440, 70, 0.9, "sine", 0.35) },
    monster_hit:      { c: "[Rầm] thủy quái cắn!", p: () => { noise(0.3, 0.7, 300, 80); tone(110, 50, 0.35, "sawtooth", 0.35); } },
    gather_end:       { c: "[Ting] cập bến", p: () => notes([523, 659, 784, 1047], "triangle", 0.14, 0.3, 0.09) },
    node_regrown:     { c: "[Tách] rau mọc lại", p: () => tone(1000, 1300, 0.06, "sine", 0.12) },
    spoiled:          { c: "[Ùng ục] hàng bị ươn", p: () => tone(260, 90, 0.35, "sine", 0.3) },
    customer_arrived: { c: "[Keng] khách đến", p: () => { tone(1318, 1318, 0.5, "sine", 0.3); tone(1760, 1760, 0.4, "sine", 0.15, 0.08); } },
    no_dish:          { c: "[Ơ…] không có món nấu", p: () => notes([392, 330], "sine", 0.18, 0.25, 0.16) },
    cook_started:     { c: "[Xèo xèo] bắt đầu nấu", p: () => noise(0.55, 0.45, 5000, 2500, 0, 0.8) },
    dish_ready:       { c: "[Ting!] món chín", p: () => { tone(1760, 1760, 0.45, "sine", 0.3); tone(2093, 2093, 0.4, "sine", 0.18, 0.1); } },
    dish_picked:      { c: "[Tách] nhấc món", p: () => tone(500, 800, 0.08, "triangle", 0.25) },
    served:           { c: "[Ting ting] phục vụ", p: () => notes([784, 988], "triangle", 0.15, 0.3, 0.1) },
    paid:             { c: "[Cạch cạch] thu tiền", p: () => { tone(1568, 1568, 0.07, "square", 0.18); tone(2093, 2093, 0.25, "square", 0.18, 0.08); } },
    customer_left:    { c: "[Hừ] khách bỏ đi", p: () => notes([392, 294], "sawtooth", 0.2, 0.18, 0.18) },
    quan_end:         { c: "[Tùng] đóng quán", p: () => tone(220, 220, 0.7, "sine", 0.35) },
    bought:           { c: "[Keng] mua nâng cấp", p: () => notes([784, 1047, 1319], "triangle", 0.12, 0.3, 0.08) },
    buy_failed:       { c: "[Bụp] không mua được", p: () => tone(160, 120, 0.2, "square", 0.25) },
    day_start:        { c: "[Tà tà] Ngày mới", p: () => notes([392, 523, 659, 784], "triangle", 0.18, 0.28, 0.14) },
  };

  function handle(name, data) {
    const m = MAP[name];
    if (!m) return null;
    // faint do ngạt hay do thủy quái: hai sự kiện, mỗi cái một âm; gather_end chỉ kêu khi cập bến
    if (name === "gather_end" && data && data.reason !== "docked") return null;
    m.p();
    return m.c;
  }

  return {
    handle, unlock,
    names: Object.keys(MAP),
    toggleMute() { muted = !muted; return muted; },
    isMuted: () => muted,
  };
})();
