"use strict";
/* Lọc sự kiện MỚI từ snap.events (máy chủ gửi 40 sự kiện gần nhất). fx và màn hình dùng chung danh sách này. */
(function (CN) {
  let seen = new Set(), primed = false, lastTick = -1;
  CN.events = {
    fresh: [],
    restarted: false,
    ingest(snap) {
      const t = snap.tick || 0;
      this.restarted = t < lastTick;
      if (this.restarted) seen = new Set();
      lastTick = t;
      // Lần nạp đầu khi mở trang giữa lượt: chỉ ghi nhận, không phát lại sự kiện cũ (mock thì phát để xem thử).
      const fire = primed || !!CN.state.mock;
      primed = true;
      const out = [];
      for (const e of snap.events || []) {
        const key = e.tick + "|" + e.phase + "|" + e.name + "|" + JSON.stringify(e.data);
        if (seen.has(key)) continue;
        seen.add(key);
        if (fire) out.push(e);
      }
      if (seen.size > 400) seen = new Set([...seen].slice(-200));
      this.fresh = out;
      return out;
    },
  };
})(window.CN);
