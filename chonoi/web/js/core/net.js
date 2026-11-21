"use strict";
/*
 * Mạng: gửi trạng thái phím / nút một lần (POST /input), lấy snapshot (GET /state) liên tục.
 * Chế độ mock: /?mock=<tên> đọc mock/<tên>.json, KHÔNG gửi gì lên máy chủ (pause bật/tắt tại chỗ để thử màn hình).
 */
(function (CN) {
  const st = (CN.state = { snap: null, offline: false, mock: null });
  const param = new URLSearchParams(location.search).get("mock");
  if (param && /^[a-z0-9_-]+$/.test(param)) st.mock = param;

  let queue = [], inflight = false, lastSent = "";
  function enqueue(body) { queue.push(body); flush(); }
  async function flush() {
    if (inflight) return;
    inflight = true;
    while (queue.length) {
      const body = queue.shift();
      try { await fetch("/input", { method: "POST", body, headers: { "Content-Type": "application/json" } }); }
      catch (e) { /* mất kết nối: poll sẽ báo */ }
    }
    inflight = false;
  }

  async function loadMock() {
    try {
      const r = await fetch("mock/" + st.mock + ".json", { cache: "no-store" });
      if (!r.ok) throw new Error("HTTP " + r.status);
      st.snap = await r.json();
      st.offline = false;
    } catch (e) {
      st.offline = true;
      console.error("Không đọc được mock/" + st.mock + ".json:", e);
    }
  }
  async function poll() {
    try {
      const r = await fetch("/state", { cache: "no-store" });
      st.snap = await r.json();
      st.offline = false;
    } catch (e) { st.offline = true; }
    setTimeout(poll, 16);
  }

  CN.net = {
    // trạng thái phím đang giữ: {move, interact, catch, attack, photo}
    sendState(inp) {
      if (st.mock) return;
      const s = JSON.stringify(inp);
      if (s === lastSent) return;
      lastSent = s;
      enqueue(s);
    },
    // một cú bấm (cạnh lên) cho nút boolean: pause, shop_done
    tap(button) {
      if (st.mock) {
        if (button === "pause" && st.snap) st.snap.state = st.snap.state === "paused" ? "running" : "paused";
        return;
      }
      enqueue(JSON.stringify({ [button]: true }));
      enqueue(JSON.stringify({ [button]: false }));
    },
    // lệnh mua trong Shop (chuỗi, chỉ có tác dụng ở một tick)
    buy(id) { if (!st.mock) enqueue(JSON.stringify({ buy: id })); },
    customerChoice(customerId, dishId) {
      if (!st.mock) enqueue(JSON.stringify({
        customer_choice: { customer_id: customerId, dish_id: dishId },
      }));
    },
    restart() {
      lastSent = "";
      if (st.mock) loadMock(); else fetch("/restart", { method: "POST" }).catch(() => {});
    },
  };

  if (st.mock) loadMock(); else poll();
})(window.CN);
